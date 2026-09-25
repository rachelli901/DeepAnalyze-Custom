import ast
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence, Union

import requests

logger = logging.getLogger(__name__)

DEFAULT_MOCK_RESPONSES = (
    """<Analyze>
Mock mode is enabled; the vLLM API request is skipped.
</Analyze>
<Code>
```python
from pathlib import Path

print("DeepAnalyze mock request completed.")
print(f"Workspace: {Path.cwd()}")
print(f"Workspace entries: {len(list(Path.cwd().iterdir()))}")
```
</Code>""",
    "<Answer>Mock generation completed successfully.</Answer>",
)


BLOCKED_MODULES = frozenset({"ctypes", "multiprocessing", "subprocess"})
BLOCKED_CALLS = frozenset({
    "__import__",
    "builtins.__import__",
    "builtins.compile",
    "builtins.eval",
    "builtins.exec",
    "compile",
    "eval",
    "exec",
    "os._exit",
    "os.fork",
    "os.popen",
    "os.remove",
    "os.removedirs",
    "os.rename",
    "os.replace",
    "os.rmdir",
    "os.system",
    "os.unlink",
    "shutil.move",
    "shutil.rmtree",
})
BLOCKED_CALL_PREFIXES = ("os.exec", "os.spawn")


class UnsafeCodeError(RuntimeError):
    """Raised when generated code contains a blocked operation."""


def _get_qualified_name(node: ast.AST) -> Optional[str]:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return ".".join(reversed(parts))


def _resolve_imported_name(name: str, aliases: dict) -> str:
    root, separator, remainder = name.partition(".")
    resolved_root = aliases.get(root, root)
    if separator:
        return f"{resolved_root}.{remainder}"
    return resolved_root


def _validate_code_safety(code_str: str) -> None:
    """Block a small set of obvious process and destructive operations."""
    try:
        tree = ast.parse(code_str)
    except SyntaxError:
        # The child interpreter will report syntax errors consistently.
        return

    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_root = alias.name.split(".", 1)[0]
                if module_root in BLOCKED_MODULES:
                    raise UnsafeCodeError(
                        f"Blocked dangerous module import: {alias.name}"
                    )
                local_name = alias.asname or module_root
                aliases[local_name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            module_root = module_name.split(".", 1)[0]
            if module_root in BLOCKED_MODULES:
                raise UnsafeCodeError(
                    f"Blocked dangerous module import: {module_name}"
                )
            for alias in node.names:
                if alias.name == "*":
                    if module_root in {"os", "shutil"}:
                        raise UnsafeCodeError(
                            f"Blocked wildcard import from: {module_name}"
                        )
                    continue
                local_name = alias.asname or alias.name
                aliases[local_name] = (
                    f"{module_name}.{alias.name}" if module_name else alias.name
                )

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        qualified_name = _get_qualified_name(node.func)
        if qualified_name is None:
            continue
        resolved_name = _resolve_imported_name(qualified_name, aliases)
        if resolved_name in BLOCKED_CALLS or any(
            resolved_name.startswith(prefix)
            for prefix in BLOCKED_CALL_PREFIXES
        ):
            raise UnsafeCodeError(
                f"Blocked dangerous operation: {resolved_name}"
            )


class DeepAnalyzeVLLM:
    """
    DeepAnalyzeVLLM provides functionality to generate and execute code
    using a vLLM API with multi-round reasoning.

    Set ``mock=True`` to exercise the generation and code-execution flow
    without contacting a vLLM service.
    """

    def __init__(
        self,
        model_name: str,
        api_url: str = "http://localhost:8000/v1/chat/completions",
        max_rounds: int = 30,
        request_timeout: Optional[float] = 300.0,
        code_timeout: float = 60.0,
        mock: bool = False,
        mock_responses: Optional[Sequence[str]] = None,
    ):
        if max_rounds <= 0:
            raise ValueError("max_rounds must be greater than zero")
        if request_timeout is not None and request_timeout <= 0:
            raise ValueError("request_timeout must be greater than zero")
        if code_timeout <= 0:
            raise ValueError("code_timeout must be greater than zero")

        responses = (
            DEFAULT_MOCK_RESPONSES
            if mock_responses is None
            else tuple(mock_responses)
        )
        if mock and not responses:
            raise ValueError("mock_responses cannot be empty in mock mode")

        self.model_name = model_name
        self.api_url = api_url
        self.max_rounds = max_rounds
        self.request_timeout = request_timeout
        self.code_timeout = code_timeout
        self.mock = mock
        self.mock_responses = responses

    def _get_mock_response(self, round_idx: int) -> str:
        try:
            return self.mock_responses[round_idx]
        except IndexError as exc:
            raise RuntimeError(
                "Mock response sequence exhausted at round "
                f"{round_idx + 1}; provide a final <Answer> response"
            ) from exc

    def execute_code(self, code_str: str) -> str:
        """
        Executes Python code in a fresh subprocess and captures stdout/stderr.
        Returns the output or a formatted error message.
        """
        try:
            _validate_code_safety(code_str)
        except UnsafeCodeError as exc:
            logger.error("Generated code blocked: %s", exc)
            return f"[Error]:\nSecurityError: {exc}"

        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-"],
                input=code_str,
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                errors="replace",
                timeout=self.code_timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            timeout_message = (
                f"代码执行超时：超过 {self.code_timeout:g} 秒，子进程已被终止。"
            )
            logger.error("%s", timeout_message)
            output_parts = []
            for stream in (exc.stdout, exc.stderr):
                if stream is None:
                    continue
                if isinstance(stream, bytes):
                    stream = stream.decode(errors="replace")
                output_parts.append(stream.rstrip())
            if output_parts:
                return f"[Error]:\n{timeout_message}\n" + "\n".join(output_parts)
            return f"[Error]:\n{timeout_message}"
        except Exception as exc:
            logger.exception("Failed to start generated-code subprocess")
            return f"[Error]:\nCode execution subprocess failed: {exc}"

        output_parts = []
        if completed.stdout:
            output_parts.append(completed.stdout.rstrip())
        if completed.stderr:
            output_parts.append(completed.stderr.rstrip())
        if completed.returncode != 0:
            output_parts.append(
                f"Process exited with code {completed.returncode}"
            )
            logger.debug(
                "Generated code subprocess exited with code %s",
                completed.returncode,
            )
        return "\n".join(part for part in output_parts if part)


    def generate(
        self,
        prompt: str,
        workspace: Union[str, os.PathLike],
        temperature: float = 0.5,
        max_tokens: int = 32768,
        top_p: float = None,
        top_k: int = None,
    ) -> dict:
        """
        Generates content using vLLM API and executes any <Code> blocks found.
        Returns a dictionary containing the full reasoning process and an
        ``error`` field when generation fails.
        """
        workspace_path = Path(workspace).expanduser().resolve()
        if not workspace_path.is_dir():
            raise FileNotFoundError(
                f"Workspace does not exist or is not a directory: {workspace_path}"
            )

        original_cwd = Path.cwd()
        os.chdir(workspace_path)
        reasoning = ""
        error_message = None
        current_round = None
        messages = [{"role": "user", "content": prompt}]
        response_message = []

        try:
            for round_idx in range(self.max_rounds):
                current_round = round_idx + 1
                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "add_generation_prompt": False,
                    "stop": ["</Code>"],
                }
                if top_p is not None:
                    payload["top_p"] = top_p
                if top_k is not None:
                    payload["top_k"] = top_k

                if self.mock:
                    logger.info(
                        "Mock mode enabled; skipping vLLM request for round %d",
                        current_round,
                    )
                    ans = self._get_mock_response(round_idx)
                else:
                    logger.debug(
                        "Sending vLLM request to %s for round %d",
                        self.api_url,
                        current_round,
                    )
                    response = requests.post(
                        self.api_url,
                        headers={"Content-Type": "application/json"},
                        json=payload,
                        timeout=self.request_timeout,
                    )
                    response.raise_for_status()
                    response_data = response.json()

                    choices = response_data["choices"]
                    choice = choices[0]
                    ans = choice["message"]["content"]
                    if choice.get("stop_reason") == "</Code>":
                        ans += "</Code>"

                response_message.append(ans)

                # Check for termination: only stop when <Answer> is present
                if "<Answer>" in ans:
                    break

                # Check for <Code> block to execute
                code_match = re.search(r"<Code>(.*?)</Code>", ans, re.DOTALL)
                if not code_match:
                    # No <Code> and no <Answer>: intermediate step (e.g. <Analyze>).
                    # Append and continue so the model can produce <Code> next.
                    messages.append({"role": "assistant", "content": ans})
                    continue

                code_content = code_match.group(1).strip()
                md_match = re.search(r"```(?:python)?(.*?)```", code_content, re.DOTALL)
                code_str = md_match.group(1).strip() if md_match else code_content

                # Execute code and append output
                exe_output = self.execute_code(code_str)
                response_message.append(f"<Execute>\n{exe_output}\n</Execute>")

                # Append messages for next round
                messages.append({"role": "assistant", "content": ans})
                messages.append({"role": "execute", "content": exe_output})
            else:
                error_message = (
                    f"Generation stopped after {self.max_rounds} rounds "
                    "without an <Answer>"
                )
                logger.warning(error_message)

        except requests.RequestException as exc:
            error_message = (
                f"vLLM API request failed at round {current_round}: {exc}"
            )
            logger.exception(error_message)
        except (KeyError, IndexError, TypeError) as exc:
            error_message = (
                f"Unexpected vLLM response at round {current_round}: {exc}"
            )
            logger.exception(error_message)
        except Exception as exc:
            error_message = (
                f"DeepAnalyze generation failed at round {current_round}: {exc}"
            )
            logger.exception(error_message)
        finally:
            os.chdir(original_cwd)

        reasoning = "\n".join(response_message)
        return {"reasoning": reasoning, "error": error_message}
