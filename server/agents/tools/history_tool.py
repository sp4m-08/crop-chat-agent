from typing import List, Dict, Any

# Simple in-memory store (global variable)
_chat_history_store: Dict[str, List[Dict[str, Any]]] = {}

async def get_chat_history(user_id: str, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    key = f"{user_id}:{session_id}"
    return _chat_history_store.get(key, [])[-limit:]

async def save_chat_turn(user_id: str, session_id: str, user_msg: str, agent_msg: str):
    key = f"{user_id}:{session_id}"
    turn = {"user": user_msg, "agent": agent_msg}
    if key not in _chat_history_store:
        _chat_history_store[key] = []
    _chat_history_store[key].append(turn)

def render_history_for_prompt(history: List[Dict[str, Any]]) -> str:
    # Simple rendering for LLM prompt
    return "\n".join([f"User: {h['user']}\nAgent: {h['agent']}" for h in history])