from fastapi import FastAPI, status
import redis
import json
from schemas import LogPayload

app = FastAPI(title="TroubleShooter AI - Log Ingestion")

# Redis 클라이언트 연결 (Docker 또는 로컬 실행)
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

@app.post("/api/v1/logs", status_code=status.HTTP_202_ACCEPTED)
async def ingest_log(payload: LogPayload):
    # LogPayload를 JSON 문자열로 변환하여 Redis 큐에 Push
    log_data = payload.model_dump_json()
    redis_client.rpush("log_queue", log_data)
    
    return {
        "status": "queued",
        "message": "Log received successfully",
        "service": payload.service_name
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}