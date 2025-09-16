from __future__ import annotations
from typing import TypedDict, Optional, Dict, Any, List, Annotated
import operator
import re
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from ..utils.response_cleaner import clean_response, format_weather, format_market_price
from .agent_roles import llm
from .tools.profile_tool import get_farmer_profile
from .tools.sensor_tool import get_latest_sensor_data
from .tools.weather_tool import get_local_weather
from .tools.history_tool import get_chat_history, save_chat_turn, render_history_for_prompt
from .tools.market_tool import get_agri_market_price

# ------------ Shared state passed between nodes ------------
class State(TypedDict, total=False):
    user_id: str
    session_id: str
    message: str
    intent: List[str]
    query_crop: Optional[str]
    history: List[Dict[str, Any]]
    history_summary: str
    profile: Dict[str, Any]
    sensors: Dict[str, Any]
    weather: Dict[str, Any]
    crop_analysis: str
    disease_risk: str
    plan: str
    market_price: Dict[str, Any]
    final_response: str
    trace: Annotated[List[str], operator.add]

def _trace(note: str) -> Dict[str, Any]:
    return {"trace": [note]}

# ------------ Nodes (agents) ------------
async def chat_history_node(state: State) -> State:
    history = await get_chat_history(state["user_id"], state["session_id"], limit=20)
    history_text = render_history_for_prompt(history)
    sys = "Summarize this farmer-assistant chat briefly. Keep goals, crops, and unresolved items. <= 120 words."
    user = history_text or "No prior messages."
    summary = (await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=user)])).content
    return {
        "history": history,
        "history_summary": summary,
        **_trace("history_loaded")
    }

async def farmer_interaction_node(state: State) -> State:
    # Detect intents
    prompt = [
        SystemMessage(content="You triage farmer queries. Output all relevant intents separated by commas: status, weather, disease, plan, advice, market, price."),
        HumanMessage(content=f"User message: {state['message']}"),
    ]
    resp = await llm.ainvoke(prompt)
    intents = [i.strip() for i in resp.content.lower().split(",") if i.strip()]

    # Try to extract crop from user query
    crop_prompt = [
        SystemMessage(content="Extract the crop name from the following user message. If none, reply 'none'."),
        HumanMessage(content=state["message"])
    ]
    crop_resp = await llm.ainvoke(crop_prompt)
    crop_query = crop_resp.content.strip().lower()
    crop_query = None if crop_query == "none" else crop_query

    return {"intent": intents, "query_crop": crop_query, **_trace(f"intent={intents}, crop={crop_query}")}

async def farmer_profile_node(state: State) -> State:
    profile = await get_farmer_profile(state["user_id"])
    return {"profile": profile, **_trace("profile")}

async def sensor_data_node(state: State) -> State:
    sensors = await get_latest_sensor_data(state["user_id"])
    return {"sensors": sensors, **_trace("sensors")}

async def weather_node(state: State) -> State:
    """
    Gets location from user query if present, else uses profile location.
    """
    profile = state.get("profile", {})
    # Try to extract location from user query using LLM
    location_prompt = [
       SystemMessage(content="Extract the city name from the following user message. If the user asks about a city other than the registered location, reply with that city name. If none, reply 'none'."),
        HumanMessage(content=state["message"])
    ]
    location_resp = await llm.ainvoke(location_prompt)
    location_query = location_resp.content.strip()
    location = location_query if location_query.lower() != "none" else profile.get("location", "")

    weather = await get_local_weather(location)
    return {"weather": weather, **_trace(f"weather for {location}")}

async def crop_health_node(state: State) -> State:
    profile = state.get("profile", {})
    crops = profile.get("crops", [])
    crop = state.get("query_crop") or (crops[0] if crops else "unknown crop")
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
    return {"crop_analysis": resp.content, **_trace("crop_analysis")}

async def disease_prediction_node(state: State) -> State:
    profile = state.get("profile", {})
    crops = profile.get("crops", [])
    crop = state.get("query_crop") or (crops[0] if crops else "unknown crop")
    sensors = state.get("sensors", {})
    weather = state.get("weather", {})
    sys = "Plant pathologist. Estimate near-term disease risks and preventive actions."
    user = (
        f"Recent chat summary: {state.get('history_summary','')}\n"
        f"Crop: {crop}\nSensors: {sensors}\nWeather: {weather}"
    )
    resp = await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=user)])
    return {"disease_risk": resp.content, **_trace("disease_risk")}

async def agmarket_price_node(state: State) -> State:
    """
    Node to extract state and market for agri market price lookup.
    Uses location from user query if present, else profile location.
    Uses crop from user query if present, else profile crop.
    """
    profile = state.get("profile", {})
    # Try to extract location from user query using LLM
    location_prompt = [
        SystemMessage(content="Extract the location (city or market and state) from the following user message. If none, reply 'none'."),
        HumanMessage(content=state["message"])
    ]
    location_resp = await llm.ainvoke(location_prompt)
    location_query = location_resp.content.strip()
    location = location_query if location_query.lower() != "none" else profile.get("location", "")

    crop = state.get("query_crop") or profile.get("crops", ["wheat"])[0]

    # Prompt LLM to extract state and market from location string only
    sys = (
        "Extract the market and state from the following location string. "
        "Reply in the format: Market: <market>, State: <state>"
    )
    user = f"Location: {location}"
    resp = await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=user)])

    # Parse response for market and state
    match = re.search(r"Market:\s*([^\n,]+).*State:\s*([^\n,]+)", resp.content)
    if match:
        market_name, state_name = match.groups()
    else:
        market_name, state_name = "chennai", "Tamil nadu"  # fallback

    price_data = await get_agri_market_price(crop, state_name.strip(), market_name.strip())
    return {"market_price": price_data, **_trace(f"market_price for {crop} at {market_name}, {state_name}")}


async def lifecycle_planning_node(state: State) -> State:
    profile = state.get("profile", {})
    crops = profile.get("crops", [])
    crop = state.get("query_crop") or (crops[0] if crops else "unknown crop")
    weather = state.get("weather", {})
    sys = "You prepare seasonal crop operation plans."
    user = (
        f"Crop: {crop}\n"
        f"Location: {profile.get('location')}\n"
        f"Weather summary: {weather}\n"
        "Output: near-term 2-4 week plan (sow/fertilize/irrigate/spray/harvest cues)."
    )
    resp = await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=user)])
    return {"plan": resp.content, **_trace("plan")}

async def response_synthesizer_node(state: State) -> State:
    """
    Synthesizes the final response for the farmer based on detected intents and context parts.
    Includes market price, weather, crop health, disease, and plan as relevant.
    """
    msg = state["message"]
    intent = state.get("intent", [])
    profile = state.get("profile", {})
    market_price_info = format_market_price(state.get("market_price", {}))
    weather_info = format_weather(state.get("weather", {}))
    crop_health_info = state.get("crop_analysis", "")
    disease_info = state.get("disease_risk", "")
    plan_info = state.get("plan", "")

    # Build context parts based on detected intents
    parts = {}
    if any(i in intent for i in ["market", "price"]):
        parts["Market price"] = market_price_info
    if any(i in intent for i in ["weather", "rain"]):
        parts["Weather"] = weather_info
    if any(i in intent for i in ["health", "status"]):
        parts["Crop health"] = crop_health_info
    if "disease" in intent:
        parts["Disease"] = disease_info
    if "plan" in intent:
        parts["Plan"] = plan_info

    # System prompt to guide the LLM
    sys = (
        "Farmer-facing assistant. Reply concisely and only about the user's query. "
        "If the user asks about market price, do not include crop health alerts. "
        "If the user asks about weather or rain, use the provided weather data and forecast. "
        "If multiple topics are asked, answer each clearly."
    )
    user = (
        f"User query: {msg}\n"
        f"Farmer profile: {profile}\n"
        f"Context parts: {parts}\n"
        "<= 180 words."
    )

    resp = await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=user)])
    final = resp.content
    final_cleaned = clean_response(final)
    await save_chat_turn(state["user_id"], state["session_id"], msg, final_cleaned)
    return {"final_response": final_cleaned, **_trace("final")}

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
    g.add_node("agmarket_price", agmarket_price_node)

    g.set_entry_point("chat_history")
    g.add_edge("chat_history", "farmer_interaction")
    g.add_edge("farmer_interaction", "farmer_profile")
    g.add_edge("farmer_profile", "sensor_data")
    g.add_edge("farmer_profile", "agmarket_price")
    g.add_edge("agmarket_price", "sensor_data")
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
    try:
        result: State = await _compiled_graph.ainvoke(initial)
        print("Trace:", result.get("trace"))
        return result.get("final_response", "Sorry, something went wrong.")
    except Exception as e:
        print("Graph execution failed:", e)
        return f"Error: {e}"