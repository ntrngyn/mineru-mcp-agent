import os
from langchain_google_genai import ChatGoogleGenerativeAI

key = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
os.environ["GOOGLE_API_KEY"] = key

try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.1)
    res = llm.invoke("Hello")
    print("Success:", res.content)
except Exception as e:
    print("Error:", e)
