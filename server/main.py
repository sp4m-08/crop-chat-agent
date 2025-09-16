import os
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.openapi.utils import get_openapi

load_dotenv()

from .routes.chat import router as chat_router

app = FastAPI(
    title="Crop/Farmer Chatbot Backend",
    description="A multi-agent system to assist farmers with crop management.",
    version="1.0.0",
)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Crop/Farmer Chatbot Backend",
        version="1.0.0",
        description="A multi-agent system to assist farmers with crop management.",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema
app.openapi = custom_openapi
app.include_router(chat_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to the Crop/Farmer Chatbot API. Navigate to /docs for API documentation."}

@app.get("/health")
async def health_check():
    return {"status": "ok"}