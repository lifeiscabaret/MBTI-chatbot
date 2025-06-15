import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader

load_dotenv()

# [1] 주제별 텍스트 파일 로딩
file_paths = [
    "mbti 성격.txt",
    "mbti 궁합.txt",
    "mbti 연애 스타일.txt",
    "mbti 업무 스타일.txt"
]

documents = []
for path in file_paths:
    loader = TextLoader(path, encoding="utf-8")
    docs = loader.load()
    documents.extend(docs)

# [2] 텍스트 분할
recursive_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=200
)
splits = recursive_splitter.split_documents(documents)

# [3] 확인용 출력
print(f"📦 총 분할된 문서 수: {len(splits)}")

# [4] 텍스트 저장 (디버깅용)
with open("split_output.txt", "w", encoding="utf-8") as f:
    for i, doc in enumerate(splits):
        f.write(f"\n\n📜 Split {i}:\n{doc.page_content}\n")

# [5] Pinecone 초기화
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index(
    name="mbti",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)
# [6] 벡터 저장소로 업로드
vectorstore = PineconeVectorStore.from_documents(
    documents=splits,
    embedding=OpenAIEmbeddings(model="text-embedding-3-large"),
    index_name="mbti"
)

print("✅ Pinecone에 업로드 완료!")