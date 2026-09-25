# DeepAnalyze-Custom

> **Disclaimer & Acknowledgments**
> This repository is a customized and optimized fork of the original [DeepAnalyze](https://github.com/aigc-apps/DeepAnalyze) project. 
> It is maintained independently for extended reliability, cross-platform stability, and local sandbox safety. 
> Special thanks to the original DeepAnalyze authors and open-source contributors for their foundational work.

---

## 🚀 Enhancements & Refactoring in This Custom Version

Compared to the upstream original repository, this fork addresses several critical production pain points, error-handling bugs, and security vulnerabilities:

### 1. Cross-Platform Workspace Fix (`run.py` & `deepanalyze.py`)
- **Resolved `FileNotFoundError`**: Eliminated Linux-hardcoded paths (e.g., `/app/...`).
- **Dynamic Path Resolution**: Refactored directory handling using Python's `pathlib.Path` relative to `__file__`, automatically supporting Windows, macOS, and Linux environments.
- **Environment Sanitization**: Cleaned up workspace string parsing to strip wrapping quotes and trailing whitespaces safely.

### 2. Error Transparency & Zero-GPU Mock Mode (`deepanalyze.py`)
- **Granular Exception Handling**: Replaced broad `except Exception:` blocks with classified exception catching (`requests.RequestException`, `KeyError`, `IndexError`, `TypeError`) and detailed `logger.exception()` stack traces to prevent silent API failures (e.g., 502 Bad Gateway).
- **Offline Mock Mode**: Added `mock=True` / `$env:DEEPANALYZE_MOCK="1"` support. Allows developers to test multi-turn agent interaction pipelines locally without a running vLLM server or local GPU hardware.
- **Request Timeout Control**: Implemented a default 300s timeout for HTTP POST requests to prevent hanging API connections.

### 3. Process Isolation, Hard Timeout & AST Safety Inspection
- **Subprocess Isolation**: Replaced in-process `exec()` code execution with isolated Python worker subprocesses (`subprocess.run([sys.executable, "-I", "-"])`), preventing code execution errors from crashing the main runner.
- **Code Execution Timeout (`code_timeout`)**: Added a default 60-second hard timeout for generated Python code (capturing `subprocess.TimeoutExpired`) to prevent infinite loops (`while True`) from locking up the system.
- **AST Static Safety Filter**: Added AST-based syntax analysis to intercept high-risk system commands and unsafe operations before execution (e.g., `os.system`, `shutil.rmtree`, `subprocess`, `ctypes`, `eval`, `exec`).

---

## 🛠️ Quick Start

### Running in Mock Mode (No GPU Required)

```powershell
# In Windows PowerShell:
$env:DEEPANALYZE_MOCK = "1"
python run.py