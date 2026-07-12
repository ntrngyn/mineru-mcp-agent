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

import subprocess
import tempfile
import hashlib
from mcp.server.fastmcp import FastMCP

# Khởi tạo FastMCP server
mcp = FastMCP("MinerU PDF Parser & RAG Agent")

@mcp.tool()
def parse_pdf(pdf_path: str):
    """
    Phân tích file PDF sang định dạng Markdown sử dụng MinerU (magic-pdf).
    
    Args:
        pdf_path: Đường dẫn tuyệt đối đến file PDF cần phân tích.
    """
    if not os.path.exists(pdf_path):
        return f"Lỗi: Không tìm thấy file tại đường dẫn {pdf_path}"
        
    if not pdf_path.lower().endswith('.pdf'):
        return "Lỗi: File được cung cấp không phải định dạng PDF"

    # Tạo thư mục tạm thời để chứa kết quả đầu ra của MinerU
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Chạy lệnh CLI magic-pdf với phương thức auto phù hợp phiên bản mới nhất
            cmd = ["magic-pdf", "-p", pdf_path, "-o", tmpdir, "-m", "auto"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Tìm file markdown kết quả trong thư mục đầu ra
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            md_dir = os.path.join(tmpdir, pdf_name)
            
            if not os.path.exists(md_dir):
                md_dir = tmpdir
                
            md_file_path = None
            for root, dirs, files in os.walk(md_dir):
                for file in files:
                    if file.endswith('.md'):
                        md_file_path = os.path.join(root, file)
                        break
                if md_file_path:
                    break
                    
            if not md_file_path or not os.path.exists(md_file_path):
                return f"Lỗi: MinerU chạy thành công nhưng không tìm thấy file Markdown kết quả. Log: {result.stdout}"
                
            with open(md_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            return content
            
        except subprocess.CalledProcessError as e:
            return f"Lỗi khi chạy magic-pdf: {e.stderr or e.stdout}"
        except FileNotFoundError:
            return "Lỗi: Không tìm thấy lệnh 'magic-pdf' trên hệ thống. Vui lòng đảm bảo MinerU (magic-pdf) đã được cài đặt thành công và nằm trong thư mục thực thi (PATH)."
        except Exception as e:
            return f"Lỗi không xác định: {str(e)}"

@mcp.tool()
def ask_pdf_with_rag(pdf_path: str, question: str):
    """
    Đọc file PDF bằng MinerU, sau đó dùng hệ thống RAG và AI để trả lời câu hỏi trực tiếp.
    
    Args:
        pdf_path: Đường dẫn tuyệt đối đến file PDF.
        question: Câu hỏi bạn muốn hệ thống AI trả lời dựa trên nội dung file PDF.
    """
    if "GOOGLE_API_KEY" not in os.environ:
        return "LỖI BẢO MẬT: Chưa tìm thấy biến môi trường GOOGLE_API_KEY. Vui lòng cấu hình API Key trước khi sử dụng tính năng trí tuệ nhân tạo."

    # 1. Sử dụng công cụ parse_pdf để lấy nội dung Markdown từ MinerU
    md_content = parse_pdf(pdf_path)
    if md_content.startswith("Lỗi:"):
        return md_content

    # Tạo một thư mục cơ sở dữ liệu Qdrant riêng biệt cho mỗi file PDF dựa trên mã băm của tên file
    pdf_hash = hashlib.md5(pdf_path.encode()).hexdigest()
    db_dir = f"/Users/nguyentrongnguyen/.gemini/antigravity-ide/scratch/mineru-mcp/qdrant_db_{pdf_hash}"
    
    try:
        from src.core.indexing import create_vector_db
        from src.core.rag_pipeline import setup_rag_pipeline
        
        # 2. Lập chỉ mục (Indexing) nếu cơ sở dữ liệu Vector cho file này chưa tồn tại
        if not os.path.exists(db_dir):
            create_vector_db(md_content, persist_directory=db_dir)
        
        # 3. Khởi tạo RAG Pipeline
        chain = setup_rag_pipeline(persist_directory=db_dir)
        
        # 4. Gửi câu hỏi cho Gemini Pro và thu thập câu trả lời
        answer = ""
        for chunk in chain.stream(
            {"question": question},
            config={"configurable": {"session_id": f"mcp_{pdf_hash}"}}
        ):
            answer += chunk
            
        return answer
    except ImportError as e:
        return f"Lỗi thiếu thư viện: Vui lòng đảm bảo bạn đã cài đặt đủ các thư viện yêu cầu (langchain, qdrant-client, fastembed, sentence-transformers,...). Chi tiết: {str(e)}"
    except Exception as e:
        return f"Lỗi trong quá trình xử lý AI/RAG: {str(e)}"

if __name__ == "__main__":
    mcp.run()
