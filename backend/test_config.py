import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    print("GEMINI_API_KEY loaded successfully")
else:
    print("GEMINI_API_KEY not found")