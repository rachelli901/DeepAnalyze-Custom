import logging
import os
import sys
from pathlib import Path

from deepanalyze import DeepAnalyzeVLLM


logging.basicConfig(
    level=getattr(
        logging,
        os.environ.get("DEEPANALYZE_LOG_LEVEL", "INFO").strip().upper(),
        logging.INFO,
    ),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_WORKSPACE = (
    PROJECT_ROOT / "example" / "analysis_on_student_loan" / "data"
)
DEFAULT_MODEL_NAME = "DeepAnalyze-8B"


def _clean_environment_value(value: str) -> str:
    """Remove surrounding whitespace and one accidental outer quote pair."""
    cleaned = value.strip()
    if (
        len(cleaned) >= 2
        and cleaned[0] == cleaned[-1]
        and cleaned[0] in {'"', "'"}
    ):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def _get_boolean_env(name: str) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return False

    return _clean_environment_value(raw_value).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _get_workspace() -> Path:
    raw_workspace = os.environ.get("DEEPANALYZE_WORKSPACE")

    if raw_workspace is None or not raw_workspace.strip():
        workspace_value = str(DEFAULT_WORKSPACE)
    else:
        workspace_value = _clean_environment_value(raw_workspace)
        if not workspace_value:
            raise ValueError(
                "DEEPANALYZE_WORKSPACE is empty after normalization"
            )

    workspace_path = Path(workspace_value).expanduser()
    if not workspace_path.is_absolute():
        workspace_path = PROJECT_ROOT / workspace_path

    try:
        workspace_path = workspace_path.resolve()
    except (OSError, ValueError) as exc:
        raise ValueError(
            f"Invalid workspace path: {workspace_value!r}"
        ) from exc

    try:
        is_directory = workspace_path.is_dir()
    except OSError as exc:
        raise ValueError(
            f"Invalid workspace path: {workspace_value!r}"
        ) from exc

    if not is_directory:
        raise FileNotFoundError(
            f"Workspace does not exist or is not a directory: {workspace_path}"
        )

    return workspace_path


def _get_model_name() -> str:
    raw_model_name = os.environ.get("DEEPANALYZE_MODEL")
    if raw_model_name is None:
        return DEFAULT_MODEL_NAME

    model_name = _clean_environment_value(raw_model_name)
    if not model_name:
        raise ValueError("DEEPANALYZE_MODEL cannot be empty")

    return model_name


prompt = """# Instruction
Generate a data science report.

# Data
File 1:
{"name": "bool.xlsx", "size": "4.8KB"}
File 2:
{"name": "person.csv", "size": "10.6KB"}
File 3:
{"name": "disabled.xlsx", "size": "5.6KB"}
File 4:
{"name": "enlist.csv", "size": "6.7KB"}
File 5:
{"name": "filed_for_bankrupcy.csv", "size": "1.0KB"}
File 6:
{"name": "longest_absense_from_school.xlsx", "size": "16.0KB"}
File 7:
{"name": "male.xlsx", "size": "8.8KB"}
File 8:
{"name": "no_payment_due.xlsx", "size": "15.6KB"}
File 9:
{"name": "unemployed.xlsx", "size": "5.6KB"}
File 10:
{"name": "enrolled.csv", "size": "20.4KB"}"""

workspace = _get_workspace()
mock_enabled = _get_boolean_env("DEEPANALYZE_MOCK")
model_name = _get_model_name()

deepanalyze = DeepAnalyzeVLLM(model_name, mock=mock_enabled)
answer = deepanalyze.generate(prompt, workspace=workspace)
if answer.get("error"):
    print(f'DeepAnalyze failed: {answer["error"]}', file=sys.stderr)
    raise SystemExit(1)
print(answer["reasoning"])
