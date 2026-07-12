import os
import math

def count_tokens(text: str):
    """
    Đếm số lượng token ước tính trong văn bản (1 token ~ 4 ký tự).
    Sử dụng công thức ước lượng đơn giản để không phụ thuộc thư viện ngoài (tiktoken).
    """
    return math.ceil(len(text) / 4)

def get_doc_toc(markdown_text: str):
    """
    Mô phỏng MCP tool 'doc-toc': Lấy mục lục của tài liệu.
    """
    toc = []
    lines = markdown_text.split('\n')
    for idx, line in enumerate(lines):
        if line.startswith('#'):
            toc.append({"line_number": idx + 1, "heading": line.strip()})
    return toc

def get_doc_read(markdown_text: str, start_line: int, end_line: int):
    """
    Mô phỏng MCP tool 'doc-read': Đọc một đoạn tài liệu theo số dòng.
    """
    lines = markdown_text.split('\n')
    # 1-indexed to 0-indexed
    return "\n".join(lines[start_line - 1 : end_line])

def demo_deep_reading():
    print("="*60)
    print("DEMO KỸ THUẬT DEEP READING (TUẦN 5)")
    print("="*60)
    
    # Tạo một văn bản mẫu giả lập tài liệu dài (báo cáo)
    sample_markdown = """# Chương 1: Giới thiệu
Đây là phần giới thiệu về dự án AI Agent.
Dự án sử dụng MCP và LLM để tự động hóa công việc.

## 1.1 Mục tiêu
Xây dựng một hệ thống RAG hiệu quả và tối ưu chi phí Token.
Hệ thống này sẽ giúp các doanh nghiệp đọc và truy xuất thông tin từ PDF nhanh chóng.

# Chương 2: Cơ sở Lý thuyết
Phần này trình bày lý thuyết về Vector Database, Embedding, và RAG.
Chúng ta sẽ tìm hiểu cách Qdrant lưu trữ các Vector và tính Cosine Similarity.

## 2.1 Vector Database là gì?
Vector database là cơ sở dữ liệu chuyên dụng để lưu trữ các biểu diễn toán học (vector) của văn bản.
""" * 500  # Nhân bản lên 500 lần để làm tài liệu dài (giả lập sách/báo cáo)
    
    # Giả sử LLM nhận được yêu cầu: "Tìm hiểu về Mục tiêu của dự án"
    num_lines = len(sample_markdown.split('\n'))
    print(f"Tổng số dòng của toàn bộ tài liệu giả lập: {num_lines:,}")
    total_tokens = count_tokens(sample_markdown)
    print(f"Tổng số token nếu nạp TOÀN BỘ tài liệu vào LLM: ~{total_tokens:,} tokens")
    
    print("\n--- BƯỚC 1: LLM gọi tool 'doc-toc' để lấy mục lục ---")
    toc = get_doc_toc(sample_markdown)
    # Lấy TOC của phần gốc để minh họa (bỏ qua phần lặp lại)
    unique_toc = [t for t in toc if t['line_number'] <= 16]
    for item in unique_toc:
        print(f"  Dòng {item['line_number']:03d}: {item['heading']}")
        
    toc_tokens = count_tokens(str(unique_toc))
    print(f"-> Token tiêu tốn cho việc đọc mục lục: ~{toc_tokens:,} tokens")
    
    print("\n--- BƯỚC 2: LLM gọi tool 'doc-read' để chỉ đọc phần liên quan ---")
    # Dựa vào TOC, LLM nhận thấy phần "1.1 Mục tiêu" nằm từ dòng 6 đến trước chương 2 (dòng 10)
    print("Agent quyết định chỉ đọc phần liên quan (từ dòng 6 đến dòng 9)...")
    relevant_content = get_doc_read(sample_markdown, 6, 9)
    print(f"Nội dung đọc được:\n{'-'*40}\n{relevant_content}\n{'-'*40}")
    
    read_tokens = count_tokens(relevant_content)
    print(f"-> Token tiêu tốn cho việc nạp phần chi tiết này: ~{read_tokens:,} tokens")
    
    print("\n" + "="*60)
    print("📊 BẢNG ĐO LƯỜNG TỐI ƯU TOKEN (DEEP READING VS TRUYỀN THỐNG)")
    print("="*60)
    total_deep_reading = toc_tokens + read_tokens
    print(f"Tổng Token (Truyền thống - Nạp cả file): {total_tokens:,}")
    print(f"Tổng Token (Deep Reading)              : {total_deep_reading:,}")
    print("-" * 60)
    saved_tokens = total_tokens - total_deep_reading
    saved_percentage = (saved_tokens / total_tokens) * 100
    print(f"✅ CHÊNH LỆCH: Tiết kiệm được {saved_tokens:,} tokens (Giảm {saved_percentage:.2f}% chi phí)")
    
if __name__ == "__main__":
    demo_deep_reading()
