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
    def __init__(self, input_value: Any, positive = True):
        self.input_value = input_value 
        self.validated = 0
        self.positive = positive

    def validate(self) -> bool:
        result = True;
        try: 
            v = int(self.input_value)
            if self.positive and v <= 0:
                return False
            self.validated = v 
        except Exception:
            result = False
        return result

    def get(self) -> int:
        return self.validated

class IntListValidator:
    def __init__(self, input_value: str, positive = True):
        self.input_value = input_value 
        self.validated: list[int] = [] 
        self.positive = positive

    def validate(self) -> bool:
        result = True;
        try:
            lst = self.input_value.split(",")
            for el in lst:
                v = int(el)
                if self.positive and v <= 0:
                    return False
                self.validated.append(v)
        except Exception:
            result = False
        return result

    def get(self) -> list[int]:
        return self.validated

class FloatListValidator:
    def __init__(self, input_value: str, positive = True):
        self.input_value = input_value 
        self.validated: list[float] = [] 
        self.positive = positive

    def validate(self) -> bool:
        result = True;
        try:
            lst = self.input_value.split(",")
            for el in lst:
                v = float(el)
                if self.positive and v <= 0:
                    return False
                self.validated.append(v)
        except Exception:
            result = False
        return result

    def get(self) -> list[float]:
        return self.validated
