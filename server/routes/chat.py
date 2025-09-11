from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from ..agents.orchestrator import run_agent_crew

class ChatRequest(BaseModel):
    user_id: str
    message: str

router = APIRouter()

@router.post("/chat")
async def chat_with_agent(request: ChatRequest) -> Dict[str, Any]:
    """
    Endpoint to receive user chat messages and forward them to the multi-agent system.
    """
    try:
        response = await run_agent_crew(user_id=request.user_id, message=request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))