from datetime import datetime, timedelta
from langchain_core.messages import SystemMessage
from app.graph.state import WeatherState
from app.llm import llm_tools

async def llm_node(state: WeatherState):
    """
    LLM reasoning node:
    1. Injects dynamic real-world date and 16-day forecast horizon into SystemMessage.
    2. Passes conversation history to the model.
    3. Model selects the specific granular weather tool or generates the final response.
    """
    messages = list(state.get('messages', []))
    
    # Compute real-world dynamic time anchors
    now_dt = datetime.now()
    today_date = now_dt.date()
    forecast_end_date = today_date + timedelta(days=16)
    
    now_str = now_dt.strftime("%A, %B %d, %Y at %I:%M %p")
    today_str = today_date.strftime("%Y-%m-%d")
    forecast_end_str = forecast_end_date.strftime("%Y-%m-%d")

    system_text = (
        f"You are a helpful, knowledgeable, and accurate AI Weather Assistant.\n\n"
        f"REAL-WORLD TEMPORAL CONTEXT:\n"
        f"- Current Real-World Date & Time: {now_str} (ISO: {today_str})\n"
        f"- Active 16-Day Forecast Horizon: {today_str} through {forecast_end_str}\n\n"
        f"GRANULAR TOOLS & SPECIFIC USAGE:\n"
        f"1. `get_current_weather(city)`: For live current conditions right now.\n"
        f"2. `get_weather_forecast(city, date)`: For a single upcoming date within the next 16 days (e.g. 'tomorrow', 'August 22').\n"
        f"3. `get_hourly_forecast(city, date, hour)`: For weather at an exact hour (e.g. 'tomorrow at 8 PM' -> hour=20, 'tonight at 11 PM' -> hour=23).\n"
        f"4. `get_weather_forecast_range(city, start_date, end_date)`: For multi-day forecast ranges (e.g. 'August 20 to August 25').\n"
        f"5. `get_historical_weather(city, date)`: For a single past date before {today_str} (e.g. 'yesterday', 'July 14, 2025').\n"
        f"6. `get_historical_weather_range(city, start_date, end_date)`: For past date ranges (e.g. 'between August 1 and August 5').\n\n"
        f"RULES & BEHAVIOR:\n"
        f"- ALWAYS call the most specific tool for the user's intent. Never invent weather data.\n"
        f"- Convert relative terms ('today', 'tomorrow', 'yesterday', 'next Friday') into exact YYYY-MM-DD dates using the temporal context.\n"
        f"- Retain the active city location across conversational turns when the user asks follow-up questions without naming the city.\n"
        f"- If a user asks for a date beyond the 16-day forecast horizon (> {forecast_end_str}), the tool will inform you of the boundary to explain to the user.\n"
        f"- Provide a clear, natural, and helpful response."
    )
    
    # Ensure system prompt is always refreshed at the start of messages
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=system_text)] + messages
    else:
        messages[0] = SystemMessage(content=system_text)

    response = await llm_tools.ainvoke(messages)
    return {"messages": [response]}


def should_continue(state: WeatherState) -> str:
    """Evaluate whether the LLM produced tool_calls or finished generating the final reply."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"