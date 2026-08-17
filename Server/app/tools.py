from langchain_core.tools import tool
from app.service.weather_service import WeatherService, WeatherDateError, LocationNotFoundError

ws = WeatherService()

@tool
def get_current_weather(city: str) -> str:
    """Get real-time current live weather conditions for a city.
    Use this when the user asks for current/now weather without mentioning any future or past dates."""
    try:
        w = ws.get_current_weather(city)
        loc = w["location"]
        return (
            f"Current Weather in {loc['name']}, {loc.get('country', '')} (Local Time: {w.get('local_time', 'Now')}):\n"
            f"- Temperature: {w['temperature_c']}°C (Feels like: {w['feels_like_c']}°C)\n"
            f"- Condition: {w['condition']}\n"
            f"- Humidity: {w['humidity_percent']}%\n"
            f"- Wind Speed: {w['wind_speed_kmh']} km/h (Direction: {w['wind_direction_deg']}°)\n"
            f"- Precipitation: {w['precipitation_mm']} mm | Pressure: {w['pressure_hpa']} hPa"
        )
    except (LocationNotFoundError, WeatherDateError, RuntimeError) as e:
        return f"Error getting current weather for '{city}': {e}"

@tool
def get_weather_forecast(city: str, date: str) -> str:
    """Get weather forecast for a single specific upcoming date (format: YYYY-MM-DD, up to 16 days in the future).
    Use this when the user asks about a specific upcoming day (e.g. 'tomorrow', 'August 22', 'next Friday')."""
    try:
        w = ws.get_daily_forecast(city, date)
        loc = w["location"]
        return (
            f"Forecast for {loc['name']}, {loc.get('country', '')} on {date}:\n"
            f"- Condition: {w['condition']}\n"
            f"- Temperature: High {w['temp_max_c']}°C / Low {w['temp_min_c']}°C (Feels like High {w['feels_like_max_c']}°C / Low {w['feels_like_min_c']}°C)\n"
            f"- Max Rain Probability: {w['rain_probability_max']}%\n"
            f"- Total Precipitation: {w['precipitation_sum_mm']} mm\n"
            f"- Max Wind Speed: {w['wind_speed_max_kmh']} km/h | UV Index: {w['uv_index_max']}\n"
            f"- Sunrise: {w['sunrise']} | Sunset: {w['sunset']}"
        )
    except (LocationNotFoundError, WeatherDateError, RuntimeError) as e:
        return f"Error getting forecast for '{city}' on {date}: {e}"

@tool
def get_hourly_forecast(city: str, date: str, hour: int) -> str:
    """Get weather forecast for a specific hour of the day (hour: integer from 0 to 23, date format: YYYY-MM-DD).
    Use this when the user asks about weather at a specific time (e.g. 'tomorrow at 8 PM' -> hour=20, 'tonight at 11 PM' -> hour=23)."""
    try:
        w = ws.get_hourly_forecast(city, date, hour)
        loc = w["location"]
        return (
            f"Hourly Forecast for {loc['name']}, {loc.get('country', '')} on {date} at {w['hour']}:\n"
            f"- Temperature: {w['temperature_c']}°C (Feels like: {w['feels_like_c']}°C)\n"
            f"- Condition: {w['condition']}\n"
            f"- Rain Probability: {w['rain_probability']}%\n"
            f"- Precipitation: {w['precipitation_mm']} mm\n"
            f"- Humidity: {w['humidity_percent']}% | Wind Speed: {w['wind_speed_kmh']} km/h"
        )
    except (LocationNotFoundError, WeatherDateError, ValueError, RuntimeError) as e:
        return f"Error getting hourly forecast for '{city}' on {date} at {hour:02d}:00: {e}"

@tool
def get_weather_forecast_range(city: str, start_date: str, end_date: str) -> str:
    """Get multi-day weather forecast for an upcoming date range (both dates format: YYYY-MM-DD, within the next 16 days).
    Use this when the user asks for a range (e.g. 'forecast from August 20 to August 25', 'weekend forecast', '5-day outlook')."""
    try:
        w = ws.get_forecast_range(city, start_date, end_date)
        loc = w["location"]
        lines = [f"Forecast for {loc['name']}, {loc.get('country', '')} from {start_date} to {end_date}:"]
        for d in w["days"]:
            lines.append(
                f"- {d['date']}: {d['condition']} | High: {d['temp_max_c']}°C / Low: {d['temp_min_c']}°C | Rain Chance: {d['rain_prob_max']}% | Precip: {d['precipitation_mm']}mm"
            )
        return "\n".join(lines)
    except (LocationNotFoundError, WeatherDateError, ValueError, RuntimeError) as e:
        return f"Error getting forecast range for '{city}' ({start_date} to {end_date}): {e}"

@tool
def get_historical_weather(city: str, date: str) -> str:
    """Get past/historical weather observations for a single past date (format: YYYY-MM-DD, prior to today).
    Use this when the user asks about the weather on a specific past day (e.g. 'yesterday', 'August 10', 'Paris on 2025-07-14')."""
    try:
        w = ws.get_historical_weather(city, date)
        loc = w["location"]
        return (
            f"Historical Weather in {loc['name']}, {loc.get('country', '')} on {date}:\n"
            f"- Condition: {w['condition']}\n"
            f"- Temperature: High {w['temp_max_c']}°C / Low {w['temp_min_c']}°C (Feels like High {w['feels_like_max_c']}°C / Low {w['feels_like_min_c']}°C)\n"
            f"- Total Precipitation: {w['precipitation_sum_mm']} mm\n"
            f"- Max Wind Speed: {w['wind_speed_max_kmh']} km/h"
        )
    except (LocationNotFoundError, WeatherDateError, RuntimeError) as e:
        return f"Error getting historical weather for '{city}' on {date}: {e}"

@tool
def get_historical_weather_range(city: str, start_date: str, end_date: str) -> str:
    """Get past/historical weather observations for a past date range (format: YYYY-MM-DD, prior to today).
    Use this when the user asks about past periods (e.g. 'weather between August 1 and August 5', 'last week')."""
    try:
        w = ws.get_historical_range(city, start_date, end_date)
        loc = w["location"]
        lines = [f"Historical Weather in {loc['name']}, {loc.get('country', '')} from {start_date} to {end_date}:"]
        for d in w["days"]:
            lines.append(
                f"- {d['date']}: {d['condition']} | High: {d['temp_max_c']}°C / Low: {d['temp_min_c']}°C | Precip: {d['precipitation_mm']}mm"
            )
        return "\n".join(lines)
    except (LocationNotFoundError, WeatherDateError, ValueError, RuntimeError) as e:
        return f"Error getting historical range for '{city}' ({start_date} to {end_date}): {e}"