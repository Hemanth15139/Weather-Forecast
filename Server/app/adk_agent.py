import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.adk import Agent
from app.adk_tools import ALL_ADK_TOOLS

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if api_key:
    os.environ["GEMINI_API_KEY"] = api_key

def get_agent_instruction() -> str:
    """Generate dynamic system instructions anchored to current real-world date and 16-day horizon."""
    now_dt = datetime.now()
    today_date = now_dt.date()
    forecast_end_date = today_date + timedelta(days=16)

    now_str = now_dt.strftime("%A, %B %d, %Y at %I:%M %p")
    today_str = today_date.strftime("%Y-%m-%d")
    forecast_end_str = forecast_end_date.strftime("%Y-%m-%d")

    return (
        f"You are a helpful, knowledgeable, and accurate AI Weather Assistant built with Google ADK.\n\n"
        f"REAL-WORLD TEMPORAL CONTEXT:\n"
        f"- Current Real-World Date & Time: {now_str} (ISO: {today_str})\n"
        f"- Active 16-Day Forecast Horizon: {today_str} through {forecast_end_str}\n\n"
        f"GRANULAR TOOLS & SPECIFIC INTENTS:\n"
        f"1. `get_current_weather(city)`: For live current weather conditions right now.\n"
        f"2. `get_weather_forecast(city, date)`: For a single upcoming date within the next 16 days (e.g. 'tomorrow', 'August 22').\n"
        f"3. `get_hourly_forecast(city, date, hour)`: For weather at an exact hour on a date (e.g. 'tomorrow at 8 PM' -> hour=20, 'tonight at 11 PM' -> hour=23).\n"
        f"4. `get_weather_forecast_range(city, start_date, end_date)`: For multi-day forecast ranges (e.g. 'August 20 to August 25', 'weekend forecast').\n"
        f"5. `get_historical_weather(city, date)`: For a single past date before {today_str} (e.g. 'yesterday', 'July 14, 2025').\n"
        f"6. `get_historical_weather_range(city, start_date, end_date)`: For past date ranges (e.g. 'between August 1 and August 5').\n\n"
        f"RULES & BEHAVIOR:\n"
        f"- ALWAYS call the most specific tool for the user's intent. Never invent weather data.\n"
        f"- Convert relative terms ('today', 'tomorrow', 'yesterday', 'next Friday') into exact YYYY-MM-DD dates using the temporal context.\n"
        f"- Retain the active city location across conversational turns when the user asks follow-up questions without naming the city.\n"
        f"- If a user asks for a date beyond the 16-day forecast horizon (> {forecast_end_str}), explain the 16-day limit politely.\n"
        f"- Provide a clear, natural, and helpful response."
    )

def create_adk_agent(model_name: str = "gemini-3.5-flash-lite") -> Agent:
    """Factory creating a Google ADK Agent for a specific model."""
    return Agent(
        name=f"weather_assistant_{model_name.replace('-', '_').replace('.', '_')}",
        model=model_name,
        description="Intelligent weather agent.",
        instruction=get_agent_instruction(),
        tools=ALL_ADK_TOOLS
    )

# Primary Agent
weather_agent = create_adk_agent(os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"))
