import time
import requests
import statistics
import csv

# Cấu hình
LOCAL_API_URL = "http://localhost:8000/chat"
CLOUD_API_URL = "http://YOUR_EC2_IP:8000/chat"  # Thay bằng IP thực tế của AWS EC2

QUERIES = [
    "Thuật toán Adam đề xuất các giá trị mặc định cho \\beta_1, \\beta_2 và \\epsilon là bao nhiêu?",
    "Tốc độ FPS và độ chính xác mAP của YOLO tiêu chuẩn và Fast YOLO là bao nhiêu?",
    "Độ lỗi top-5 error (%) của mô hình ResNet-152 (10-crop testing) đạt được là bao nhiêu?",
    "Công thức tính cơ chế chú ý Scaled Dot-Product Attention được định nghĩa thế nào?"
]

def estimate_tokens(text: str) -> int:
    """
    Ước lượng số token dựa trên số từ (1 từ tiếng Anh ~ 1.33 tokens, tiếng Việt có thể cao hơn).
    Sử dụng tỷ lệ 1.5 để ước lượng an toàn cho tiếng Việt.
    """
    return int(len(text.split()) * 1.5)

def run_performance_test(api_url: str, env_name: str, mode_name: str = "Hybrid"):
    print(f"\n--- Bắt đầu kiểm thử trên môi trường: {env_name} ({mode_name}) ---")
    
    latencies = []
    total_tokens_input = 0
    total_tokens_output = 0
    
    results = []

    for i, question in enumerate(QUERIES):
        print(f"[{i+1}/{len(QUERIES)}] Đang truy vấn: {question}")
        
        payload = {
            "session_id": f"perf_test_{env_name}_{i}",
            "question": question
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(api_url, json=payload, timeout=30)
            end_time = time.time()
            
            latency = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                
                # Ước lượng Token
                tokens_in = estimate_tokens(question)
                tokens_out = estimate_tokens(answer)
                
                latencies.append(latency)
                total_tokens_input += tokens_in
                total_tokens_output += tokens_out
                
                results.append({
                    "Question": question,
                    "Environment": env_name,
                    "Mode": mode_name,
                    "Latency(s)": round(latency, 3),
                    "Tokens_In": tokens_in,
                    "Tokens_Out": tokens_out,
                    "Status": "Success"
                })
                print(f"   -> Latency: {latency:.3f}s | Tokens In/Out: {tokens_in}/{tokens_out}")
            else:
                print(f"   -> Error: HTTP {response.status_code}")
                results.append({
                    "Question": question,
                    "Environment": env_name,
                    "Mode": mode_name,
                    "Latency(s)": round(latency, 3),
                    "Tokens_In": 0,
                    "Tokens_Out": 0,
                    "Status": f"Error {response.status_code}"
                })
                
        except requests.exceptions.RequestException as e:
            print(f"   -> Request Failed: {e}")
            results.append({
                "Question": question,
                "Environment": env_name,
                "Mode": mode_name,
                "Latency(s)": 0,
                "Tokens_In": 0,
                "Tokens_Out": 0,
                "Status": "Failed"
            })

    # Tổng kết
    if latencies:
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
        
        print("\n=== KẾT QUẢ TỔNG QUAN ===")
        print(f"Môi trường: {env_name} | Mode: {mode_name}")
        print(f"Số lượng truy vấn thành công: {len(latencies)}/{len(QUERIES)}")
        print(f"Average Latency: {avg_latency:.3f}s")
        print(f"P95 Latency: {p95_latency:.3f}s")
        print(f"Total Tokens In: {total_tokens_input} | Total Tokens Out: {total_tokens_output}")
        print("=========================\n")
    
    return results

if __name__ == "__main__":
    all_results = []
    
    # Chạy trên Local (Đảm bảo FastAPI backend đang bật)
    print("Mẹo: Đảm bảo bạn đã khởi chạy 'docker-compose up -d' ở local trước khi test.")
    try:
        local_res = run_performance_test(LOCAL_API_URL, env_name="Local", mode_name="Hybrid Search")
        all_results.extend(local_res)
    except Exception as e:
        print(f"Lỗi khi chạy Local: {e}")
        
    # (Tùy chọn) Chạy trên Cloud nếu đã điền IP
    if "YOUR_EC2_IP" not in CLOUD_API_URL:
        cloud_res = run_performance_test(CLOUD_API_URL, env_name="Cloud (AWS)", mode_name="Hybrid Search")
        all_results.extend(cloud_res)
    else:
        print("\n[!] Bỏ qua test trên Cloud. Hãy thay đổi CLOUD_API_URL bằng IP của AWS EC2 để so sánh.")
        
    # Xuất ra file CSV
    csv_file = "performance_metrics.csv"
    if all_results:
        keys = all_results[0].keys()
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_results)
        print(f"Đã xuất dữ liệu đo lường ra file: {csv_file}")
