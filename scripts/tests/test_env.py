import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
print("KEY:", os.environ.get('GOOGLE_API_KEY'))
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
embeddings.embed_query("test")
print("SUCCESS")
