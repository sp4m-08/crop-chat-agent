from __future__ import annotations
from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from .agent_roles import llm
from .tools.profile_tool import get_farmer_profile
from .tools.sensor_tool import get_latest_sensor_data
from .tools.weather_tool import get_local_weather
from .tools.history_tool import get_chat_history, save_chat_turn, render_history_for_prompt

# ------------ Shared state passed between nodes ------------
class State(TypedDict, total=False):
    user_id: str
    session_id: str            # add this
    message: str
    intent: str
    history: List[Dict[str, Any]]
    history_summary: str
    profile: Dict[str, Any]
    sensors: Dict[str, Any]
    weather: Dict[str, Any]
    crop_analysis: str
    disease_risk: str
    plan: str
    final_response: str
    trace: List[str]

def _append_trace(state: State, note: str) -> State:
    t = state.get("trace", [])
    t.append(note)
    state["trace"] = t
    return state


# ------------ Nodes (agents) ------------
async def chat_history_node(state: State) -> State:
    history = await get_chat_history(state["user_id"], state["session_id"], limit=20)
    history_text = render_history_for_prompt(history)
    sys = "Summarize this farmer-assistant chat briefly. Keep goals, crops, and unresolved items. <= 120 words."
    user = history_text or "No prior messages."
    summary = (await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=user)])).content
    state["history"] = history
    state["history_summary"] = summary
    return _append_trace(state, "history_loaded")


async def farmer_interaction_node(state: State) -> State:
    prompt = [
        SystemMessage(content="You triage farmer queries. Output only one intent: status | weather | disease | plan | advice."),
        HumanMessage(content=f"User message: {state['message']}"),
    ]
    resp = await llm.ainvoke(prompt)
    intent = resp.content.strip().lower().split()[0]
    
    state["intent"] = intent         
    return _append_trace(state, f"intent={intent}") 

async def farmer_profile_node(state: State) -> State:
    profile = await get_farmer_profile(state["user_id"])
    state["profile"] = profile  # update only profile
    return _append_trace(state, "profile")


async def sensor_data_node(state: State) -> State:
    sensors = await get_latest_sensor_data(state["user_id"])
    state["sensors"] = sensors
    return _append_trace(state, "sensors")

async def weather_node(state: State) -> State:
    location = (state.get("profile") or {}).get("location", "Unknown")
    weather = await get_local_weather(location)
    state["weather"] = weather
    return _append_trace(state, "weather")

async def crop_health_node(state: State) -> State:
    profile = state.get("profile", {})
    crops = profile.get("crops", [])
    crop = crops[0] if crops else "unknown crop"
    sensors = state.get("sensors", {})

    sys = (
        "You are an expert agronomist. From your knowledge, infer ideal environmental ranges "
        "for the specified crop (temperature, humidity, soil moisture, rainfall if relevant). "
        "Compare those inferred ideals with the provided sensor readings. "
        "Point out any risks or deviations and provide practical, field-ready advice. "
        "Be concise and avoid hedging."
    )
    user = (
        f"Recent chat summary: {state.get('history_summary','')}\n"
        f"Crop: {crop}\nFarmer context: {profile}\nSensors: {sensors}\n"
        "Output: 3–5 bullets and a line starting with 'Action:'"
    )

    resp = await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=user)])

    # Update state in-place
    state["crop_analysis"] = resp.content
    return _append_trace(state, "crop_analysis")



async def disease_prediction_node(state: State) -> State:
    crops = (state.get("profile") or {}).get("crops", [])
    crop = crops[0] if crops else "unknown crop"
    sensors = state.get("sensors", {})
    weather = state.get("weather", {})
    sys = "Plant pathologist. Estimate near-term disease risks and preventive actions."
    user = (
        f"Recent chat summary: {state.get('history_summary','')}\n"
        f"Crop: {crop}\nSensors: {sensors}\nWeather: {weather}"
    )
    resp = await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=user)])
    state["disease_risk"] = resp.content
    return _append_trace(state, "disease_risk")


async def lifecycle_planning_node(state: State) -> State:
    profile = state.get("profile", {})
    crops = profile.get("crops", [])
    crop = crops[0] if crops else "unknown crop"
    weather = state.get("weather", {})

    sys = "You prepare seasonal crop operation plans."
    user = (
        f"Crop: {crop}\n"
        f"Location: {profile.get('location')}\n"
        f"Weather summary: {weather}\n"
        "Output: near-term 2-4 week plan (sow/fertilize/irrigate/spray/harvest cues)."
    )
    resp = await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=user)])
    state["plan"] = resp.content
    return _append_trace(state, "plan")



async def response_synthesizer_node(state: State) -> State:
    msg = state["message"]
    profile = state.get("profile", {})
    parts = {
        "History": state.get("history_summary", ""),
        "Crop health": state.get("crop_analysis", ""),
        "Disease": state.get("disease_risk", ""),
        "Plan": state.get("plan", ""),
        "Weather": str(state.get("weather", "")),
        "Sensors": str(state.get("sensors", "")),
    }
    sys = "Farmer-facing assistant. Concise bullets and a final Action line."
    user = f"User query: {msg}\nFarmer profile: {profile}\nContext parts: {parts}\n<= 180 words."
    resp = await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=user)])
    state["final_response"] = resp.content
    # save turn with session_id
    await save_chat_turn(state["user_id"], state["session_id"], msg, state["final_response"])
    return _append_trace(state, "final")


# ------------ Build and run the graph ------------

def _build_graph():
    g = StateGraph(State)
    g.add_node("chat_history", chat_history_node)
    g.add_node("farmer_interaction", farmer_interaction_node)
    g.add_node("farmer_profile", farmer_profile_node)
    g.add_node("sensor_data", sensor_data_node)
    g.add_node("weather", weather_node)
    g.add_node("crop_health", crop_health_node)
    g.add_node("disease_prediction", disease_prediction_node)
    g.add_node("lifecycle_planning", lifecycle_planning_node)
    g.add_node("response", response_synthesizer_node)

    g.set_entry_point("chat_history")
    g.add_edge("chat_history", "farmer_interaction")
    g.add_edge("farmer_interaction", "farmer_profile")
    g.add_edge("farmer_profile", "sensor_data")
    g.add_edge("farmer_profile", "weather")
    g.add_edge("sensor_data", "crop_health")
    g.add_edge("sensor_data", "disease_prediction")
    g.add_edge("weather", "disease_prediction")
    g.add_edge("weather", "lifecycle_planning")
    g.add_edge("crop_health", "response")
    g.add_edge("disease_prediction", "response")
    g.add_edge("lifecycle_planning", "response")
    g.add_edge("response", END)
    return g.compile()

_compiled_graph = _build_graph()

async def run_langgraph_workflow(user_id: str, session_id: str, message: str) -> str:
    initial: State = {"user_id": user_id, "session_id": session_id, "message": message, "trace": []}
    result: State = await _compiled_graph.ainvoke(initial)
    return result.get("final_response", "Sorry, something went wrong.")