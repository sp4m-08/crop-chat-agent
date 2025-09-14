import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))
MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "1024"))

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Set GOOGLE_API_KEY (or GEMINI_API_KEY) in your environment or .env.")

llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    google_api_key=API_KEY,   
    temperature=TEMPERATURE,
    max_output_tokens=MAX_TOKENS,
    verbose=False,
)