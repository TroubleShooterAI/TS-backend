import os
from dotenv import load_dotenv
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# .env 파일 로드
load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

class CodeIndexer:
    def __init__(self, collection_name: str = "troubleshooter_codebase"):
        self.collection_name = collection_name

        # FastEmbed 로컬 임베딩 모델 (384 차원)
        self.embeddings = FastEmbedEmbeddings(
            model_name="BAAI/bge-small-en-v1.5"
        )

        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, check_compatibility=False)

    def index_directory(self, repo_path: str, file_extension: str = ".py", language_type: Language = Language.PYTHON):
        print(f"📂 [{repo_path}] 디렉토리에서 소스 코드를 불러오는 중...")

        documents = []
        ignored_dirs = {'venv', '.venv', '__pycache__', '.git', 'build', 'dist'}

        for root, dirs, files in os.walk(repo_path):
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

        if not documents:
            print("⚠️ 수집된 문서가 없습니다.")
            return

        # 2. 코드 Chunking
        python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=language_type, 
            chunk_size=1000, 
            chunk_overlap=200
        )
        texts = python_splitter.split_documents(documents)
        print(f"🧩 총 {len(texts)}개의 Code Chunk로 분할되었습니다.")

        # 3. 임베딩 벡터 생성
        print("⚡ 벡터 임베딩 생성 중...")
        contents = [doc.page_content for doc in texts]
        vector_list = self.embeddings.embed_documents(contents)

        # 4. Qdrant 컬렉션 재생성 및 데이터 업서트 (네이티브 API)
        vector_size = len(vector_list[0])
        print(f"⚡ Qdrant 컬렉션 [{self.collection_name}] 생성 중 (Vector Dimension: {vector_size})...")

        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

        points = [
            PointStruct(
                id=idx,
                vector=vector_list[idx],
                payload={
                    "page_content": doc.page_content,
                    "metadata": doc.metadata
                }
            )
            for idx, doc in enumerate(texts)
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        print(f"✅ [{self.collection_name}] 컬렉션에 소스코드 인덱싱 완료!")

if __name__ == "__main__":
    indexer = CodeIndexer(collection_name="my_test_service_codebase")
    target_repo_path = "../my-target-service"
    
    indexer.index_directory(
        repo_path=target_repo_path, 
        file_extension=".py", 
        language_type=Language.PYTHON
    )