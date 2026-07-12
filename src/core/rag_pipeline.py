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

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_qdrant import QdrantVectorStore, FastEmbedSparse
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

def setup_rag_pipeline(persist_directory: str = "./qdrant_db"):
    """
    Thiết lập đường ống (Pipeline) RAG hoàn chỉnh:
    Nhận câu hỏi -> Tìm kiếm Vector -> Nạp Prompt -> Gemini trả lời.
    """
    # 1. Kết nối lại với Vector Database Qdrant
    print("Đang kết nối với cơ sở dữ liệu Qdrant...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    client = QdrantClient(path=persist_directory)
    
    # Cấu hình Sparse Embeddings (BM25) cho Hybrid Search
    sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
    
    vectorstore = QdrantVectorStore(
        client=client,
        collection_name="mineru_docs",
        embedding=embeddings,
        sparse_embedding=sparse_embeddings,
        retrieval_mode="hybrid"
    )
    
    # Thiết lập bộ tìm kiếm (Retriever)
    qdrant_filter = rest.Filter(
        must=[
            rest.FieldCondition(
                key="metadata.status",
                match=rest.MatchValue(value="active"),
            )
        ]
    )
    # Lấy ra số lượng tài liệu nhiều hơn (k=10) để đưa vào bước Reranking
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10, "filter": qdrant_filter})
    
    # 1.5 Thiết lập Reranker (Ví dụ: BAAI/bge-reranker-base)
    print("Đang khởi tạo mô hình Reranker (Cross-Encoder)...")
    cross_encoder = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")
    # Lọc lại chỉ lấy 3 kết quả tốt nhất
    compressor = CrossEncoderReranker(model=cross_encoder, top_n=3)
    
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=retriever
    )
    
    # 2. Thiết lập mô hình AI Gemini Pro 1.5
    print("Đang khởi tạo Gemini Pro...")
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0.2)
    
    # 3. Thiết lập Mẫu Prompt chuyên dụng cho RAG
    qa_system_prompt = """Bạn là một chuyên gia phân tích dữ liệu chuyên nghiệp.
Sử dụng các thông tin ngữ cảnh sau đây để trả lời câu hỏi.
Nếu bạn không biết câu trả lời, hãy nói rõ là bạn không tìm thấy thông tin.
Luôn trả lời bằng tiếng Việt.

Ngữ cảnh:
{context}"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{question}"),
        ]
    )
    
    # Hàm gộp các đoạn văn bản lại với nhau để nạp vào prompt
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
        
    # 4. Xây dựng chuỗi LCEL (LangChain Expression Language)
    print("Đang lắp ráp đường ống RAG...")
    rag_chain = (
        RunnablePassthrough.assign(
            context=lambda x: format_docs(compression_retriever.invoke(x["question"]))
        )
        | prompt
        | llm
        | StrOutputParser()
    )
    
    store = {}
    def get_session_history(session_id: str):
        if session_id not in store:
            store[session_id] = ChatMessageHistory()
        return store[session_id]

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history",
    )
    
    return conversational_rag_chain

if __name__ == "__main__":
    if "GOOGLE_API_KEY" not in os.environ:
        print("LỖI BẢO MẬT: Chưa tìm thấy GOOGLE_API_KEY.")
        print("Vui lòng thiết lập biến môi trường GOOGLE_API_KEY bằng lệnh export.")
        exit(1)
        
    if not os.path.exists("./data/vector_db"):
        print("LỖI: Chưa tìm thấy cơ sở dữ liệu Qdrant (data/vector_db). Vui lòng chạy file indexing.py trước.")
        exit(1)
        
    # Khởi tạo Pipeline
    chain = setup_rag_pipeline(persist_directory="./data/vector_db")
    
    print("\n[HỆ THỐNG RAG ĐÃ SẴN SÀNG]")
    print("Bạn có thể đặt câu hỏi liên tục. Gõ 'exit' hoặc 'quit' để thoát.")
    
    while True:
        try:
            question = input("\nHỏi: ")
            if question.lower().strip() in ['exit', 'quit']:
                break
            if not question.strip():
                continue
                
            print("Đang suy nghĩ...\n")
            # Gửi câu hỏi và in kết quả dần dần (stream)
            for chunk in chain.stream(
                {"question": question},
                config={"configurable": {"session_id": "cli_session"}}
            ):
                print(chunk, end="", flush=True)
            print("\n")
            print("-" * 50)
            
        except (KeyboardInterrupt, EOFError):
            print("\nĐã thoát chương trình.")
            break
