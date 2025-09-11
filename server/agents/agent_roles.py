import os
from crewai import Agent, Task, Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

# Initialize the LLM with your API key from environment variables
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    verbose=True,
)

# =========================================================================
# 1. Pydantic Models for Data Validation
# =========================================================================

class SensorData(BaseModel):
    temperature: float
    humidity: float
    soil_moisture: int
    gas_level: int
    timestamp: str

# =========================================================================
# 2. Tools (using mocked data for demonstration)
# =========================================================================

class SensorTools:
    """Tools for interacting with sensor data."""
    @Tool
    def get_latest_sensor_data(self) -> str:
        """
        Fetches the latest sensor data from the AWS IoT Core.
        Returns a JSON string of the most recent sensor readings.
        """
        data = {
            "temperature": 28.5,
            "humidity": 65.0,
            "soil_moisture": 450,
            "gas_level": 150,
            "timestamp": "2025-09-06T12:00:00Z"
        }
        return str(data)

class KnowledgeBaseTools:
    """Tools for accessing a knowledge base of agricultural information."""
    @Tool
    def get_crop_requirements(self, crop_name: str) -> str:
        """
        Looks up the ideal growing conditions for a specific crop.
        Returns a detailed string of ideal temperature, humidity, and soil moisture ranges.
        """
        if "corn" in crop_name.lower():
            return "Ideal conditions for corn: Temperature: 21-27°C, Humidity: 60-80%, Soil Moisture: 300-600. Requires full sun."
        elif "wheat" in crop_name.lower():
            return "Ideal conditions for wheat: Temperature: 10-25°C, Humidity: 50-70%, Soil Moisture: 400-700. Tolerates cooler temperatures."
        else:
            return "No specific data found for this crop. Please provide a common crop name like 'corn' or 'wheat'."

class WeatherTools:
    """Tools for fetching real-time weather information."""
    @Tool
    def get_local_weather(self, location: str) -> str:
        """
        Fetches the current weather conditions for a given location.
        Returns a string with details like temperature, rainfall, and forecast.
        """
        return "Current local weather: Temperature is 29°C with 75% humidity. No rain expected for the next 48 hours."

# =========================================================================
# 3. Agents
# =========================================================================

interaction_agent = Agent(
    llm=llm,
    role="Farmer Interaction Agent",
    goal="Synthesize information from other agents and provide a helpful, conversational, and actionable response to the farmer's query.",
    backstory=(
        "You are the primary interface for the farmer. Your expertise lies in translating technical data and "
        "agricultural insights into clear, friendly advice. You coordinate with other agents to "
        "gather the necessary information before formulating your response."
    ),
    verbose=True,
    allow_delegation=True,
)

data_ingestion_agent = Agent(
    llm=llm,
    role="Sensor Data Ingestion Agent",
    goal="Fetch the latest sensor readings from the hardware and format the data for analysis.",
    backstory=(
        "You are the data expert. Your sole purpose is to retrieve the most up-to-date "
        "readings from the soil moisture, temperature, humidity, and gas sensors. "
        "You do not analyze the data yourself, but you provide it accurately to other agents."
    ),
    verbose=True,
    tools=[SensorTools().get_latest_sensor_data],
)

crop_health_agent = Agent(
    llm=llm,
    role="Crop Health Analyst",
    goal="Analyze sensor data in the context of specific crop requirements to identify potential issues.",
    backstory=(
        "You are a seasoned agronomist. You use your deep knowledge of plants to compare "
        "current environmental conditions against the ideal conditions for a given crop. "
        "You identify problems and suggest potential solutions."
    ),
    verbose=True,
    tools=[KnowledgeBaseTools().get_crop_requirements],
)

weather_agent = Agent(
    llm=llm,
    role="Weather Forecaster",
    goal="Provide accurate, short-term weather forecasts relevant to the farm's location.",
    backstory=(
        "You are a weather specialist. Your job is to fetch and report on the current and "
        "upcoming weather conditions, including rainfall, temperature, and humidity, to help "
        "the farmer plan their daily tasks."
    ),
    verbose=True,
    tools=[WeatherTools().get_local_weather],
)

def define_tasks(user_id: str, user_message: str):
    """
    Defines the list of tasks for the agent crew based on the user's query.
    """
    fetch_data_task = Task(
        description=(
            "Fetch the latest sensor data from the AWS IoT Core. Do not analyze, just provide the raw data."
        ),
        expected_output="A JSON string containing the latest temperature, humidity, soil moisture, and gas level readings.",
        agent=data_ingestion_agent,
    )

    analyze_crop_task = Task(
        description=(
            f"Analyze the following user query: '{user_message}'. "
            "Use the provided sensor data to compare against ideal crop conditions. "
            "Identify any potential issues related to temperature, humidity, or soil moisture."
        ),
        expected_output="A summary of the crop's health based on sensor data, highlighting any issues and their likely causes.",
        agent=crop_health_agent,
        context=[fetch_data_task],
    )

    get_weather_task = Task(
        description=(
            "Fetch the current and forecasted weather for the farm location. Use the 'get_local_weather' tool."
        ),
        expected_output="A brief summary of the current weather and a short-term forecast.",
        agent=weather_agent,
    )

    synthesize_response_task = Task(
        description=(
            f"Given the user's query: '{user_message}', and the analysis from the other agents, "
            "synthesize a final, comprehensive, and friendly response. "
            "The response should be conversational, easy to understand, and provide actionable advice. "
            "Do not return a JSON object, but a plain text string."
        ),
        expected_output="A well-structured, conversational response for the farmer.",
        agent=interaction_agent,
        context=[analyze_crop_task, get_weather_task],
    )

    return [fetch_data_task, analyze_crop_task, get_weather_task, synthesize_response_task]