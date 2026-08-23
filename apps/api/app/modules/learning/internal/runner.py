import asyncio
import json
import os
import resource
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Protocol


@dataclass
class RunnerResult:
    status: str  # "passed" | "failed" | "error"
    stdout: str
    stderr: str
    tests_passed: int
    tests_total: int
    duration_ms: int


class CodeRunnerProtocol(Protocol):
    async def run_submission(
        self,
        code: str,
        tests_code: str,
        timeout_seconds: float = 4.0,
    ) -> RunnerResult: ...


# Wrapper script template executed inside the isolated subprocess
_RUNNER_HARNESS_TEMPLATE = """
import io
import json
import os
import socket
import sys
import traceback

# 1. Intercept network access inside the sandboxed environment
_orig_socket = socket.socket

class _BlockedSocket(_orig_socket):
    def __init__(self, *args, **kwargs):
        raise PermissionError("Network access is disabled in the exercise sandbox.")

    def connect(self, *args, **kwargs):
        raise PermissionError("Network access is disabled in the exercise sandbox.")

    def send(self, *args, **kwargs):
        raise PermissionError("Network access is disabled in the exercise sandbox.")

def _blocked_connection(*args, **kwargs):
    raise PermissionError("Network access is disabled in the exercise sandbox.")

socket.socket = _BlockedSocket
socket.create_connection = _blocked_connection
socket.getaddrinfo = _blocked_connection

# 2. Redirect stdout/stderr to capture execution output safely
_user_stdout = io.StringIO()
_user_stderr = io.StringIO()
_orig_stdout = sys.stdout
_orig_stderr = sys.stderr

sys.stdout = _user_stdout
sys.stderr = _user_stderr

_tests_passed = 0
_tests_total = 0
_failure_msg = ""
_status = "passed"

try:
    # 3. Execute student code in isolated namespace
    _namespace = {
        "__name__": "__main__",
        "__builtins__": __builtins__,
    }
    exec(compile(_STUDENT_CODE, "<student_code>", "exec"), _namespace)

    # 4. Execute test code assertions against student namespace
    exec(compile(_TESTS_CODE, "<test_code>", "exec"), _namespace)

    # If test runner functions or assertions were defined and run
    # Count tests if test helper functions were registered, or default 1/1 if assertions passed
    _tests_passed = _namespace.get("__tests_passed", 1)
    _tests_total = _namespace.get("__tests_total", 1)
    _status = "passed"

except AssertionError as e:
    _status = "failed"
    _failure_msg = str(e) or "AssertionError: test case assertion failed."
    _tests_total = _namespace.get("__tests_total", 1)
    _tests_passed = _namespace.get("__tests_passed", 0)

except PermissionError as e:
    _status = "error"
    _failure_msg = f"Security Violation: {e}"
    _tests_total = 1
    _tests_passed = 0

except Exception as e:
    _status = "error"
    _failure_msg = f"{type(e).__name__}: {e}\\n" + traceback.format_exc()
    _tests_total = _namespace.get("__tests_total", 1)
    _tests_passed = _namespace.get("__tests_passed", 0)

finally:
    sys.stdout = _orig_stdout
    sys.stderr = _orig_stderr

_captured_stdout = _user_stdout.getvalue()
_captured_stderr = _user_stderr.getvalue()

if _failure_msg:
    if _captured_stderr:
        _captured_stderr = _captured_stderr + "\\n" + _failure_msg
    else:
        _captured_stderr = _failure_msg

_result_payload = {
    "status": _status,
    "stdout": _captured_stdout,
    "stderr": _captured_stderr,
    "tests_passed": _tests_passed,
    "tests_total": _tests_total,
}

print("__LEARNLOOP_RUNNER_RESULT_START__")
print(json.dumps(_result_payload))
print("__LEARNLOOP_RUNNER_RESULT_END__")
"""


def _set_process_limits(timeout_seconds: int = 5, memory_mb: int = 128) -> None:
    """Set CPU and memory resource limits in subprocess preexec."""
    try:
        # Limit CPU time (soft and hard limits in seconds)
        resource.setrlimit(resource.RLIMIT_CPU, (timeout_seconds, timeout_seconds + 1))
        # Limit virtual memory address space (in bytes)
        mem_bytes = memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    except Exception:
        pass


class SubprocessPythonRunner:
    def __init__(self, python_executable: str | None = None) -> None:
        self.python_executable = python_executable or sys.executable

    async def run_submission(
        self,
        code: str,
        tests_code: str,
        timeout_seconds: float = 4.0,
    ) -> RunnerResult:
        start_time = time.perf_counter()

        with tempfile.TemporaryDirectory(prefix="learnloop_run_") as temp_dir:
            harness_path = os.path.join(temp_dir, "harness.py")
            payload_content = (
                f"_STUDENT_CODE = {repr(code)}\n"
                f"_TESTS_CODE = {repr(tests_code)}\n" + _RUNNER_HARNESS_TEMPLATE
            )

            with open(harness_path, "w", encoding="utf-8") as f:
                f.write(payload_content)

            try:
                proc = await asyncio.create_subprocess_exec(
                    self.python_executable,
                    harness_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=temp_dir,
                    preexec_fn=lambda: _set_process_limits(int(timeout_seconds) + 1, 128),
                )

                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        proc.communicate(),
                        timeout=timeout_seconds,
                    )
                except TimeoutError:
                    try:
                        proc.kill()
                        await proc.wait()
                    except Exception:
                        pass

                    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                    return RunnerResult(
                        status="error",
                        stdout="",
                        stderr=f"Execution timed out (exceeded {timeout_seconds}s limit).",
                        tests_passed=0,
                        tests_total=1,
                        duration_ms=elapsed_ms,
                    )

                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                raw_stdout = stdout_bytes.decode("utf-8", errors="replace")
                raw_stderr = stderr_bytes.decode("utf-8", errors="replace")

                # Parse delimiter-wrapped JSON payload
                if "__LEARNLOOP_RUNNER_RESULT_START__" in raw_stdout:
                    parts = raw_stdout.split("__LEARNLOOP_RUNNER_RESULT_START__")[1]
                    json_str = parts.split("__LEARNLOOP_RUNNER_RESULT_END__")[0].strip()
                    try:
                        data = json.loads(json_str)
                        return RunnerResult(
                            status=data.get("status", "error"),
                            stdout=data.get("stdout", ""),
                            stderr=data.get("stderr", "") or raw_stderr,
                            tests_passed=data.get("tests_passed", 0),
                            tests_total=data.get("tests_total", 1),
                            duration_ms=elapsed_ms,
                        )
                    except Exception as parse_err:
                        return RunnerResult(
                            status="error",
                            stdout=raw_stdout,
                            stderr=f"Runner payload parse failure: {parse_err}\n{raw_stderr}",
                            tests_passed=0,
                            tests_total=1,
                            duration_ms=elapsed_ms,
                        )

                # Process crashed or exited abnormally
                return RunnerResult(
                    status="error",
                    stdout=raw_stdout,
                    stderr=raw_stderr or "Execution failed with unexpected exit code.",
                    tests_passed=0,
                    tests_total=1,
                    duration_ms=elapsed_ms,
                )

            except Exception as e:
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                return RunnerResult(
                    status="error",
                    stdout="",
                    stderr=f"Subprocess error: {e}",
                    tests_passed=0,
                    tests_total=1,
                    duration_ms=elapsed_ms,
                )
