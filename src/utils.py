import sys
import logging
from typing import NamedTuple
from pathlib import Path

class RemoveStaticLogs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not ("GET /static/" in record.getMessage())

def set_log_filters(logger_name: str, log_filters: list[logging.Filter]):
    logger = logging.getLogger(logger_name)
    for log_filter in log_filters:
        logger.addFilter(log_filter)

class GetFilepathResult(NamedTuple):
    valid: bool
    error: str
    path: Path | None

# TODO: Quickly hacked together. Unit test this
def get_filepath(path_str: str) -> GetFilepathResult:
    if not path_str:
        return GetFilepathResult(
                False, 
                "Failed to resolve an empty path", 
                None)
    root_dir = Path(__file__).resolve().parent.parent # ../..
    if root_dir is None:
        return GetFilepathResult(
                False, 
                "Failed to resolve path to project root directory", 
                None)
    current_dir = root_dir
    dir_names = path_str.split("/")
    filename = dir_names.pop()
    for dir_name in dir_names:
        path = current_dir.joinpath(dir_name)
        if path is None:
            return GetFilepathResult(
                    False, 
                    f"Failed to resolve path to {dir_name} directory\n{path_str}", 
                    None)
        current_dir = path
    file_path = current_dir.joinpath(filename)
    if file_path is None:
        return GetFilepathResult(
                False, 
                f"Failed to resolve path to {filename}\n{path_str}", 
                None)
    return GetFilepathResult(True, "", file_path)

def debug_output(message: str):
    print(f"[DEBUG] {message}")

def debug_assert(expect_true: bool, error_message: str):
    # TODO: Maybe use the built in assert?
    if not expect_true:
        sys.exit(error_message)
