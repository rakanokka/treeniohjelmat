import logging
from typing import Any

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
