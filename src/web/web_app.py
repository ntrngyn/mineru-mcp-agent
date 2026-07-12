import streamlit as st
import requests
import uuid
import os

# Cấu hình trang
st.set_page_config(page_title="Hệ thống Hỏi Đáp", page_icon="🤖", layout="centered")

# Tiêu đề giao diện
st.title("🤖 Chatbot (RAG)")
st.caption("Trợ lý AI giúp tra cứu nhanh tài liệu nội bộ, tự động cập nhật dữ liệu mới nhất.")

# Sinh session_id tự động cho mỗi người dùng (lưu trong session_state của Streamlit)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Khởi tạo danh sách tin nhắn
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử chat trên giao diện
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ô nhập liệu chat ở dưới cùng
if prompt := st.chat_input("Nhập câu hỏi của bạn vào đây..."):
    # 1. Thêm tin nhắn của người dùng vào giao diện
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Gọi API backend để lấy câu trả lời
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("⏳ Đang suy nghĩ...")
        
        try:
            # Gửi yêu cầu tới FastAPI Server
            api_url = os.environ.get("API_URL", "http://localhost:8000/chat")
            response = requests.post(
                api_url,
                json={
                    "session_id": st.session_state.session_id, 
                    "question": prompt
                }
            )
            response.raise_for_status()
            
            # Lấy câu trả lời
            answer = response.json()["answer"]
            
            # Hiển thị và lưu lại
            message_placeholder.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = response.json().get("detail", str(e))
            except:
                error_detail = str(e)
            message_placeholder.error(f"🚨 Lỗi từ máy chủ AI: {error_detail}")
        except requests.exceptions.ConnectionError:
            message_placeholder.error("🚨 Lỗi: Không thể kết nối tới máy chủ AI. Vui lòng kiểm tra xem Backend (api_server.py) đã được chạy chưa.")
        except Exception as e:
            message_placeholder.error(f"🚨 Đã xảy ra lỗi: {e}")
