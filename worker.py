import redis
import json
import time

# Redis 클라이언트 연결
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def start_worker():
    print("🚀 TroubleShooter AI Worker Started... Waiting for logs.")
    
    while True:
        # blpop: log_queue에 데이터가 들어올 때까지 대기(Blocking)하다가 꺼냄 (Timeout: 0 = 무한대기)
        result = redis_client.blpop("log_queue", timeout=0)
        
        if result:
            queue_name, log_data_str = result
            log_data = json.loads(log_data_str)
            
            print("\n================ [New Error Log Arrived] ================")
            print(f"Service   : {log_data.get('service_name')}")
            print(f"Exception : {log_data.get('exception_type')}")
            print(f"Message   : {log_data.get('message')}")
            print(f"File/Line : {log_data.get('file_path')}:{log_data.get('line_number')}")
            print("---------------- StackTrace ----------------")
            print(log_data.get('stack_trace'))
            print("=========================================================\n")
            
            # TODO (Phase 2): 여기서 Vector DB 검색 및 LLM(RAG) 분석 호출 예정

if __name__ == "__main__":
    start_worker()