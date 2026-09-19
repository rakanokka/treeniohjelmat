import logging
from typing import Any, NamedTuple
from pathlib import Path
from .config import DEBUG_MODE

class RemoveStaticLogs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not("GET /static/" in record.getMessage())

class RemoveChromeDevtoolLogs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not("com.chrome.devtools" in record.getMessage())

def set_log_filters(logger_name: str, log_filters: list[logging.Filter]):
    logger = logging.getLogger(logger_name)
    for log_filter in log_filters:
        logger.addFilter(log_filter)

class IntValidator:
    def __init__(self, input_value: Any):
        self.input_value = input_value 
        self.validated = 0

    def validate(self) -> bool:
        result = True;
        try: 
            self.validated = int(self.input_value)
        except Exception:
            result = False
        return result

    def get(self) -> int:
        return self.validated

class GetPathResult(NamedTuple):
    success: bool
    error: str
    path: Path | None

# TODO: Quickly hacked together. Unit test this
def get_path(path_str: str) -> GetPathResult:
    if not path_str:
        return GetPathResult(
                False, 
                "Cannot resolve empty path", 
                None) 
    dir_names = path_str.split("/")
    last = dir_names.pop()
    # current_dir = project_root, __file__ -> src -> xfit
    current_dir = Path(__file__).resolve().parent.parent
    for dir_name in dir_names:
        path = current_dir.joinpath(dir_name)
        if not path.exists():
            return GetPathResult(
                    False, 
                    f"Failed to resolve path to {dir_name} in {path_str}", 
                    None)
        current_dir = path
    target_path = current_dir.joinpath(last)
    if not target_path.exists():
        return GetPathResult(
                False, 
                f"Failed to resolve path to {last} in {path_str}", 
                None)
    return GetPathResult(True, "", target_path)

def debug_output(message: Any):
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

def debug_assert(expected: bool, message = "Invalid assertion"):
    if DEBUG_MODE:
        assert expected, message
