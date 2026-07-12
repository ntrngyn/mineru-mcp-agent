# Đề tài: Nghiên cứu Tối ưu hiệu suất đọc hiểu tài liệu trên nền tảng MCP-LLM

Dự án này là hệ thống triển khai kiến trúc RAG tích hợp công nghệ xử lý tài liệu MinerU và giao thức Model Context Protocol (MCP).

## Cấu trúc hệ thống
Hệ thống được đóng gói hoàn toàn bằng Docker với kiến trúc Microservices bao gồm 3 thành phần chính:
1. **Frontend (Streamlit)**: Giao diện WebUI Chatbot (Port `8501`)
2. **Backend (FastAPI)**: Xử lý logic RAG và giao tiếp với Vector DB (Port `8000`)
3. **MCP Server**: Cung cấp các công cụ khai phá tài liệu chuẩn MCP (Port `8001`)

## Hướng dẫn cài đặt và khởi chạy

### Yêu cầu tiên quyết
- Đã cài đặt **Docker** và **Docker Compose** trên máy.

### Bước 1: Cấu hình biến môi trường
1. Kiểm tra file `.env` ở thư mục gốc (nếu chưa có, hãy copy từ `.env.example` hoặc tạo mới file `.env`).
2. Cập nhật các API Key cần thiết (ví dụ: `GEMINI_API_KEY` hoặc các thông số khác) vào file `.env`.

### Bước 2: Khởi chạy hệ thống bằng Docker
Mở Terminal/Command Prompt tại thư mục gốc của dự án (nơi chứa file `docker-compose.yml`) và chạy lệnh sau:

```bash
docker-compose up --build -d
```

Lệnh này sẽ tự động tải các base image, cài đặt thư viện (`requirements.txt`), và chạy cả 3 dịch vụ lên. Quá trình build lần đầu có thể mất vài phút.

### Bước 3: Truy cập ứng dụng
Sau khi terminal báo các container đã chạy thành công (Started), bạn có thể truy cập các thành phần sau qua trình duyệt:

- **Giao diện Chatbot (Frontend):** [http://localhost:8501](http://localhost:8501)
- **API Swagger UI (Backend):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **MCP Server (SSE Endpoint):** `http://localhost:8001/sse`

### Dừng hệ thống
Để dừng hệ thống, chạy lệnh sau:
```bash
docker-compose down
```

## Lưu ý
- Nếu bạn muốn thêm tài liệu PDF mới, hãy bỏ vào thư mục `data/raw` (nếu có cấu hình đường dẫn tương ứng) hoặc upload qua giao diện web.
- Vector DB (Qdrant) sẽ tự động lưu dữ liệu vào thư mục `data/vector_db` nên dữ liệu sẽ không bị mất khi bạn khởi động lại container.
