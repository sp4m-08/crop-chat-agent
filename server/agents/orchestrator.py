from __future__ import annotations
from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from .agent_roles import llm
from tools.profile_tool import get_farmer_profile
from .tools.sensor_tool import get_latest_sensor_data
from .tools.weather_tool import get_local_weather


# ------------ Shared state passed between nodes ------------
class State(TypedDict, total=False):
    user_id: str
    message: str
    intent: str
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
    return {"trace": t}

# ------------ Nodes (agents) ------------

async def farmer_interaction_node(state: State) -> State:
    prompt = [
        SystemMessage(content="You triage farmer queries. Output only one intent: status | weather | disease | plan | advice."),
        HumanMessage(content=f"User message: {state['message']}"),
    ]
    resp = await llm.ainvoke(prompt)
    intent = resp.content.strip().lower().split()[0]
    return {"intent": intent, **_append_trace(state, f"intent={intent}")}

async def farmer_profile_node(state: State) -> State:
    profile = await get_farmer_profile(state["user_id"])
    return {"profile": profile, **_append_trace(state, "profile")}

async def sensor_data_node(state: State) -> State:
    sensors = await get_latest_sensor_data(state["user_id"])
    return {"sensors": sensors, **_append_trace(state, "sensors")}

async def weather_node(state: State) -> State:
    location = (state.get("profile") or {}).get("location", "Unknown")
    weather = await get_local_weather(location)
    return {"weather": weather, **_append_trace(state, "weather")}

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
        f"Crop: {crop}\n"
        f"Farmer context: {profile}\n"
        f"Sensor readings: {sensors}\n"
        "Output:\n"
        "- 3–5 bullet insights comparing readings vs ideal ranges (state the ideal when you flag a deviation)\n"
        "- One-line recommendation starting with 'Action:'"
    )
    resp = await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=user)])
    return {"crop_analysis": resp.content, **_append_trace(state, "crop_analysis")}

async def disease_prediction_node(state: State) -> State:
    crops = (state.get("profile") or {}).get("crops", [])
    crop = crops[0] if crops else "unknown crop"
    sensors = state.get("sensors", {})
    weather = state.get("weather", {})
    sys = "You are a plant pathologist. Estimate near-term disease risks from crop, sensors and weather."
    user = f"Crop: {crop}\nSensors: {sensors}\nWeather: {weather}\nOutput: risks (if any) and preventive actions. Keep it short."
    resp = await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=user)])
    return {"disease_risk": resp.content, **_append_trace(state, "disease_risk")}

async def lifecycle_planning_node(state: State) -> State:
    profile = state.get("profile", {})
    crops = profile.get("crops", [])
    crop = crops[0] if crops else "unknown crop"
    weather = state.get("weather", {})
    sys = "You prepare seasonal crop operation plans."
    user = f"Crop: {crop}\nLocation: {profile.get('location')}\nWeather summary: {weather}\nOutput: near-term 2-4 week plan (sow/fertilize/irrigate/spray/harvest cues)."
    resp = await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=user)])
    return {"plan": resp.content, **_append_trace(state, "plan")}

async def response_synthesizer_node(state: State) -> State:
    msg = state["message"]
    profile = state.get("profile", {})
    parts = {
        "Crop health": state.get("crop_analysis", ""),
        "Disease": state.get("disease_risk", ""),
        "Plan": state.get("plan", ""),
        "Weather": str(state.get("weather", "")),
        "Sensors": str(state.get("sensors", "")),
    }
    sys = "You are the farmer-facing assistant. Write a friendly, concise answer with bullets and a final action line."
    user = (
        f"User query: {msg}\n"
        f"Farmer profile: {profile}\n"
        f"Context parts: {parts}\n"
        "Respond in <= 180 words."
    )
    resp = await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=user)])
    return {"final_response": resp.content, **_append_trace(state, "final")}

# ------------ Build and run the graph ------------

def _build_graph():
    g = StateGraph(State)

    g.add_node("farmer_interaction", farmer_interaction_node)
    g.add_node("farmer_profile", farmer_profile_node)
    g.add_node("sensor_data", sensor_data_node)
    g.add_node("weather", weather_node)
    g.add_node("crop_health", crop_health_node)
    g.add_node("disease_prediction", disease_prediction_node)
    g.add_node("lifecycle_planning", lifecycle_planning_node)
    g.add_node("response", response_synthesizer_node)

    # Flow: interaction -> profile -> parallel (sensors, weather) -> analyses -> response
    g.set_entry_point("farmer_interaction")
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

async def run_langgraph_workflow(user_id: str, message: str) -> str:
    initial: State = {"user_id": user_id, "message": message, "trace": []}
    result: State = await _compiled_graph.ainvoke(initial)
    return result.get("final_response", "Sorry, something went wrong.")