import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.core.rag_pipeline import setup_rag_pipeline

# Load env từ thư mục gốc
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

app = FastAPI(title="Multi-User RAG API")

# Khởi tạo RAG Pipeline dùng chung từ core
try:
    conversational_rag_chain = setup_rag_pipeline(persist_directory="./data/vector_db")
except Exception as e:
    print(f"Cảnh báo: Không thể khởi tạo RAG Pipeline khi khởi động server. Lỗi: {e}")
    conversational_rag_chain = None

# Định nghĩa API
class ChatRequest(BaseModel):
    session_id: str
    question: str

class ChatResponse(BaseModel):
    answer: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if conversational_rag_chain is None:
        raise HTTPException(status_code=500, detail="RAG Pipeline chưa được khởi tạo. Hãy chắc chắn bạn đã lập chỉ mục (indexing) dữ liệu.")
        
    try:
        # Gửi request vào chain
        response = conversational_rag_chain.invoke(
            {"question": request.question},
            config={"configurable": {"session_id": request.session_id}}
        )
        return ChatResponse(answer=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
