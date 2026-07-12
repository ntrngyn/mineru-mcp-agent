import os
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

def chunk_markdown(markdown_text: str, chunk_size: int = 1500, chunk_overlap: int = 150):
    """
    Chia nhỏ văn bản Markdown tối ưu:
    1. Đầu tiên chia theo các thẻ tiêu đề (Header) để bảo toàn cấu trúc ngữ nghĩa.
    2. Sau đó, với các phần nằm dưới một tiêu đề mà quá dài, tiếp tục cắt nhỏ bằng RecursiveCharacterTextSplitter.
    """
    # Bước 1: Chia theo tiêu đề
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(markdown_text)
    
    # Bước 2: Giới hạn độ dài từng đoạn
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""] # Ưu tiên cắt theo đoạn văn, cuối dòng, sau đó mới đến khoảng trắng
    )
    
    final_splits = text_splitter.split_documents(md_header_splits)
    
    return final_splits

if __name__ == "__main__":
    md_path = input("\nNhập đường dẫn đến file Markdown (.md) vừa xuất ra: ").strip()
    if not os.path.exists(md_path):
        print(f"Không tìm thấy file {md_path}. Vui lòng chạy MinerU trước!")
    else:
        with open(md_path, "r", encoding="utf-8") as f:
            sample_markdown = f.read()
            
        print("Đang tiến hành chia nhỏ (Chunking)...")
        chunks = chunk_markdown(sample_markdown)
        
        print(f"Thành công! Tổng số chunks được tạo: {len(chunks)}\n")
        # Ghi toàn bộ chunks ra file để tiện kiểm tra (debug)
        output_dir = os.path.dirname(md_path)
        debug_file = os.path.join(output_dir, "chunks_debug.txt")
        
        with open(debug_file, "w", encoding="utf-8") as out_f:
            out_f.write(f"TỔNG SỐ CHUNKS: {len(chunks)}\n")
            out_f.write("="*60 + "\n\n")
            for i, chunk in enumerate(chunks):
                out_f.write(f"[{i+1}/{len(chunks)}] --- METADATA (Tiêu đề) ---\n")
                out_f.write(f"{chunk.metadata}\n\n")
                out_f.write(f"--- NỘI DUNG ---\n")
                out_f.write(f"{chunk.page_content}\n")
                out_f.write("="*60 + "\n\n")
                
        print(f"Đã xuất toàn bộ nội dung của {len(chunks)} chunks ra file để bạn kiểm tra tại:\n👉 {debug_file}\n")
