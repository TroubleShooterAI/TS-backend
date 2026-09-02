# target_app_logger.py
import logging
import requests

class TroubleShooterHandler(logging.Handler):
    def __init__(self, service_name: str, server_url: str):
        super().__init__()
        self.service_name = service_name
        self.server_url = server_url

    def emit(self, record):
        if record.levelno >= logging.ERROR:
            payload = {
                "service_name": self.service_name,
                "environment": "local",
                "exception_type": record.exc_info[0].__name__ if record.exc_info else "Error",
                "message": record.getMessage(),
                "stack_trace": self.format(record),
                "file_path": record.pathname,
                "line_number": record.lineno
            }
            try:
                requests.post(self.server_url, json=payload, timeout=2)
            except Exception:
                pass # 로깅 전송 실패가 메인 로직에 영향을 주지 않도록 예외 처리