from app.service.weather_service import WeatherService, WeatherDateError, LocationNotFoundError

ws = WeatherService()

def get_current_weather(city: str) -> str:
    """Get real-time current live weather conditions for a city.
    
    Args:
        city: Name of the city (e.g. 'Visakhapatnam', 'Tokyo', 'London', 'New York').
    """
    try:
        w = ws.get_current_weather(city)
        loc = w["location"]
        return (
            f"Current Weather in {loc['name']}, {loc.get('country', '')} (Local Time: {w.get('local_time', 'Now')}):\n"
            f"- Temperature: {w['temperature_c']}°C (Feels like: {w['feels_like_c']}°C)\n"
            f"- Condition: {w['condition']}\n"
            f"- Humidity: {w['humidity_percent']}%\n"
            f"- Wind Speed: {w['wind_speed_kmh']} km/h\n"
            f"- Precipitation: {w['precipitation_mm']} mm"
        )
    except (LocationNotFoundError, WeatherDateError, RuntimeError) as e:
        return f"Error getting current weather for '{city}': {e}"


def get_weather_forecast(city: str, date: str) -> str:
    """Get weather forecast for a single specific upcoming date within the next 16 days.
    
    Args:
        city: Name of the city.
        date: Target upcoming date in ISO format YYYY-MM-DD (e.g. '2026-08-22').
    """
    try:
        w = ws.get_daily_forecast(city, date)
        loc = w["location"]
        return (
            f"Forecast for {loc['name']}, {loc.get('country', '')} on {date}:\n"
            f"- Condition: {w['condition']}\n"
            f"- Temperature: High {w['temp_max_c']}°C / Low {w['temp_min_c']}°C\n"
            f"- Rain Probability: {w['rain_probability_max']}%\n"
            f"- Total Precipitation: {w['precipitation_sum_mm']} mm\n"
            f"- Sunrise: {w['sunrise']} | Sunset: {w['sunset']}"
        )
    except (LocationNotFoundError, WeatherDateError, RuntimeError) as e:
        return f"Error getting forecast for '{city}' on {date}: {e}"


def get_hourly_forecast(city: str, date: str, hour: int) -> str:
    """Get weather forecast for an exact hour of the day.
    
    Args:
        city: Name of the city.
        date: Target date in ISO format YYYY-MM-DD (e.g. '2026-08-18').
        hour: Hour of the day as an integer from 0 to 23 (e.g. 20 for 8 PM, 23 for 11 PM).
    """
    try:
        w = ws.get_hourly_forecast(city, date, hour)
        loc = w["location"]
        return (
            f"Hourly Forecast for {loc['name']}, {loc.get('country', '')} on {date} at {w['hour']}:\n"
            f"- Temperature: {w['temperature_c']}°C (Feels like: {w['feels_like_c']}°C)\n"
            f"- Condition: {w['condition']}\n"
            f"- Rain Probability: {w['rain_probability']}%\n"
            f"- Precipitation: {w['precipitation_mm']} mm\n"
            f"- Humidity: {w['humidity_percent']}%"
        )
    except (LocationNotFoundError, WeatherDateError, ValueError, RuntimeError) as e:
        return f"Error getting hourly forecast for '{city}' on {date} at {hour:02d}:00: {e}"


def get_weather_forecast_range(city: str, start_date: str, end_date: str) -> str:
    """Get multi-day weather forecast for an upcoming date range (within next 16 days).
    
    Args:
        city: Name of the city.
        start_date: Starting date in ISO format YYYY-MM-DD.
        end_date: Ending date in ISO format YYYY-MM-DD.
    """
    try:
        w = ws.get_forecast_range(city, start_date, end_date)
        loc = w["location"]
        lines = [f"Forecast for {loc['name']}, {loc.get('country', '')} from {start_date} to {end_date}:"]
        for d in w["days"]:
            lines.append(
                f"- {d['date']}: {d['condition']} | High: {d['temp_max_c']}°C / Low: {d['temp_min_c']}°C | Rain: {d['rain_prob_max']}%"
            )
        return "\n".join(lines)
    except (LocationNotFoundError, WeatherDateError, ValueError, RuntimeError) as e:
        return f"Error getting forecast range for '{city}' ({start_date} to {end_date}): {e}"


def get_historical_weather(city: str, date: str) -> str:
    """Get past weather observations for a single past date.
    
    Args:
        city: Name of the city.
        date: Past date in ISO format YYYY-MM-DD (e.g. '2025-07-14').
    """
    try:
        w = ws.get_historical_weather(city, date)
        loc = w["location"]
        return (
            f"Historical Weather in {loc['name']}, {loc.get('country', '')} on {date}:\n"
            f"- Condition: {w['condition']}\n"
            f"- Temperature: High {w['temp_max_c']}°C / Low {w['temp_min_c']}°C\n"
            f"- Total Precipitation: {w['precipitation_sum_mm']} mm\n"
            f"- Max Wind Speed: {w['wind_speed_max_kmh']} km/h"
        )
    except (LocationNotFoundError, WeatherDateError, RuntimeError) as e:
        return f"Error getting historical weather for '{city}' on {date}: {e}"


def get_historical_weather_range(city: str, start_date: str, end_date: str) -> str:
    """Get past weather observations for a date range in the past.
    
    Args:
        city: Name of the city.
        start_date: Starting past date in ISO format YYYY-MM-DD.
        end_date: Ending past date in ISO format YYYY-MM-DD.
    """
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

ALL_ADK_TOOLS = [
    get_current_weather,
    get_weather_forecast,
    get_hourly_forecast,
    get_weather_forecast_range,
    get_historical_weather,
    get_historical_weather_range
]
