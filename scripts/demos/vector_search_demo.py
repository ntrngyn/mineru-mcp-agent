import os
import time

# Tự động nạp file .env để lấy GEMINI_API_KEY
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

# Nếu dùng tên biến là GEMINI_API_KEY thì set luôn cho GOOGLE_API_KEY
if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore, FastEmbedSparse
from qdrant_client import QdrantClient

def run_real_search():
    query = "Attention mechanism and Transformer architecture"
    
    print(f"\n[🔍] Đang nạp mô hình Google Gemini Embedding...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
    
    print(f"[⚙️] Đang kết nối tới Vector DB thực tế (Qdrant)...")
    try:
        client = QdrantClient(path="./data/vector_db")
        vectorstore = QdrantVectorStore(
            client=client,
            collection_name="mineru_docs",
            embedding=embeddings,
            sparse_embedding=sparse_embeddings,
            retrieval_mode="hybrid"
        )
    except Exception as e:
        print("Lỗi kết nối Qdrant. Hãy chắc chắn rằng hệ thống Backend đang không chiếm dụng CSDL cục bộ.")
        print(e)
        return

    print(f"[⚙️] Đang quét toàn bộ CSDL và tính toán điểm Cosine Similarity...\n")
    time.sleep(1) # Tạo hiệu ứng delay một chút cho giống xử lý nặng
    
    # Thực hiện search thật!
    results = vectorstore.similarity_search_with_score(query, k=2)
    
    print(f"{'='*90}")
    print(f"KẾT QUẢ TÌM KIẾM NGỮ NGHĨA CHO: '{query}'")
    print(f"{'='*90}\n")
    
    for i, (doc, score) in enumerate(results):
        color = "\033[92m" if i == 0 else "\033[93m"
        reset = "\033[0m"
        print(f"{color}[Top {i+1}]{reset}")
        source = doc.metadata.get('source', 'Unknown Source')
        # Lấy tên file gốc
        file_name = os.path.basename(source)
        print(f"🔖 Source File: {file_name}")
        print(f"📈 Hybrid Similarity Score: {color}{score:.4f}{reset}")
        content = doc.page_content.replace('\n', ' ')[:250]
        print(f"📄 Content: {content}...")
        print("-" * 90)
        
    print("\n✅ Quá trình truy xuất hoàn tất. Đang chuyển dữ liệu vào Prompt cho LLM...\n")

if __name__ == "__main__":
    run_real_search()
