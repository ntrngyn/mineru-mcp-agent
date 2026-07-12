# Hướng dẫn triển khai (Deployment Guide) lên AWS EC2

Tài liệu này hướng dẫn cách đưa toàn bộ hệ thống (FastAPI, Streamlit, FastMCP Server) lên máy chủ đám mây AWS EC2 (hệ điều hành Ubuntu).

## Bước 1: Khởi tạo AWS EC2 Instance
1. Đăng nhập vào AWS Management Console.
2. Điều hướng đến dịch vụ **EC2** và chọn **Launch Instance**.
3. **Cấu hình Instance:**
   - **Tên:** `MinerU-MCP-Server`
   - **Hệ điều hành (AMI):** Ubuntu Server 22.04 LTS hoặc 24.04 LTS (64-bit).
   - **Instance Type:** Tối thiểu `t3.large` (2 vCPU, 8 GB RAM) do mô hình xử lý PDF/Vector tốn khá nhiều bộ nhớ.
   - **Key pair:** Tạo key pair mới (ví dụ `mineru-key.pem`) và tải về máy tính để có thể truy cập SSH.
   - **Network settings:**
     - Cho phép SSH traffic from Anywhere (hoặc IP của bạn).
     - Cho phép HTTP/HTTPS traffic.

## Bước 2: Cấu hình Security Group (Mở Port)
Sau khi Instance được tạo, bạn cần mở các cổng mạng (ports) mà hệ thống sử dụng.
1. Trong màn hình cấu hình EC2, kéo xuống phần **Security**, click vào link Security groups (ví dụ: `sg-0xxxx`).
2. Chọn mục **Inbound rules** -> **Edit inbound rules**.
3. Thêm các quy tắc (Add rule) sau:
   - **Custom TCP** | Port **8000** | Source: `Anywhere-IPv4` (0.0.0.0/0) -> Cho FastAPI
   - **Custom TCP** | Port **8001** | Source: `Anywhere-IPv4` (0.0.0.0/0) -> Cho MCP Server (SSE)
   - **Custom TCP** | Port **8501** | Source: `Anywhere-IPv4` (0.0.0.0/0) -> Cho Streamlit Web App
4. Lưu cấu hình (Save rules).

## Bước 3: Đăng nhập SSH và Cài đặt Docker
Mở Terminal (hoặc Command Prompt / PowerShell) và SSH vào máy chủ bằng Key pair đã tải về (thay `IP_CỦA_EC2` bằng IP Public của bạn):

```bash
# Phân quyền cho file key (trên MacOS/Linux)
chmod 400 mineru-key.pem

# SSH vào server
ssh -i mineru-key.pem ubuntu@IP_CỦA_EC2
```

Sau khi SSH thành công, chạy script cài đặt Docker dưới đây:
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Thêm repository Docker
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Cấp quyền cho user ubuntu chạy docker không cần sudo
sudo usermod -aG docker ubuntu
newgrp docker
```

## Bước 4: Triển khai mã nguồn
Trên máy chủ AWS, tải mã nguồn về (thông qua Git hoặc SCP/SFTP). Sau đó vào thư mục dự án và khởi chạy Docker Compose:

```bash
# Clone source code
git clone <đường-dẫn-repo-github> mineru-mcp
cd mineru-mcp

# Cấu hình biến môi trường
nano .env
# (Dán các nội dung biến môi trường như GOOGLE_API_KEY, GROQ_API_KEY vào đây)

# Build và chạy ngầm (Daemon mode)
docker compose up -d --build
```

## Bước 5: Kiểm tra kết nối
Khi tiến trình cài đặt hoàn tất, bạn có thể truy cập hệ thống qua trình duyệt:
- **Giao diện Web:** `http://IP_CỦA_EC2:8501`
- **FastAPI Docs:** `http://IP_CỦA_EC2:8000/docs`
- **MCP Server (SSE Endpoint):** `http://IP_CỦA_EC2:8001/sse` (Sử dụng URL này để cấu hình MCP Client từ xa như Cursor, Claude Desktop bằng kết nối SSE).
