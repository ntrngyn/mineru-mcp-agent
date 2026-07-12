import os
import time
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore, FastEmbedSparse
from qdrant_client import QdrantClient

# Tự động nạp file .env để lấy GEMINI_API_KEY
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

def run_benchmark():
    print("Khởi tạo mô hình và kết nối Qdrant...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
    client = QdrantClient(path="./data/vector_db")
    
    # Vector Search Only Store
    vectorstore_dense = QdrantVectorStore(
        client=client,
        collection_name="mineru_docs",
        embedding=embeddings,
    )
    
    # Hybrid Search Store
    vectorstore_hybrid = QdrantVectorStore(
        client=client,
        collection_name="mineru_docs",
        embedding=embeddings,
        sparse_embedding=sparse_embeddings,
        retrieval_mode="hybrid"
    )

    queries = [
        "Kiến trúc cốt lõi của hệ thống RAG là gì?",
        "Công thức toán học để tính IDF?",
        "Ưu điểm của Vector Search so với BM25?",
        "Token được tiết kiệm như thế nào ở Deep Reading?"
    ]

    print("\n--- BẢNG 5.1: ĐO LƯỜNG LATENCY (ms) CHO CÁC CÂU HỎI ---")
    total_dense_time = 0
    total_hybrid_time = 0

    for idx, q in enumerate(queries):
        # Đo Dense
        start = time.time()
        vectorstore_dense.similarity_search(q, k=3)
        dense_time = (time.time() - start) * 1000
        total_dense_time += dense_time

        # Đo Hybrid
        start = time.time()
        vectorstore_hybrid.similarity_search(q, k=3)
        hybrid_time = (time.time() - start) * 1000
        total_hybrid_time += hybrid_time

        print(f"Q{idx+1}: {q[:40]}... | Vector: {dense_time:.2f} ms | Hybrid: {hybrid_time:.2f} ms")

    avg_dense = total_dense_time / len(queries)
    avg_hybrid = total_hybrid_time / len(queries)
    
    print("\n--- BIỂU ĐỒ 5.1: THỜI GIAN TRUNG BÌNH (Local CPU) ---")
    print(f"Vector Search Average Latency: {avg_dense:.2f} ms")
    print(f"Hybrid Search Average Latency: {avg_hybrid:.2f} ms")

if __name__ == "__main__":
    run_benchmark()
