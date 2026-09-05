import os
import json
from dotenv import load_dotenv
import redis
from qdrant_client import QdrantClient
from langchain_community.embeddings import FastEmbedEmbeddings
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# 1. 클라이언트 초기화
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, check_compatibility=False)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

def process_error_log(log_data):
    # 타겟 앱 로그 규격 대응
    error_type = log_data.get('exception_type') or log_data.get('error_type', 'Error')
    error_message = log_data.get('message') or log_data.get('error_message', '')
    stack_trace = log_data.get('stack_trace') or log_data.get('traceback', '')

    print(f"\n📩 [에러 감지] {error_type}: {error_message}")
    
    # 2. Qdrant 소스코드 검색 (최신 query_points API 사용)
    query_text = f"{error_type} {error_message}"
    query_vector = embeddings.embed_query(query_text)
    
    try:
        # 최신 qdrant-client 메서드
        search_results = qdrant_client.query_points(
            collection_name="my_test_service_codebase",
            query=query_vector,
            limit=2
        ).points
    except AttributeError:
        # 구버전 호환용 Fallback
        search_results = qdrant_client.search(
            collection_name="my_test_service_codebase",
            query_vector=query_vector,
            limit=2
        )
    
    context_code = "\n---\n".join([hit.payload.get("page_content", "") for hit in search_results])  
    print("🔍 관련 소스코드 검색 완료!")

    # 3. Gemini 장애 분석
    prompt = f"""
    너는 백엔드 장애 분석 AI 전문가야. 아래 에러 로그와 관련 소스코드를 분석해서 원인과 해결책을 간결하게 제시해줘.

    [에러 로그]
    - Service: {log_data.get('service_name', 'Unknown')}
    - Type: {error_type}
    - Message: {error_message}
    - Traceback: {stack_trace}

    [관련 소스코드]
    {context_code}
    """
    
    print("🤖 Gemini 분석 요청 중...")
    response = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    print("\n================ [ 장애 분석 결과 ] ================")
    print(response.text)
    print("===================================================\n")

if __name__ == "__main__":
    print("🚀 Troubleshooter AI Worker 시작됨. (Redis 큐 감지 중...)")
    
    while True:
        _, data = redis_client.blpop("error_logs")
        if data:
            log_data = json.loads(data.decode('utf-8'))
            process_error_log(log_data)