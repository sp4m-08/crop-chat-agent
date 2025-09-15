from typing import List, Dict, Any
from datetime import datetime, timezone
from ...services.mongo_client import get_db

COLL = "chat_history"

async def get_chat_history(user_id: str, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    db = get_db()
    cursor = (
        db[COLL]
        .find({"user_id": user_id, "session_id": session_id})
        .sort("ts", -1)
        .limit(limit)
    )
    docs = [d async for d in cursor]
    docs.reverse()
    return [{"role": d["role"], "content": d["content"], "ts": d["ts"]} for d in docs]

async def save_chat_turn(user_id: str, session_id: str, user_message: str, assistant_message: str) -> None:
    db = get_db()
    ts = datetime.now(timezone.utc)
    await db[COLL].insert_many([
        {"user_id": user_id, "session_id": session_id, "role": "user", "content": user_message, "ts": ts},
        {"user_id": user_id, "session_id": session_id, "role": "assistant", "content": assistant_message, "ts": ts},
    ])

def render_history_for_prompt(history: List[Dict[str, Any]]) -> str:
    lines = []
    for h in history:
        role = "Farmer" if h["role"] == "user" else "Assistant"
        lines.append(f"{role}: {h['content']}")
    return "\n".join(lines[-20:])