from crewai import Crew, Process
from typing import Dict, Any

from .agent_roles import (
    data_ingestion_agent,
    crop_health_agent,
    weather_agent,
    interaction_agent,
    define_tasks,
)

async def run_agent_crew(user_id: str, message: str) -> Dict[str, Any]:
    """
    Initializes and runs the multi-agent crew to answer the user's query.
    """
    print(f"User {user_id} message received: {message}")
    
    tasks = define_tasks(user_id, message)
    
    farmer_crew = Crew(
        agents=[
            data_ingestion_agent,
            crop_health_agent,
            weather_agent,
            interaction_agent,
        ],
        tasks=tasks,
        process=Process.sequential,
        verbose=2,
    )
    
    try:
        result = farmer_crew.kickoff(inputs={'user_message': message, 'user_id': user_id})
        return {"response": result}
    except Exception as e:
        print(f"An error occurred during crew kickoff: {e}")
        return {"response": "I'm sorry, an error occurred while processing your request. Please try again later."}