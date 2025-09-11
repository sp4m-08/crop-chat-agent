### Project Structure

crop-chatbot-backend/
├── fastapi_app/
│ ├── **init**.py
│ ├── agents/
│ │ ├── **init**.py
│ │ ├── agent_roles.py
│ │ └── orchestrator.py
│ ├── models/
│ │ ├── **init**.py
│ │ └── sensor_data.py
│ ├── routes/
│ │ ├── **init**.py
│ │ └── chat.py
│ └── main.py
├── requirements.txt
└── venv/

---

### Project Documentation: The LLM Multi-Agent Crop/Farmer Chatbot

This document provides a comprehensive overview of the `Crop-Chatbot` project, a multi-agent system designed to assist farmers by analyzing sensor data and providing actionable agricultural advice.

This project is built using a **FastAPI** backend that hosts a team of specialized AI agents. This backend is designed to be a service layer, meaning it can be called by any client, such as a web application, a mobile app, or a separate Express.js server.

---

### 1. The Multi-Agent Architecture

The core intelligence of this project is a **multi-agent system** powered by the **CrewAI** framework. This system operates as a team of experts, each with a specific role and access to unique tools. Instead of a single LLM trying to solve everything, the task is broken down and delegated to the most suitable agent, leading to more accurate and reliable responses.

Here's how the team works:

- **Farmer Interaction Agent**: This is the "manager" of the crew. Its primary job is to communicate with the farmer in a friendly, conversational tone. It receives the farmer's queries and, based on the complexity, delegates sub-tasks to the other agents. It then synthesizes all the information from the team into a single, comprehensive response.

- **Sensor Data Ingestion Agent**: This is the data expert. Its sole responsibility is to fetch the latest sensor readings (temperature, humidity, soil moisture, etc.). It uses a specialized **tool** to retrieve this data and provides the raw information to the other agents.

- **Crop Health Analyst**: This agent is the agronomist. Its role is to analyze the raw sensor data provided by the Data Ingestion Agent and compare it to the ideal growing conditions for a specific crop. It uses a **tool** to access a knowledge base of agricultural requirements and identifies any potential issues.

- **Weather Forecaster**: This agent is the meteorologist. It uses a **tool** to get the current weather and a short-term forecast for the farm's location. This information is crucial for providing contextual advice, such as suggesting irrigation or harvest plans.

---

### 2. The File Structure and Its Purpose

The project is organized into a modular structure to ensure maintainability and scalability. Each file and directory has a clear purpose.

- **`fastapi_app/`**: This is the root of your Python application.
- **`main.py`**: The application's entry point. It creates the FastAPI instance and includes the API routes, acting as the central hub of your backend.
- **`routes/`**: This directory contains all of your API endpoints.
  - `chat.py`: Defines the `/chat` endpoint. This is the only endpoint exposed to your Express.js front end. It receives chat messages, triggers the agent crew, and returns the response.
- **`models/`**: This is where you define **Pydantic** models.
  - `sensor_data.py`: A Pydantic model for validating the structure of incoming sensor data.
- **`agents/`**: This is the heart of your multi-agent system.
  - `agent_roles.py`: Defines each of the specialized agents, their goals, backstories, and the **tools** they can use. This is where you will add your code to connect to real data sources like AWS IoT.
  - `orchestrator.py`: Orchestrates the communication and collaboration between the agents. It defines the sequence of tasks and kicks off the entire process.
- **`requirements.txt`**: A simple text file that lists all the necessary Python libraries for your project.
- **`venv/`**: The Python virtual environment. It isolates your project's dependencies from other projects on your computer.

---

### 3. Key Concepts Explained

- **FastAPI**: A modern, high-performance web framework for building APIs with Python. It's a perfect choice for the backend because it's fast, easy to use, and comes with automatic interactive API documentation.
- **CrewAI**: The framework for building and running your multi-agent system. It allows you to create a "crew" of agents and have them work together to solve complex problems.
- **Pydantic**: A library for data validation. In your project, it ensures that data sent to and received from your agents and API endpoints has a consistent structure.
- **LLM (Gemini API)**: The large language model is the "brain" for each of your agents. The CrewAI framework uses the LLM to power the agents' reasoning and decision-making abilities. You pass your Gemini API key to CrewAI, which handles all communication with the LLM.
- **Tools**: These are specialized functions or APIs that an agent can call. They are what ground the LLM in real-world data and actions. For example, your `get_latest_sensor_data` tool connects the LLM to your hardware sensors via AWS.
