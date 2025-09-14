import os
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

# Initialize the LLM with your API key from environment variables
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    verbose=True,
    temperature=0.7,
    max_output_tokens=1024,
)
