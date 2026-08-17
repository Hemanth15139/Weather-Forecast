import sys
import os

# Adjust sys.path to allow importing 'app' as a package
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir in sys.path:
    sys.path.remove(current_dir)
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

from app.graph.workflow import workflow

app = FastAPI(title="Weather Forecast API")

# Add CORS Middleware to allow cross-origin requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CurrentWeather(BaseModel):
    temp: Optional[float] = None
    condition: Optional[str] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None

class ChatHistoryItem(BaseModel):
    role: str
    content: str

import uuid

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    location: Optional[str] = None
    current_weather: Optional[CurrentWeather] = None
    chat_history: Optional[List[ChatHistoryItem]] = None

class WeatherSnapshot(BaseModel):
    location: str
    temp: str
    condition: str
    humidity: str
    recommendation: Optional[str] = None

class WeatherLocation(BaseModel):
    name: str
    country: Optional[str] = None
    latitude: float
    longitude: float

import re
from datetime import datetime, timedelta

def parse_target_date_time(text: str, current_dt: datetime = None):
    if not current_dt:
        current_dt = datetime.now()
    today = current_dt.date()
    text_lower = text.lower()
    
    target_date = None
    target_time = None
    target_label = None

    # Check relative days
    if "day after tomorrow" in text_lower:
        dt = today + timedelta(days=2)
        target_date = dt.strftime("%Y-%m-%d")
        target_label = dt.strftime("%A, %b %d, %Y")
    elif "tomorrow" in text_lower:
        dt = today + timedelta(days=1)
        target_date = dt.strftime("%Y-%m-%d")
        target_label = dt.strftime("%A, %b %d, %Y")
    elif "yesterday" in text_lower:
        dt = today - timedelta(days=1)
        target_date = dt.strftime("%Y-%m-%d")
        target_label = dt.strftime("%A, %b %d, %Y")
    else:
        # Check 'in X days'
        m_in_days = re.search(r"in\s+(\d+)\s+days?", text_lower)
        if m_in_days:
            days = int(m_in_days.group(1))
            dt = today + timedelta(days=days)
            target_date = dt.strftime("%Y-%m-%d")
            target_label = dt.strftime("%A, %b %d, %Y")
        else:
            # Check ISO date YYYY-MM-DD
            m_iso = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
            if m_iso:
                y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
                try:
                    dt = datetime(y, m, d).date()
                    target_date = dt.strftime("%Y-%m-%d")
                    target_label = dt.strftime("%A, %b %d, %Y")
                except Exception:
                    pass
            else:
                months = {
                    'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
                    'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
                    'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
                    'november': 11, 'nov': 11, 'december': 12, 'dec': 12
                }
                for m_name, m_num in sorted(months.items(), key=lambda x: -len(x[0])):
                    pat = rf"(?:(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?)?\b{m_name}\b(?:\s+(\d{{1,2}})(?:st|nd|rd|th)?)?(?:\s+(\d{{4}}))?"
                    m = re.search(pat, text_lower)
                    if m:
                        d1, d2, y_str = m.group(1), m.group(2), m.group(3)
                        day = int(d1) if d1 else (int(d2) if d2 else None)
                        if day:
                            year = int(y_str) if y_str else current_dt.year
                            try:
                                dt = datetime(year, m_num, day).date()
                                target_date = dt.strftime("%Y-%m-%d")
                                target_label = dt.strftime("%A, %b %d, %Y")
                                break
                            except Exception:
                                pass

    # Check time: e.g. 11 pm, 11:30 am, 23:00, 5pm
    m_time = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", text_lower)
    if m_time:
        hr = int(m_time.group(1))
        mn = int(m_time.group(2)) if m_time.group(2) else 0
        ampm = m_time.group(3)
        hr_24 = hr
        if ampm == "pm" and hr < 12: hr_24 += 12
        if ampm == "am" and hr == 12: hr_24 = 0
        target_time = f"{hr_24:02d}:{mn:02d}"
        time_label = f"{hr}:{mn:02d} {ampm.upper()}" if m_time.group(2) else f"{hr} {ampm.upper()}"
        if not target_date:
            target_date = today.strftime("%Y-%m-%d")
            target_label = f"Today at {time_label}"
        else:
            target_label = f"{target_label} at {time_label}"
    else:
        m_24h = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text)
        if m_24h:
            target_time = f"{int(m_24h.group(1)):02d}:{int(m_24h.group(2)):02d}"
            if not target_date:
                target_date = today.strftime("%Y-%m-%d")
                target_label = f"Today at {target_time}"
            else:
                target_label = f"{target_label} at {target_time}"

    return target_date, target_time, target_label

class ChatResponse(BaseModel):
    reply: str
    session_id: Optional[str] = None
    target_date: Optional[str] = None
    target_time: Optional[str] = None
    target_label: Optional[str] = None
    suggestions: Optional[List[str]] = None
    weather_recommendation: Optional[str] = None
    weather_snapshot: Optional[WeatherSnapshot] = None
    location: Optional[WeatherLocation] = None

@app.get("/")
def read_root():
    return {"status": "running", "message": "Weather Forecast API is active"}

@app.get("/chat", response_class=HTMLResponse)
@app.get("/api/chat", response_class=HTMLResponse)
def get_chat_ui():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Weather Agent Chat Test</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #121214; color: #e1e1e6; max-width: 600px; margin: 40px auto; padding: 20px; }
            h1 { color: #61afef; text-align: center; }
            #chat-container { background: #1e1e24; border-radius: 8px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
            #messages { height: 300px; overflow-y: auto; border: 1px solid #2e2e38; border-radius: 4px; padding: 10px; margin-bottom: 20px; background: #151518; }
            .message { margin-bottom: 12px; line-height: 1.4; }
            .user { color: #98c379; }
            .assistant { color: #61afef; }
            #input-area { display: flex; gap: 10px; }
            input { flex: 1; padding: 10px; border-radius: 4px; border: 1px solid #2e2e38; background: #202024; color: #fff; }
            button { padding: 10px 20px; border: none; border-radius: 4px; background: #61afef; color: #1e1e24; font-weight: bold; cursor: pointer; }
            button:hover { background: #529ade; }
        </style>
    </head>
    <body>
        <h1>Weather Agent Chat Test</h1>
        <div id="chat-container">
            <div id="messages">
                <div class="message assistant"><b>Assistant:</b> Ask me about the weather in any city around the globe!</div>
            </div>
            <div id="input-area">
                <input type="text" id="query" placeholder="What is the weather in Hyderabad?" onkeydown="if(event.key === 'Enter') sendMessage()">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
        <script>
            let currentSessionId = null;
            async function sendMessage() {
                const input = document.getElementById('query');
                const text = input.value.trim();
                if (!text) return;
                
                const messagesDiv = document.getElementById('messages');
                messagesDiv.innerHTML += `<div class="message user"><b>You:</b> ${text}</div>`;
                input.value = '';
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                
                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: text, session_id: currentSessionId })
                    });
                    const data = await response.json();
                    if (data.session_id) currentSessionId = data.session_id;
                    messagesDiv.innerHTML += `<div class="message assistant"><b>Assistant:</b> ${data.reply}</div>`;
                } catch (err) {
                    messagesDiv.innerHTML += `<div class="message assistant" style="color: #e06c75;"><b>Error:</b> Failed to connect to server.</div>`;
                }
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

def get_condition_name(code: int) -> str:
    if code == 0: return 'Clear Sky'
    if 1 <= code <= 3: return 'Partly Cloudy'
    if code in (45, 48): return 'Foggy'
    if 51 <= code <= 67: return 'Light Rain'
    if 71 <= code <= 77: return 'Snowfall'
    if 80 <= code <= 82: return 'Rain Showers'
    if code >= 95: return 'Thunderstorm'
    return 'Overcast'

def get_recommendation(condition: str, temp: float) -> str:
    cond = condition.lower()
    if 'rain' in cond or 'shower' in cond or 'drizzle' in cond:
        return "It's rainy. Don't forget your umbrella!"
    if 'storm' in cond or 'thunder' in cond:
        return "Thunderstorm active. Stay indoors if possible."
    if temp > 30:
        return "It's quite hot. Stay hydrated and wear light clothes."
    if temp < 15:
        return "It's chilly. Wear a warm jacket."
    return "Weather is pleasant. Enjoy your day!"

@app.post("/api/chat", response_model=ChatResponse)
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    try:
        # Check existing state in checkpointer
        existing_state = workflow.get_state(config)
        
        # Build input messages
        input_messages = []
        now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        default_loc = request.location or "Hyderabad"

        # If new session, inject system context
        if not existing_state or not existing_state.values:
            system_prompt = (
                f"You are a helpful and accurate weather assistant. "
                f"Today's date and time is {now_str}. "
                f"The user's active dashboard location is '{default_loc}'. "
                f"When the user asks for the weather (including future forecasts, past/historical weather, or specific times like '11 pm', 'tomorrow', 'next Friday', 'yesterday', or past dates) "
                f"without specifying a city, use their active location '{default_loc}'. "
                f"You have access to two tools: "
                f"1. `get_weather(city)`: for real-time current weather, 14-day daily forecast (past 7 days to next 14 days), and detailed hourly timeline. "
                f"2. `get_historical_weather(city, date, end_date)`: for past/historical records on any specific date in history (e.g. YYYY-MM-DD)."
            )
            input_messages.append(SystemMessage(content=system_prompt))
            if request.chat_history:
                for item in request.chat_history:
                    if item.role == "user":
                        input_messages.append(HumanMessage(content=item.content))
                    elif item.role in ("assistant", "ai"):
                        input_messages.append(AIMessage(content=item.content))
                    elif item.role == "system":
                        input_messages.append(SystemMessage(content=item.content))
        
        # Append current user prompt
        input_messages.append(HumanMessage(content=request.message))
        
        # Invoke workflow asynchronously with thread_id session tracking
        result = await workflow.ainvoke({"messages": input_messages}, config=config)
        
        # Extract reply content
        last_message = result["messages"][-1]
        reply_text = ""
        if isinstance(last_message.content, str):
            reply_text = last_message.content
        elif isinstance(last_message.content, list):
            for part in last_message.content:
                if isinstance(part, dict) and part.get("type") == "text":
                    reply_text += part.get("text", "")
                elif isinstance(part, str):
                    reply_text += part
        else:
            reply_text = str(last_message.content)
            
        # Extract target date & target time if mentioned
        target_date, target_time, target_label = parse_target_date_time(request.message)

        # Inspect if weather tools were called in the conversation turn
        weather_snapshot = None
        location_data = None
        for msg in reversed(result.get("messages", [])):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_name = tc.get("name")
                    if tool_name in ("get_weather", "get_historical_weather"):
                        city = tc.get("args", {}).get("city")
                        # If tool call had specific historical date, prioritize it
                        if tool_name == "get_historical_weather":
                            hist_date = tc.get("args", {}).get("date")
                            if hist_date:
                                target_date = hist_date
                                try:
                                    dt_obj = datetime.strptime(hist_date, "%Y-%m-%d")
                                    target_label = dt_obj.strftime("%A, %b %d, %Y")
                                except Exception:
                                    target_label = hist_date

                        if city:
                            try:
                                from app.service.weather_service import WeatherService
                                ws = WeatherService()
                                loc_coords = ws.get_coordinates(city)
                                location_data = WeatherLocation(
                                    name=loc_coords["name"],
                                    country=loc_coords.get("country", ""),
                                    latitude=loc_coords["latitude"],
                                    longitude=loc_coords["longitude"]
                                )

                                today_str = datetime.now().strftime("%Y-%m-%d")
                                temp_val = 22
                                cond_name = "Partly Cloudy"
                                humidity_val = "60%"

                                # Case 1: Target date is in past (< today)
                                if target_date and target_date < today_str:
                                    hist_data = ws.get_historical_weather(city, target_date)
                                    daily = hist_data.get("daily", {})
                                    hourly = hist_data.get("hourly", {})
                                    if daily.get("temperature_2m_max"):
                                        temp_val = daily["temperature_2m_max"][0]
                                        cond_name = get_condition_name(daily.get("weather_code", [0])[0])
                                    if hourly.get("relative_humidity_2m"):
                                        humidity_val = f"{hourly['relative_humidity_2m'][0]}%"

                                # Case 2: Target date is today or in future
                                elif target_date or target_time:
                                    weather = ws.get_weather(city)
                                    daily = weather.get("daily", {})
                                    hourly = weather.get("hourly", {})
                                    
                                    # If specific time requested today or target date
                                    if target_time:
                                        t_times = hourly.get("time", [])
                                        t_temps = hourly.get("temperature_2m", [])
                                        t_codes = hourly.get("weather_code", [])
                                        t_humids = hourly.get("relative_humidity_2m", [])
                                        search_prefix = f"{target_date}T{target_time[:2]}" if target_date else f"T{target_time[:2]}"
                                        matched_idx = None
                                        for idx, t_str in enumerate(t_times):
                                            if target_date:
                                                if t_str.startswith(f"{target_date}T{target_time[:2]}"):
                                                    matched_idx = idx
                                                    break
                                            else:
                                                if f"T{target_time[:2]}" in t_str:
                                                    matched_idx = idx
                                                    break
                                        if matched_idx is not None and matched_idx < len(t_temps):
                                            temp_val = t_temps[matched_idx]
                                            cond_name = get_condition_name(t_codes[matched_idx])
                                            humidity_val = f"{t_humids[matched_idx]}%"
                                    elif target_date:
                                        d_times = daily.get("time", [])
                                        if target_date in d_times:
                                            d_idx = d_times.index(target_date)
                                            temp_val = daily.get("temperature_2m_max", [22])[d_idx]
                                            cond_name = get_condition_name(daily.get("weather_code", [0])[d_idx])
                                        else:
                                            curr = weather.get("current", {})
                                            temp_val = curr.get("temperature_2m", 22)
                                            cond_name = get_condition_name(curr.get("weather_code", 0))
                                else:
                                    # Regular current weather
                                    weather = ws.get_weather(city)
                                    curr = weather.get("current", {})
                                    temp_val = curr.get("temperature_2m", 22)
                                    cond_name = get_condition_name(curr.get("weather_code", 0))
                                    humidity_val = f"{curr.get('relative_humidity_2m', 60)}%"

                                temp_str = f"{int(round(temp_val))}°C"
                                weather_snapshot = WeatherSnapshot(
                                    location=f"{loc_coords['name']}, {loc_coords.get('country', '')}",
                                    temp=temp_str,
                                    condition=cond_name,
                                    humidity=humidity_val,
                                    recommendation=get_recommendation(cond_name, temp_val)
                                )
                            except Exception as ex:
                                print(f"Error extracting weather snapshot: {ex}", flush=True)
                        break

        return ChatResponse(
            reply=reply_text,
            session_id=session_id,
            target_date=target_date,
            target_time=target_time,
            target_label=target_label,
            weather_snapshot=weather_snapshot,
            location=location_data
        )
    except Exception as e:
        print(f"Error handling chat request: {e}", flush=True)
        # If location was provided in request, attempt direct fallback weather lookup
        if request.location:
            try:
                from app.service.weather_service import WeatherService
                weather = WeatherService().get_weather(request.location)
                loc = weather["location"]
                curr = weather["current"]
                temp_v = curr.get("temperature_2m", 22)
                cond_n = get_condition_name(curr.get("weather_code", 0))
                return ChatResponse(
                    reply=f"Here is the current weather for **{loc['name']}, {loc.get('country', '')}**: Currently **{int(round(temp_v))}°C** with **{cond_n}**, humidity at {curr.get('relative_humidity_2m', 60)}%.",
                    session_id=session_id,
                    weather_snapshot=WeatherSnapshot(
                        location=f"{loc['name']}, {loc.get('country', '')}",
                        temp=f"{int(round(temp_v))}°C",
                        condition=cond_n,
                        humidity=f"{curr.get('relative_humidity_2m', 60)}%",
                        recommendation=get_recommendation(cond_n, temp_v)
                    ),
                    location=WeatherLocation(
                        name=loc["name"],
                        country=loc.get("country", ""),
                        latitude=loc["latitude"],
                        longitude=loc["longitude"]
                    )
                )
            except Exception:
                pass
        return ChatResponse(
            reply="I'm having trouble connecting to the AI services right now. Please try asking again in a moment.",
            session_id=session_id,
            weather_snapshot=None,
            location=None
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
