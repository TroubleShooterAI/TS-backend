from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LogPayload(BaseModel):
    service_name: str          # 에러 발생 프로젝트/서비스 이름
    environment: str           # dev, prod, local 등
    exception_type: str        # 예: NullPointerException, ZeroDivisionError
    message: str               # 에러 메시지
    stack_trace: str           # StackTrace 전체
    file_path: Optional[str] = None   # 에러 발생 파일 경로
    line_number: Optional[int] = None # 에러 발생 줄 번호
    timestamp: datetime = datetime.now()