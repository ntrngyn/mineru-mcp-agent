import os
import hashlib
import json

# Tự động nạp file .env nếu tồn tại
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_qdrant import QdrantVectorStore, FastEmbedSparse
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from chunking import chunk_markdown

def extract_metadata_with_ai(text: str, extra_text: str, existing_topics: list, existing_doc_ids: list) -> dict:
    """
    Sử dụng Gemini để tự động đọc tài liệu và trích xuất Topic, Date, và Document ID
    dựa trên danh sách các Topic và Document ID đã có sẵn trong hệ thống (Dynamic Taxonomy Mapping).
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
    topics_str = ", ".join(existing_topics) if existing_topics else "Chưa có chủ đề nào"
    doc_ids_str = ", ".join(existing_doc_ids) if existing_doc_ids else "Chưa có tài liệu nào"
    
    prompt = f"""
Nhiệm vụ của bạn là phân tích tài liệu và trích xuất siêu dữ liệu (metadata) dưới dạng JSON.
Dưới đây là danh sách các chủ đề (topic) ĐANG CÓ: [{topics_str}].
Dưới đây là danh sách các định danh tài liệu (document_id) ĐANG CÓ: [{doc_ids_str}].

YÊU CẦU:
1. Trích xuất "topic" (chủ đề): Chọn một chủ đề phù hợp nhất từ danh sách trên, hoặc tạo mới nếu hoàn toàn khác biệt.
2. Trích xuất "date" (ngày tháng): Tìm ngày ban hành/hiệu lực của tài liệu (ưu tiên các định dạng như YYYY-MM-DD, Tháng Năm, năm xuất bản). Xuất ra định dạng YYYY-MM-DD (ví dụ: tháng 5 năm 2016 -> 2016-05-01, nếu chỉ có năm -> YYYY-01-01). Nếu không có, trả về "1970-01-01".
3. Trích xuất "document_id" (định danh cốt lõi): Xác định tên gọi/thực thể cốt lõi của tài liệu này. NẾU tài liệu này là phiên bản mới/cũ của một tài liệu đã có trong danh sách document_id ĐANG CÓ ở trên (cùng tên gọi cốt lõi, chỉ khác năm ban hành/phiên bản), bạn PHẢI sử dụng lại chính xác document_id đó. NẾU KHÔNG (tài liệu mới hoàn toàn), hãy tạo một document_id mới (viết liền không dấu, ví dụ: bao_cao_tai_chinh_vinamilk).
4. CHỈ trả về duy nhất một chuỗi JSON hợp lệ, không kèm markdown, không giải thích.

Định dạng trả về:
{{"topic": "...", "date": "YYYY-MM-DD", "document_id": "..."}}

Tài liệu Markdown (trích đoạn 4000 ký tự đầu):
{text[:4000]}

Dữ liệu thô bổ sung (chứa các header/footer bị ẩn):
{extra_text[:5000]}
"""
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        metadata = json.loads(content.strip())
        return metadata
    except Exception as e:
        print(f"Lỗi khi dùng AI trích xuất metadata: {e}")
        return {"topic": "khong_xac_dinh", "date": "1970-01-01", "document_id": "khong_xac_dinh"}

def create_vector_db(markdown_text: str, extra_text: str = "", persist_directory: str = "./qdrant_db"):
    """
    Chia nhỏ văn bản và lưu trữ vào Vector Database (Qdrant).
    """
    print("Đang tiến hành chia nhỏ văn bản Markdown...")
    docs = chunk_markdown(markdown_text)
    
    print("Đang tải mô hình Google Embeddings (Dense)...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    print("Đang tải mô hình BM25 Embeddings (Sparse) cho Hybrid Search...")
    sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
    
    # --- CHUYỂN SANG QDRANT ---
    print(f"Đang kết nối với cơ sở dữ liệu Qdrant tại thư mục '{persist_directory}'...")
    client = QdrantClient(path=persist_directory)
    collection_name = "mineru_docs"
    
    # Tạo collection nếu chưa có
    if not client.collection_exists(collection_name):
        dim = len(embeddings.embed_query("test"))
        client.create_collection(
            collection_name=collection_name,
            vectors_config=rest.VectorParams(size=dim, distance=rest.Distance.COSINE),
            sparse_vectors_config={
                "langchain-sparse": rest.SparseVectorParams(
                    index=rest.SparseIndexParams(on_disk=False)
                )
            }
        )
        
    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
        sparse_embedding=sparse_embeddings,
        retrieval_mode="hybrid"
    )
    
    # --- BƯỚC 1: TRÍCH XUẤT METADATA BẰNG AI ---
    print("Đang phân tích tài liệu bằng AI để tìm Chủ đề và Ngày tháng...")
    try:
        # Lấy một số bản ghi để dò tìm topic cũ
        all_existing, _ = client.scroll(
            collection_name=collection_name,
            limit=1000,
            with_payload=True,
            with_vectors=False
        )
        existing_topics = list(set([m.payload.get('metadata', {}).get('topic') for m in all_existing if m.payload and 'metadata' in m.payload and m.payload['metadata'].get('topic')]))
        existing_doc_ids = list(set([m.payload.get('metadata', {}).get('document_id') for m in all_existing if m.payload and 'metadata' in m.payload and m.payload['metadata'].get('document_id')]))
    except Exception:
        existing_topics = []
        existing_doc_ids = []
        
    ai_meta = extract_metadata_with_ai(markdown_text, extra_text, existing_topics, existing_doc_ids)
    new_topic = ai_meta.get("topic", "khong_xac_dinh")
    new_date = ai_meta.get("date", "1970-01-01")
    new_doc_id = ai_meta.get("document_id", "khong_xac_dinh")
    print(f"-> Chủ đề (Topic): {new_topic}")
    print(f"-> Ngày tháng (Date): {new_date}")
    print(f"-> Định danh tài liệu (Doc ID): {new_doc_id}")
    
    # --- BƯỚC 4: GIẢI QUYẾT XUNG ĐỘT THỜI GIAN (Temporal Resolution) ---
    print("Đang kiểm tra xung đột thời gian với các tài liệu cũ...")
    try:
        topic_docs, _ = client.scroll(
            collection_name=collection_name,
            scroll_filter=rest.Filter(
                must=[
                    rest.FieldCondition(
                        key="metadata.document_id", 
                        match=rest.MatchValue(value=new_doc_id)
                    )
                ]
            ),
            limit=10000,
            with_payload=True
        )
        
        ids_to_supersede = []
        for doc in topic_docs:
            old_meta = doc.payload.get('metadata', {})
            old_date = old_meta.get('date', '1970-01-01')
            old_status = old_meta.get('status', 'active')
            
            if old_date < new_date and old_status == 'active':
                ids_to_supersede.append(doc.id)
                
        if ids_to_supersede:
            print(f"Phát hiện {len(ids_to_supersede)} đoạn văn bản cũ thuộc tài liệu '{new_doc_id}'. Đang vô hiệu hóa (superseded)...")
            
            for doc in topic_docs:
                if doc.id in ids_to_supersede:
                    updated_meta = doc.payload.get('metadata', {}).copy()
                    updated_meta['status'] = 'superseded'
                    client.set_payload(
                        collection_name=collection_name,
                        payload={"metadata": updated_meta},
                        points=[doc.id],
                    )
            print("Đã vô hiệu hóa thành công tài liệu cũ!")
    except Exception as e:
        print(f"Bỏ qua giải quyết xung đột (có thể do DB mới tinh): {e}")
    
    # --- BƯỚC 2: LỌC TRÙNG LẶP HASH & LƯU DB ---
    print("Đang kiểm tra trùng lặp dữ liệu (Hash)...")
    unique_docs = []
    skipped_count = 0
    
    for doc in docs:
        doc_hash = hashlib.md5(doc.page_content.encode('utf-8')).hexdigest()
        
        doc.metadata['hash'] = doc_hash
        doc.metadata['status'] = 'active'
        doc.metadata['topic'] = new_topic
        doc.metadata['date'] = new_date
        doc.metadata['document_id'] = new_doc_id
        
        # Kiểm tra Hash trong Qdrant
        try:
            existing, _ = client.scroll(
                collection_name=collection_name,
                scroll_filter=rest.Filter(
                    must=[
                        rest.FieldCondition(
                            key="metadata.hash", 
                            match=rest.MatchValue(value=doc_hash)
                        ),
                        rest.FieldCondition(
                            key="metadata.status", 
                            match=rest.MatchValue(value="active")
                        )
                    ]
                ),
                limit=1
            )
            if existing and len(existing) > 0:
                skipped_count += 1
                continue
        except Exception:
            pass
            
        unique_docs.append(doc)
        
    print(f"Đã bỏ qua {skipped_count} đoạn văn bản trùng lặp.")
    
    if unique_docs:
        print(f"Đang tính toán và lưu trữ {len(unique_docs)} đoạn văn bản mới vào Qdrant...")
        vectorstore.add_documents(unique_docs)
    else:
        print("Không có văn bản nào mới cần lưu trữ.")
        
    print("Tuyệt vời! Quá trình nạp liệu (Smart Ingestion) thành công.")
    return vectorstore

if __name__ == "__main__":
    if "GOOGLE_API_KEY" not in os.environ:
        print("Lỗi thiếu Key")
    else:
        md_path = input("\nNhập đường dẫn đến file Markdown (.md) vừa xuất ra: ").strip()
        if not os.path.exists(md_path):
            print(f"Không tìm thấy file {md_path}. Vui lòng chạy MinerU trước!")
        else:
            with open(md_path, "r", encoding="utf-8") as f:
                thuc_te_markdown = f.read()
            
            extra_text = ""
            json_path = md_path.replace('.md', '_middle.json')
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        raw_json = f.read()
                    import re
                    contents = re.findall(r'"content":\s*"([^"]+)"', raw_json)
                    extra_text = " ".join(contents[:100]) # Lấy 100 block text đầu tiên
                except Exception as e:
                    pass
            
            create_vector_db(thuc_te_markdown, extra_text, persist_directory="./data/vector_db")
