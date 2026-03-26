from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()

try:
    from config import GROQ_API_KEY
except:
    GROQ_API_KEY = None

key = os.getenv("GROQ_API_KEY") or GROQ_API_KEY
print(f"Key loaded: {'YES — ' + key[:12] + '...' if key else 'NO — key is None!'}")

def test_api():
    try:
        client = Groq(api_key=key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Summarize: Patient has a cough."}],
            max_tokens=200,
        )
        print("SUCCESS! AI says:", response.choices[0].message.content[:200])
    except Exception as e:
        print("FAILED:", e)

if __name__ == "__main__":
    test_api()
