import os
import json
import redis
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Qdrant
from langchain_core.prompts import PromptTemplate
from qdrant_client import QdrantClient

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

# 1. Redis 및 Qdrant 클라이언트 초기화
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
qdrant_client_obj = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# 2. Gemini 임베딩 및 LLM 초기화
embeddings = GoogleGenerativeAIEmbeddings(
    model="text-embedding-004",
    google_api_key=GEMINI_API_KEY
)

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.2
)

# Qdrant Vector Store 연결
vector_store = Qdrant(
    client=qdrant_client_obj,
    collection_name="my_test_service_codebase",
    embeddings=embeddings
)

# 3. RAG 분석 프롬프트 정의
analysis_prompt = PromptTemplate.from_template("""
너는 서버 장애 원인을 분석하는 전문 SRE/DevOps AI 에이전트야.
전달받은 [에러 로그]와 Vector DB에서 검색한 [관련 소스 코드]를 바탕으로 장애 원인을 분석해줘.

[에러 로그]
- 서비스명: {service_name}
- 에러 유형: {exception_type}
- 에러 메시지: {message}
- 스택 트레이스:
{stack_trace}

[관련 소스 코드]
{retrieved_code}

---
다음 형식에 맞춰 한국어로 명확하게 답변해줘:
1. 🚨 **장애 요약**: 무슨 에러가 왜 발생했는지 한 줄 요약
2. 🔍 **원인 코드 위치**: 파일명 및 문제 코드 조각 지정
3. 🛠️ **수정 가이드**: 코드 수정 제안 또는 예시 코드
""")

def process_log(log_data: dict):
    print(f"\n📩 [Worker] 에러 로그 수신 완료: {log_data.get('exception_type')}")
    
    # 1. 스택 트레이스 및 메시지를 검색 쿼리로 활용하여 연관 코드 검색
    query = f"{log_data.get('exception_type')} {log_data.get('message')} {log_data.get('stack_trace', '')}"
    docs = vector_store.similarity_search(query, k=2)
    
    retrieved_code = "\n\n".join([f"--- Code Chunk ---\n{doc.page_content}" for doc in docs]) if docs else "관련 코드를 찾을 수 없습니다."
    
    # 2. 프롬프트 구성 및 Gemini LLM 분석 요청
    prompt_value = analysis_prompt.format(
        service_name=log_data.get("service_name"),
        exception_type=log_data.get("exception_type"),
        message=log_data.get("message"),
        stack_trace=log_data.get("stack_trace"),
        retrieved_code=retrieved_code
    )
    
    print("🤖 [Gemini AI] 장애 분석 진행 중...")
    response = llm.invoke(prompt_value)
    
    print("\n================ [ AI 장애 분석 결과 ] ================")
    print(response.content)
    print("=======================================================\n")

def start_worker():
    print("🚀 Troubleshooter AI Worker 시작됨. (Redis 큐 감지 중...)")
    while True:
        try:
            # Redis 'error_logs' 큐에서 데이터 대기 (Blocking Pop)
            _, raw_data = redis_client.blpop("error_logs")
            log_data = json.loads(raw_data.decode("utf-8"))
            process_log(log_data)
        except Exception as e:
            print(f"❌ Worker 처리 중 오류 발생: {e}")

if __name__ == "__main__":
    start_worker()