import os

# Tự động nạp file .env nếu tồn tại
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

from qdrant_client import QdrantClient

def inspect_qdrant_db():
    db_dir = "./data/vector_db"
    collection_name = "mineru_docs"

    if not os.path.exists(db_dir):
        print(f"Lỗi: Không tìm thấy thư mục cơ sở dữ liệu tại '{db_dir}'")
        return

    # Khởi tạo lại đối tượng QdrantClient từ thư mục lưu trữ
    try:
        client = QdrantClient(path=db_dir)
    except Exception as e:
        print(f"Lỗi khi kết nối Qdrant: {e}\n(Lưu ý: Bạn không thể chạy file này nếu Backend đang chạy vì Qdrant local chỉ cho phép 1 kết nối tại 1 thời điểm).")
        return

    if not client.collection_exists(collection_name):
        print(f"Lỗi: Collection '{collection_name}' không tồn tại trong database.")
        return

    # Lấy dữ liệu từ collection (giới hạn 1000 bản ghi để tránh quá tải)
    records, _ = client.scroll(
        collection_name=collection_name,
        limit=1000,
        with_payload=True,
        with_vectors=True
    )
    
    print("\n" + "="*50)
    print(f"📊 KẾT QUẢ KIỂM TRA QDRANT CỤC BỘ")
    print("="*50)
    print(f"🔹 Tổng số chunks/bản ghi hiện có: {len(records)}")
    
    if len(records) == 0:
        print("❌ Database rỗng.")
        return

    # Thống kê sơ bộ các chủ đề (topic) và trạng thái (status)
    topics_count = {}
    status_count = {"active": 0, "superseded": 0}
    for r in records:
        meta = r.payload.get("metadata", {})
        topic = meta.get("topic", "unknown")
        status = meta.get("status", "unknown")
        
        topics_count[topic] = topics_count.get(topic, 0) + 1
        if status in status_count:
            status_count[status] += 1
        else:
            status_count[status] = 1

    print(f"🔹 Phân loại theo Trạng thái:")
    for st, count in status_count.items():
        print(f"   - {st}: {count} chunks")
        
    print(f"🔹 Phân loại theo Chủ đề (Topic):")
    for tp, count in topics_count.items():
        print(f"   - {tp}: {count} chunks")

    # In thông tin của 2 bản ghi đầu tiên làm mẫu
    sample_size = min(2, len(records))
    for i in range(sample_size):
        r = records[i]
        payload = r.payload or {}
        metadata = payload.get("metadata", {})
        page_content = payload.get("page_content", "")
        vector = r.vector

        print("\n" + "-"*40)
        print(f"📝 BẢN GHI MẪU {i + 1} / {len(records)}")
        print(f"📍 ID: {r.id}")
        print(f"🏷️ Metadata: {metadata}")
        if vector is not None:
            print(f"🔢 Embedding Vector ({len(vector)} chiều): [{', '.join(f'{x:.5f}' for x in vector[:5])}, ...]")
        else:
            print(f"🔢 Embedding Vector: Không tìm thấy")
        print(f"📄 Nội dung văn bản (300 ký tự đầu):")
        print(f"   {repr(page_content[:300])}...")
        print("-"*40)

if __name__ == "__main__":
    inspect_qdrant_db()
