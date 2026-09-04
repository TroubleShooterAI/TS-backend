# code_indexer.py
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

# .env 파일 로드
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

class CodeIndexer:
    def __init__(self, collection_name: str = "troubleshooter_codebase"):
        self.collection_name = collection_name
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small", 
            openai_api_key=OPENAI_API_KEY
        )
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    def index_directory(self, repo_path: str, file_extension: str = ".py", language_type: Language = Language.PYTHON):
        """
        지정한 소스코드 디렉토리를 분할/임베딩하여 Qdrant에 저장합니다.
        """
        print(f"📂 [{repo_path}] 디렉토리에서 소스 코드를 불러오는 중...")

        # 1. 소스코드 로딩 및 파싱 (함수/클래스 단위 구조 인식)
        loader = GenericLoader.from_filesystem(
            repo_path,
            glob=f"**/*{file_extension}",
            suffixes=[file_extension],
            parser=LanguageParser(language=language_type, parser_threshold=500)
        )
        documents = loader.load()
        print(f"📄 총 {len(documents)}개의 코드 파일/블록 수집 완료.")

        if not documents:
            print("⚠️ 수집된 문서가 없습니다. 경로 및 확장자를 확인해주세요.")
            return

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