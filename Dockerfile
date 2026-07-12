FROM python:3.10-slim

WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết (đặc biệt cho MinerU / magic-pdf xử lý PDF/Ảnh)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy và cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Expose port cho FastAPI, Streamlit và MCP Server (SSE)
EXPOSE 8000 8501 8001

# Set PYTHONPATH để Python nhận diện các module trong thư mục src
ENV PYTHONPATH="/app"

# Lệnh mặc định (sẽ bị ghi đè bởi docker-compose)
CMD ["uvicorn", "src.api.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
