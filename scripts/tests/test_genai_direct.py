import os
from google import genai

key = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
os.environ["GEMINI_API_KEY"] = key

try:
    client = genai.Client()
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents='Hello'
    )
    print("Success:", response.text)
except Exception as e:
    print("Error:", e)
