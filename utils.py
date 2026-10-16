import logging

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
