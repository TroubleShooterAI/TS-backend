# code_indexer.py
import os
from dotenv import load_dotenv
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers.language.language_parser import LanguageParser
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
#from langchain_openai import OpenAIEmbeddings
#from langchain_google_genai import GoogleGenerativeAIEmbeddings
# langchain_google_genai 대신 FastEmbed 임포트
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

# .env 파일 로드
load_dotenv()

#OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

class CodeIndexer:
    def __init__(self, collection_name: str = "troubleshooter_codebase"):
        self.collection_name = collection_name

        # GEMINI 키 검증
        if not GEMINI_API_KEY:
            raise ValueError(".env에서 GENINI KEY를 못 찾았습니다.")
        #self.embeddings = OpenAIEmbeddings(
        #    model="text-embedding-3-small", 
        #    openai_api_key=OPENAI_API_KEY
        #)
        # Google API 대신 로컬 경량 모델 사용 (속도 우수, 100% 무료/안정적)
        self.embeddings = FastEmbedEmbeddings(
            model_name="BAAI/bge-small-en-v1.5"
        )

        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    def index_directory(self, repo_path: str, file_extension: str = ".py", language_type: Language = Language.PYTHON):
        """
        지정한 소스코드 디렉토리를 분할/임베딩하여 Qdrant에 저장합니다.
        """
        print(f"📂 [{repo_path}] 디렉토리에서 소스 코드를 불러오는 중...")

        # venv, __pycache__, .git 폴더를 확실하게 걸러내는 파일 수집 로직
        documents = []
        ignored_dirs = {'venv', '.venv', '__pycache__', '.git', 'build', 'dist'}

        for root, dirs, files in os.walk(repo_path):
            # 무시할 디렉토리는 탐색 목록에서 즉시 제외
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            
            for file in files:
                if file.endswith(file_extension):
                    file_path = os.path.join(root, file)
                    try:
                        loader = TextLoader(file_path, encoding='utf-8')
                        documents.extend(loader.load())
                    except Exception as e:
                        print(f"⚠️ 파일 로드 실패 ({file_path}): {e}")

        print(f"📄 총 {len(documents)}개의 소스코드 파일 수집 완료.")

        # 2. 코드 구조에 맞게 Chunking (문맥 보존)
        python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=language_type, 
            chunk_size=1000, 
            chunk_overlap=200
        )
        texts = python_splitter.split_documents(documents)
        print(f"🧩 총 {len(texts)}개의 Code Chunk로 분할되었습니다.")

        # 3. Vector DB 저장 (Qdrant)
        print("⚡ Qdrant Vector DB에 임베딩 저장 중...")
        vector_store = Qdrant.from_documents(
            documents=texts,
            embedding=self.embeddings,
            url=f"http://{QDRANT_HOST}:{QDRANT_PORT}",
            collection_name=self.collection_name,
            force_recreate=True  # 재인덱싱 시 기존 콜렉션 초기화
        )
        print(f"✅ [{self.collection_name}] 컬렉션에 소스코드 인덱싱 완료!")

# if __name__ == "__main__":
    # 테스트용: 현재 백엔드 폴더(또는 타겟 앱 폴더)를 인덱싱
#    indexer = CodeIndexer(collection_name="techstack_navigator_codebase")
    
    # 예시: 인덱싱할 프로젝트 소스코드 폴더 경로 지정
#    target_repo_path = "./"  # 현재 디렉토리 기준
#    indexer.index_directory(repo_path=target_repo_path, file_extension=".py", language_type=Language.PYTHON)

if __name__ == "__main__":
    # 1. 테스트 서비스 전용 컬렉션 이름 지정
    indexer = CodeIndexer(collection_name="my_test_service_codebase")
    
    # 2. 상위 폴더의 my-target-service 경로 지정
    target_repo_path = "../my-target-service"
    
    # 3. 인덱싱 실행
    indexer.index_directory(
        repo_path=target_repo_path, 
        file_extension=".py", 
        language_type=Language.PYTHON
    )