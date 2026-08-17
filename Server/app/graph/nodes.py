from datetime import datetime, timedelta
from langchain_core.messages import SystemMessage
from app.graph.state import WeatherState
from app.llm import llm_tools

async def llm_node(state: WeatherState):
    messages = list(state.get('messages', []))
    
    # Dynamically compute real-world time and forecast boundaries
    now_dt = datetime.now()
    today_date = now_dt.date()
    forecast_end_date = today_date + timedelta(days=14)
    
    now_str = now_dt.strftime("%A, %B %d, %Y at %I:%M %p")
    today_str = today_date.strftime("%Y-%m-%d")
    forecast_end_str = forecast_end_date.strftime("%Y-%m-%d")

    system_text = (
        f"You are a helpful, knowledgeable, and accurate AI Weather Assistant.\n\n"
        f"TIME & HORIZON CONTEXT:\n"
        f"- Current Real-World Date & Time: {now_str} (ISO: {today_str})\n"
        f"- Active 14-Day Forecast Window: {today_str} through {forecast_end_str}\n\n"
        f"AVAILABLE TOOLS:\n"
        f"1. `get_weather(city)`:\n"
        f"   - Retrieves real-time current conditions, hourly timeline (for today and upcoming days), and a 14-day daily forecast (covering {today_str} to {forecast_end_str}).\n"
        f"   - Use for: current weather, specific hours today/tomorrow/this week (e.g. 'at 11 pm', 'tonight', 'tomorrow morning'), and any upcoming date within the 14-day window.\n"
        f"2. `get_historical_weather(city, date, end_date=None)`:\n"
        f"   - Retrieves past weather records for any date prior to {today_str} (format: YYYY-MM-DD).\n"
        f"   - Use for: past dates (e.g. 'yesterday', 'last month', 'July 4 2024', any past year/day).\n\n"
        f"RULES & BEHAVIOR:\n"
        f"- ALWAYS call the appropriate weather tool before answering. Never invent weather data.\n"
        f"- If the requested date falls between {today_str} and {forecast_end_str}, call `get_weather(city)` and extract the forecast for that specific day or hour.\n"
        f"- If the requested date is before {today_str}, call `get_historical_weather(city, date)`.\n"
        f"- If the user specifies a time or date without naming a city, maintain the active location from the conversation context.\n"
        f"- Provide a clear, natural, and helpful response with temperature, feels-like, sky condition, and precipitation/rain chance."
    )
    
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=system_text)] + messages
    else:
        messages[0] = SystemMessage(content=system_text)

    response = await llm_tools.ainvoke(messages)

    return {
        "messages": [response]
    }


def should_continue(state: WeatherState):

    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return "end"