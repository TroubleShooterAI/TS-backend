import logging
import json
import redis

class TroubleShooterHandler(logging.Handler):
    def __init__(self, service_name: str, redis_host: str = "localhost", redis_port: int = 6379):
        super().__init__()
        self.service_name = service_name
        # HTTP 대신 Redis 클라이언트 직접 연결
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)

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
                # worker.py가 감지 중인 'log_queue'에 직접 Push
                self.redis_client.rpush("log_queue", json.dumps(payload))
                print("⚡ [Logger] Redis log_queue로 에러 로그 전송 완료!")
            except Exception as e:
                print(f"❌ [Logger] Redis 전송 실패: {e}")