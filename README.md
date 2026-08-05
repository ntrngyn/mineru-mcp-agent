# Đề tài: Nghiên cứu Tối ưu hiệu suất đọc hiểu tài liệu trên nền tảng MCP-LLM

Dự án này là hệ thống triển khai kiến trúc RAG tích hợp công nghệ xử lý tài liệu MinerU và giao thức Model Context Protocol (MCP).

## Cấu trúc hệ thống
Hệ thống được đóng gói hoàn toàn bằng Docker với kiến trúc Microservices bao gồm 3 thành phần chính:
1. **Frontend (Streamlit)**: Giao diện WebUI Chatbot (Port `8501`)
2. **Backend (FastAPI)**: Xử lý logic RAG và giao tiếp với Vector DB (Port `8000`)
3. **MCP Server**: Cung cấp các công cụ khai phá tài liệu chuẩn MCP (Port `8001`)

## Hướng dẫn cài đặt và khởi chạy

### Bước 0: Giải nén mã nguồn
Sau khi tải/nhận file `.zip` chứa mã nguồn, hãy giải nén file đó ra một thư mục. Sau đó, mở Terminal/Command Prompt và di chuyển (lệnh `cd`) vào thư mục gốc của dự án vừa giải nén.

### Bước 1: Cấu hình biến môi trường
Kiểm tra file `.env` ở thư mục gốc (nếu chưa có, hãy copy từ `.env.example` hoặc tạo mới file `.env`). Hãy cập nhật các API Key cần thiết (bao gồm `GOOGLE_API_KEY` cho Embeddings và `GROQ_API_KEY` cho Llama 3) vào file này.

Bạn có thể chạy dự án bằng 1 trong 2 cách sau:

### Cách 1: Khởi chạy bằng Docker (Khuyên dùng)
**Yêu cầu:** Đã cài đặt **Docker** và **Docker Compose** trên máy.
1. Mở Terminal tại thư mục gốc và chạy lệnh:
   ```bash
   docker-compose up --build -d
   ```
2. Lệnh này sẽ tự động tải các base image, cài đặt thư viện và chạy cả 3 dịch vụ lên. Để dừng hệ thống, chạy lệnh:
   ```bash
   docker-compose down
   ```

### Cách 2: Khởi chạy trực tiếp (Local - Không dùng Docker)
**Yêu cầu:** Đã cài đặt **Python 3.10+**.
1. Tạo và kích hoạt môi trường ảo (Virtual Environment):
   ```bash
   python -m venv mineru-env
   # Trên Mac/Linux:
   source mineru-env/bin/activate
   # Trên Windows:
   .\mineru-env\Scripts\activate
   ```
2. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
3. Mở Terminal thứ 1 để chạy API Backend (FastAPI):
   ```bash
   uvicorn src.api.api_server:app --host 0.0.0.0 --port 8000
   ```
4. Mở Terminal thứ 2 để chạy Frontend (Streamlit):
   ```bash
   streamlit run src/web/web_app.py --server.port 8501 --server.address 0.0.0.0
   ```
5. Mở Terminal thứ 3 để chạy MCP Server:
   ```bash
   uvicorn src.mcp.mineru_mcp:mcp.sse_app --host 0.0.0.0 --port 8001
   ```
*(Lưu ý: Bạn cần phải activate môi trường ảo ở tất cả các tab Terminal trước khi chạy lệnh)*

### Bước 3: Truy cập ứng dụng
Dù chạy bằng cách nào, khi hệ thống đã khởi động thành công, bạn có thể truy cập các thành phần sau qua trình duyệt:

- **Giao diện Chatbot (Frontend):** [http://localhost:8501](http://localhost:8501)
- **API Swagger UI (Backend):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **MCP Server (SSE Endpoint):** `http://localhost:8001/sse`

## Lưu ý
- Nếu bạn muốn thêm tài liệu PDF mới, hãy bỏ vào thư mục `data/raw` (nếu có cấu hình đường dẫn tương ứng) hoặc upload qua giao diện web.
- Vector DB (Qdrant) sẽ tự động lưu dữ liệu vào thư mục `data/vector_db` nên dữ liệu sẽ không bị mất khi bạn khởi động lại container.
