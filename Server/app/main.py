import os
import re
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.adk_runner import ask_adk_agent
from app.service.weather_service import WeatherService, WEATHER_CODE_NAMES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather_agent.api")

app = FastAPI(
    title="Intelligent Weather AI Assistant API (Google ADK)",
    description="Production-grade Google ADK Weather Agent with Granular Tool Routing and Multi-Turn Memory",
    version="2.0.0"
)

# Enable CORS for Angular Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Pydantic Request & Response Schemas
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    location: Optional[str] = None

class WeatherSnapshot(BaseModel):
    location: str
    temp: str
    condition: str
    humidity: str
    recommendation: Optional[str] = None

class WeatherLocation(BaseModel):
    name: str
    country: Optional[str] = ""
    latitude: float
    longitude: float

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    location: Optional[WeatherLocation] = None
    weather_snapshot: Optional[WeatherSnapshot] = None
    weather_recommendation: Optional[str] = None
    suggestions: Optional[List[str]] = None
    target_date: Optional[str] = None
    target_time: Optional[str] = None
    target_label: Optional[str] = None

# ---------------------------------------------------------
# Target Date & Time NLP Parser
# ---------------------------------------------------------
def parse_target_date_time(text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract target ISO date (YYYY-MM-DD), time (HH:MM), and user label from natural language."""
    now = datetime.now()
    today_date = now.date()
    lower_text = text.lower()
    
    target_date = None
    target_time = None
    target_label = None

    # 1. Relative date keywords
    if "day after tomorrow" in lower_text:
        dt = today_date + timedelta(days=2)
        target_date = dt.strftime("%Y-%m-%d")
        target_label = dt.strftime("%A, %b %d, %Y")
    elif "tomorrow" in lower_text:
        dt = today_date + timedelta(days=1)
        target_date = dt.strftime("%Y-%m-%d")
        target_label = dt.strftime("%A, %b %d, %Y")
    elif "yesterday" in lower_text:
        dt = today_date - timedelta(days=1)
        target_date = dt.strftime("%Y-%m-%d")
        target_label = dt.strftime("%A, %b %d, %Y")
    elif "in " in lower_text and " days" in lower_text:
        m = re.search(r'in\s+(\d+)\s+days?', lower_text)
        if m:
            days_count = int(m.group(1))
            dt = today_date + timedelta(days=days_count)
            target_date = dt.strftime("%Y-%m-%d")
            target_label = dt.strftime("%A, %b %d, %Y")

    # 2. ISO dates (YYYY-MM-DD)
    if not target_date:
        iso_m = re.search(r'\b(20\d{2})-(\d{2})-(\d{2})\b', text)
        if iso_m:
            target_date = iso_m.group(0)
            try:
                dt = datetime.strptime(target_date, "%Y-%m-%d")
                target_label = dt.strftime("%A, %b %d, %Y")
            except Exception:
                target_label = target_date

    # 3. Explicit month/day phrases (e.g. "20th august 2026", "august 22")
    if not target_date:
        date_pattern = r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)(?:\s+(20\d{2}))?\b'
        m = re.search(date_pattern, lower_text)
        if not m:
            date_pattern_rev = r'\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s+(20\d{2}))?\b'
            m_rev = re.search(date_pattern_rev, lower_text)
            if m_rev:
                day = int(m_rev.group(2))
                month_str = m_rev.group(1)[:3]
                year = int(m_rev.group(3)) if m_rev.group(3) else now.year
                try:
                    dt = datetime.strptime(f"{year}-{month_str}-{day}", "%Y-%b-%d")
                    target_date = dt.strftime("%Y-%m-%d")
                    target_label = dt.strftime("%A, %b %d, %Y")
                except Exception:
                    pass
        else:
            day = int(m.group(1))
            month_str = m.group(2)[:3]
            year = int(m.group(3)) if m.group(3) else now.year
            try:
                dt = datetime.strptime(f"{year}-{month_str}-{day}", "%Y-%b-%d")
                target_date = dt.strftime("%Y-%m-%d")
                target_label = dt.strftime("%A, %b %d, %Y")
            except Exception:
                pass

    # 4. Specific Hour expressions (e.g. "8 pm", "20:00", "11:30 am")
    time_12h = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b', lower_text)
    if time_12h:
        hr = int(time_12h.group(1))
        minute = int(time_12h.group(2)) if time_12h.group(2) else 0
        meridiem = time_12h.group(3)
        if meridiem == 'pm' and hr != 12:
            hr += 12
        elif meridiem == 'am' and hr == 12:
            hr = 0
        target_time = f"{hr:02d}:{minute:02d}"
        t_label = f"{time_12h.group(1)}{':' + f'{minute:02d}' if minute else ''} {meridiem.upper()}"
        target_label = f"{target_label} at {t_label}" if target_label else f"Today at {t_label}"
    else:
        time_24h = re.search(r'\b([01]?\d|2[0-3]):([0-5]\d)\b', text)
        if time_24h:
            target_time = f"{int(time_24h.group(1)):02d}:{time_24h.group(2)}"
            target_label = f"{target_label} at {target_time}" if target_label else f"Today at {target_time}"

    return target_date, target_time, target_label


# ---------------------------------------------------------
# Dynamic Weather Recommendation Generator
# ---------------------------------------------------------
def generate_recommendation(temp: float, condition: str, humidity: str) -> str:
    cond_lower = condition.lower()
    if "thunderstorm" in cond_lower:
        return "Thunderstorm active. Stay indoors if possible."
    elif "rain" in cond_lower or "drizzle" in cond_lower or "shower" in cond_lower:
        return "It's rainy. Don't forget your umbrella!"
    elif "snow" in cond_lower:
        return "Snowy conditions. Wear warm winter layers."
    elif temp >= 33:
        return "It's quite hot outside. Stay hydrated and use sunscreen."
    elif temp <= 10:
        return "Chilly weather. A warm jacket is recommended."
    return "Weather is pleasant. Enjoy your day!"


# ---------------------------------------------------------
# Chat Endpoint (Powered by Google ADK)
# ---------------------------------------------------------
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # Execute through Google ADK Runner
        adk_result = await ask_adk_agent(request.message, session_id=session_id)
        reply_text = adk_result["reply"]
        executed_tool_calls = adk_result["tool_calls"]

        # NLP Date/Time Parsing
        target_date, target_time, target_label = parse_target_date_time(request.message)

        # Inspect Tool Calls for Location & Time
        location_data = None
        weather_snapshot = None
        ws = WeatherService()

        for tc in reversed(executed_tool_calls):
            city = tc.get("args", {}).get("city")
            args = tc.get("args", {})
            if "date" in args:
                target_date = args["date"]
            elif "start_date" in args:
                target_date = args["start_date"]
            if "hour" in args:
                target_time = f"{int(args['hour']):02d}:00"

            if city:
                try:
                    loc_coords = ws.get_coordinates(city)
                    location_data = WeatherLocation(
                        name=loc_coords["name"],
                        country=loc_coords.get("country", ""),
                        latitude=loc_coords["latitude"],
                        longitude=loc_coords["longitude"]
                    )

                    today_str = datetime.now().strftime("%Y-%m-%d")
                    temp_val = 22.0
                    cond_name = "Partly Cloudy"
                    humidity_val = "60%"

                    # Target Date in Past
                    if target_date and target_date < today_str:
                        hist = ws.get_historical_weather(city, target_date)
                        temp_val = hist.get("temp_max_c") or 22.0
                        cond_name = hist.get("condition", "Partly Cloudy")
                    # Target Hour Today or Future
                    elif target_time:
                        hr_int = int(target_time[:2])
                        hr_date = target_date or today_str
                        hr_data = ws.get_hourly_forecast(city, hr_date, hr_int)
                        temp_val = hr_data.get("temperature_c") or 22.0
                        cond_name = hr_data.get("condition", "Partly Cloudy")
                        humidity_val = f"{hr_data.get('humidity_percent', 60)}%"
                    # Target Date Today or Future
                    elif target_date:
                        d_data = ws.get_daily_forecast(city, target_date)
                        temp_val = d_data.get("temp_max_c") or 22.0
                        cond_name = d_data.get("condition", "Partly Cloudy")
                    # Live Current Weather
                    else:
                        curr = ws.get_current_weather(city)
                        temp_val = curr.get("temperature_c") or 22.0
                        cond_name = curr.get("condition", "Partly Cloudy")
                        humidity_val = f"{curr.get('humidity_percent', 60)}%"

                    recom = generate_recommendation(temp_val, cond_name, humidity_val)
                    loc_display = f"{loc_coords['name']}, {loc_coords.get('country', '')}".strip(", ")
                    weather_snapshot = WeatherSnapshot(
                        location=loc_display,
                        temp=f"{round(temp_val)}°C",
                        condition=cond_name,
                        humidity=humidity_val,
                        recommendation=recom
                    )
                    break
                except Exception as e:
                    logger.warning(f"Failed to generate snapshot for {city}: {e}")
            if location_data:
                break

        return ChatResponse(
            reply=reply_text,
            session_id=session_id,
            location=location_data,
            weather_snapshot=weather_snapshot,
            weather_recommendation=weather_snapshot.recommendation if weather_snapshot else None,
            suggestions=["What's the forecast for tomorrow?", "Will it rain at 8 PM?", "Weather in Paris on 2025-07-14?"],
            target_date=target_date,
            target_time=target_time,
            target_label=target_label
        )

    except Exception as e:
        logger.error(f"Chat processing error in Google ADK: {e}", exc_info=True)
        return ChatResponse(
            reply="I'm having trouble retrieving weather data right now. Please try again in a moment.",
            session_id=session_id
        )

@app.get("/health")
def health():
    return {"status": "ok", "architecture": "Google ADK Weather Agent"}
