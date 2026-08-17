
from datetime import datetime
# pyrefly: ignore [missing-import]
from langchain_core.tools import tool
from app.service.weather_service import WeatherService

WEATHER_CODE_NAMES = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    71: "Slight Snow Fall",
    73: "Moderate Snow Fall",
    75: "Heavy Snow Fall",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail"
}

def format_hour_label(dt_str: str) -> str:
    try:
        dt = datetime.fromisoformat(dt_str)
        # Formats as "2026-08-17 11:00 PM (23:00)"
        return dt.strftime("%Y-%m-%d %I:%M %p (%H:%M)")
    except Exception:
        return dt_str

@tool
def get_weather(city: str) -> str:
    """Get real-time current weather, 14-day future daily forecast outlook (including specific upcoming dates), and hourly forecast timeline for a city."""
    weather = WeatherService().get_weather(city)

    location = weather["location"]
    current = weather.get("current", {})
    hourly = weather.get("hourly", {})
    daily = weather.get("daily", {})
    units = weather.get("units", {})

    temp_unit = units.get("temperature_2m", "°C")
    wind_unit = units.get("wind_speed_10m", "km/h")
    precip_unit = units.get("precipitation", "mm")
    curr_code = current.get("weather_code", 0)
    curr_condition = WEATHER_CODE_NAMES.get(curr_code, "Partly Cloudy")

    lines = [
        f"Weather Report for {location['name']}, {location.get('country', '')}:",
        f"Current Temperature: {current.get('temperature_2m', 'N/A')}{temp_unit}",
        f"Feels like: {current.get('apparent_temperature', 'N/A')}{temp_unit}",
        f"Condition: {curr_condition}",
        f"Humidity: {current.get('relative_humidity_2m', 'N/A')}%",
        f"Wind: {current.get('wind_speed_10m', 'N/A')} {wind_unit}",
        f"Precipitation: {current.get('precipitation', '0.0')} {precip_unit}",
    ]

    # Include Daily Summary (14-Day Outlook & Recent History)
    d_times = daily.get("time", [])
    d_max = daily.get("temperature_2m_max", [])
    d_min = daily.get("temperature_2m_min", [])
    d_rain_prob = daily.get("precipitation_probability_max", [])
    d_precip = daily.get("precipitation_sum", [])
    d_codes = daily.get("weather_code", [])

    if d_times and d_max:
        lines.append("\n14-Day Daily Forecast Outlook (Use this for specific future dates or multi-day forecasts):")
        for i, dt in enumerate(d_times):
            try:
                day_label = datetime.fromisoformat(dt).strftime("%A, %b %d")
            except Exception:
                day_label = dt
            mx = d_max[i] if i < len(d_max) else "N/A"
            mn = d_min[i] if i < len(d_min) else "N/A"
            p_prob = d_rain_prob[i] if i < len(d_rain_prob) else 0
            psum = d_precip[i] if i < len(d_precip) else 0
            w_code = d_codes[i] if i < len(d_codes) else 0
            cond = WEATHER_CODE_NAMES.get(w_code, "Partly Cloudy")
            lines.append(
                f"{dt} ({day_label}) -> High: {mx}{temp_unit}, Low: {mn}{temp_unit} | Condition: {cond} | Rain Chance: {p_prob}% | Total Precip: {psum}{precip_unit}"
            )

    # Include detailed hourly forecast timeline (Filtered from TODAY onwards)
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    precip_probs = hourly.get("precipitation_probability", [])
    precips = hourly.get("precipitation", [])
    apparent_temps = hourly.get("apparent_temperature", [])
    weather_codes = hourly.get("weather_code", [])

    # Find starting index for today
    today_str = datetime.now().strftime("%Y-%m-%d")
    start_idx = 0
    for i, t in enumerate(times):
        if t.startswith(today_str):
            start_idx = i
            break

    if times and temps:
        lines.append("\nHourly Forecast Timeline (Starting from Today - Use for specific time of day queries):")
        for i in range(start_idx, min(start_idx + 72, len(times))):
            t = times[i]
            time_label = format_hour_label(t)
            temp_v = temps[i] if i < len(temps) else ""
            app_v = apparent_temps[i] if i < len(apparent_temps) else ""
            prob_v = precip_probs[i] if i < len(precip_probs) else 0
            prec_v = precips[i] if i < len(precips) else 0
            wcode_v = weather_codes[i] if i < len(weather_codes) else 0
            cond_name = WEATHER_CODE_NAMES.get(wcode_v, "Partly Cloudy")
            lines.append(
                f"{time_label} -> Temp: {temp_v}{temp_unit} (Feels like {app_v}{temp_unit}) | Condition: {cond_name} | Rain Prob: {prob_v}% | Precip: {prec_v}{precip_unit}"
            )

    return "\n".join(lines)

@tool
def get_historical_weather(city: str, date: str, end_date: str = None) -> str:
    """Get past/historical weather observations for a city for any specific date in the past (format: YYYY-MM-DD). If checking a range, provide end_date (format: YYYY-MM-DD)."""
    weather = WeatherService().get_historical_weather(city, start_date=date, end_date=end_date)
    location = weather["location"]
    daily = weather.get("daily", {})
    hourly = weather.get("hourly", {})

    lines = [
        f"Historical Weather Report for {location['name']}, {location.get('country', '')} on {date}" + (f" to {end_date}:" if end_date and end_date != date else ":")
    ]

    d_times = daily.get("time", [])
    d_max = daily.get("temperature_2m_max", [])
    d_min = daily.get("temperature_2m_min", [])
    d_precip = daily.get("precipitation_sum", [])
    d_codes = daily.get("weather_code", [])

    if d_times:
        lines.append("\nHistorical Daily Summary:")
        for i, dt in enumerate(d_times):
            mx = d_max[i] if i < len(d_max) else "N/A"
            mn = d_min[i] if i < len(d_min) else "N/A"
            psum = d_precip[i] if i < len(d_precip) else 0
            w_code = d_codes[i] if i < len(d_codes) else 0
            cond = WEATHER_CODE_NAMES.get(w_code, "Partly Cloudy")
            lines.append(
                f"Date: {dt} -> High: {mx}°C, Low: {mn}°C | Condition: {cond} | Total Precipitation: {psum}mm"
            )

    h_times = hourly.get("time", [])
    h_temps = hourly.get("temperature_2m", [])
    h_precips = hourly.get("precipitation", [])
    h_codes = hourly.get("weather_code", [])

    if h_times and len(d_times) <= 3:
        lines.append("\nHistorical Hourly Records:")
        for i, t in enumerate(h_times[:48]):
            time_label = format_hour_label(t)
            temp_v = h_temps[i] if i < len(h_temps) else ""
            prec_v = h_precips[i] if i < len(h_precips) else 0
            wcode_v = h_codes[i] if i < len(h_codes) else 0
            cond_name = WEATHER_CODE_NAMES.get(wcode_v, "Partly Cloudy")
            lines.append(
                f"{time_label} -> Temp: {temp_v}°C | Condition: {cond_name} | Precip: {prec_v}mm"
            )

    return "\n".join(lines)