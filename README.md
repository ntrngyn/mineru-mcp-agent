# Project: Optimizing Document Reading Performance on MCP-LLM Platform

This project implements a Retrieval-Augmented Generation (RAG) architecture integrating MinerU document processing technology and the Model Context Protocol (MCP).

## System Architecture
The system is fully containerized using Docker with a Microservices architecture consisting of 3 main components:
1. **Frontend (Streamlit)**: WebUI Chatbot Interface (Port `8501`)
2. **Backend (FastAPI)**: RAG logic processing and Vector DB communication (Port `8000`)
3. **MCP Server**: Provides MCP-compliant document extraction tools (Port `8001`)

## Installation and Startup Guide

### Step 0: Extract Source Code
After downloading/receiving the `.zip` file containing the source code, extract it to a folder. Then, open your Terminal/Command Prompt and navigate (`cd`) to the root directory of the extracted project.

### Step 1: Configure Environment Variables
Check for the `.env` file in the root directory (if it doesn't exist, copy from `.env.example` or create a new `.env` file). Update the necessary API Keys (including `GOOGLE_API_KEY` for Embeddings and `GROQ_API_KEY` for Llama 3) in this file.

### Step 2: Indexing Documents (Data Ingestion)
Before asking questions, you need to process and ingest your markdown documents into the Vector Database (Qdrant).
1. Ensure your PDF has been processed into a Markdown file (e.g., using MinerU).
2. Run the indexing script:
   ```bash
   python src/core/indexing.py
   ```
3. When prompted, provide the absolute path to your `.md` file. The system will automatically extract metadata, chunk the document, generate vectors, and save them to `data/vector_db`.

### Step 3: Running the Application
You can run the project using one of the two methods below:

#### Method 1: Using Docker (Recommended)
**Requirements:** **Docker** and **Docker Compose** installed on your machine.
1. Open a Terminal at the root directory and run:
   ```bash
   docker-compose up --build -d
   ```
2. **⚠️ IMPORTANT NOTE FOR FIRST RUN:** 
   When running via Docker for the first time, the Backend container needs to download the AI Reranker model (~1GB) from HuggingFace. **Please wait for about 2-3 minutes** for the backend to finish initializing. If you open the Web UI immediately and send a message, you may receive a "Cannot connect to AI server" error. 
   You can check the backend status by running: `docker logs mineru_api_server -f`. Wait until you see `Application startup complete` before using the chatbot.
3. To stop the system, run:
   ```bash
   docker-compose down
   ```

#### Method 2: Running Locally (Without Docker)
**Requirements:** **Python 3.10+** installed.
1. Create and activate a Virtual Environment:
   ```bash
   python -m venv mineru-env
   # On Mac/Linux:
   source mineru-env/bin/activate
   # On Windows:
   .\mineru-env\Scripts\activate
   ```
2. Install the required libraries:
   ```bash
   pip install -r requirements.txt
   ```
3. Open Terminal 1 to run the Backend API (FastAPI):
   ```bash
   uvicorn src.api.api_server:app --host 0.0.0.0 --port 8000
   ```
4. Open Terminal 2 to run the Frontend (Streamlit):
   ```bash
   streamlit run src/web/web_app.py --server.port 8501 --server.address 0.0.0.0
   ```
5. Open Terminal 3 to run the MCP Server:
   ```bash
   uvicorn src.mcp.mineru_mcp:mcp.sse_app --host 0.0.0.0 --port 8001
   ```
*(Note: You must activate the virtual environment in all Terminal tabs before running the commands)*

### Step 4: Access the Application
Regardless of how you run it, once the system has successfully started, you can access the following components via your web browser:

- **Chatbot Interface (Frontend):** [http://localhost:8501](http://localhost:8501)
- **API Swagger UI (Backend):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **MCP Server (SSE Endpoint):** `http://localhost:8001/sse`

## Notes
- If you want to add new PDF documents, place them in the `data/raw` directory (if a path configuration exists) or upload them via the web interface.
- The Vector DB (Qdrant) automatically saves data to the `data/vector_db` directory, so your indexed data will not be lost when you restart the containers.
