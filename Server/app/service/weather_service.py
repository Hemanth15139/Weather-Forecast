import time
import requests
import urllib3
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, Optional, Tuple
from zoneinfo import ZoneInfo

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

# Reusable HTTP session
_session = requests.Session()

# Caches
_geocoding_cache: Dict[str, Dict[str, Any]] = {}
_cache: Dict[Tuple, Tuple[float, Dict[str, Any]]] = {}
CACHE_TTL = 300  # 5 minutes cache

WEATHER_CODE_NAMES = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    56: "Light Freezing Drizzle",
    57: "Dense Freezing Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    66: "Light Freezing Rain",
    67: "Heavy Freezing Rain",
    71: "Slight Snow Fall",
    73: "Moderate Snow Fall",
    75: "Heavy Snow Fall",
    77: "Snow Grains",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    85: "Slight Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail"
}

class WeatherDateError(ValueError):
    """Raised when a date is outside supported forecast or historical horizons."""
    pass

class LocationNotFoundError(ValueError):
    """Raised when geocoding fails to resolve a location."""
    pass

class WeatherService:
    """Core domain service for weather retrieval with location-aware timezone support."""

    def get_coordinates(self, city: str) -> Dict[str, Any]:
        """Resolve city name to coordinates and local timezone string."""
        city_key = city.strip().lower()
        if city_key in _geocoding_cache:
            return _geocoding_cache[city_key]

        try:
            resp = _session.get(
                GEOCODING_URL,
                params={"name": city, "count": 1, "language": "en", "format": "json"},
                timeout=10,
                verify=False
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            raise LocationNotFoundError(f"Failed to connect to geocoding service: {e}")

        if not data.get("results"):
            raise LocationNotFoundError(f"Could not find location '{city}'. Please check the city name.")

        location = data["results"][0]
        result = {
            "name": location["name"],
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "country": location.get("country", ""),
            "admin1": location.get("admin1", ""),
            "timezone": location.get("timezone", "UTC")
        }
        _geocoding_cache[city_key] = result
        return result

    def get_city_local_datetime(self, tz_name: str, utc_offset_seconds: Optional[int] = None) -> datetime:
        """Get the current datetime at the target location's timezone."""
        if utc_offset_seconds is not None:
            tz_obj = timezone(timedelta(seconds=utc_offset_seconds))
            return datetime.now(timezone.utc).astimezone(tz_obj)
        try:
            from dateutil import tz
            tz_obj = tz.gettz(tz_name)
            if tz_obj:
                return datetime.now(timezone.utc).astimezone(tz_obj)
        except Exception:
            pass
        try:
            return datetime.now(ZoneInfo(tz_name))
        except Exception:
            pass
        return datetime.now(timezone.utc)

    def get_city_local_date(self, tz_name: str, utc_offset_seconds: Optional[int] = None) -> date:
        """Get the current date at the target location's timezone."""
        return self.get_city_local_datetime(tz_name, utc_offset_seconds).date()

    def validate_date_horizon(self, target_date_str: str, city_tz: str) -> str:
        """
        Validates target date against city's local date.
        Returns category: 'CURRENT', 'FORECAST', 'HISTORICAL', or raises WeatherDateError.
        """
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise WeatherDateError(f"Invalid date format '{target_date_str}'. Expected YYYY-MM-DD.")

        local_today = self.get_city_local_date(city_tz)
        max_forecast_date = local_today + timedelta(days=16)
        min_historical_date = date(1940, 1, 1)

        if target_date == local_today:
            return "CURRENT"
        elif local_today < target_date <= max_forecast_date:
            return "FORECAST"
        elif min_historical_date <= target_date < local_today:
            return "HISTORICAL"
        elif target_date > max_forecast_date:
            days_ahead = (target_date - local_today).days
            raise WeatherDateError(
                f"Date {target_date_str} is {days_ahead} days in the future. "
                f"Reliable weather forecasts are only available up to 16 days in advance (until {max_forecast_date.strftime('%Y-%m-%d')})."
            )
        else:
            raise WeatherDateError(
                f"Date {target_date_str} is before 1940-01-01 and outside historical archives."
            )

    def get_current_weather(self, city: str) -> Dict[str, Any]:
        """Fetch strictly current weather conditions for a city."""
        loc = self.get_coordinates(city)
        params = {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure",
            "timezone": loc["timezone"]
        }
        data = self._make_request(FORECAST_URL, params)
        current = data.get("current", {})
        wcode = current.get("weather_code", 0)

        return {
            "location": loc,
            "local_time": current.get("time"),
            "temperature_c": current.get("temperature_2m"),
            "feels_like_c": current.get("apparent_temperature"),
            "condition": WEATHER_CODE_NAMES.get(wcode, "Unknown"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "wind_direction_deg": current.get("wind_direction_10m"),
            "precipitation_mm": current.get("precipitation", 0.0),
            "pressure_hpa": current.get("surface_pressure")
        }

    def get_daily_forecast(self, city: str, target_date: str) -> Dict[str, Any]:
        """Fetch daily forecast for a single specific date within the 16-day window."""
        loc = self.get_coordinates(city)
        self.validate_date_horizon(target_date, loc["timezone"])

        params = {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "start_date": target_date,
            "end_date": target_date,
            "daily": "temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,precipitation_probability_max,weather_code,wind_speed_10m_max,sunrise,sunset,uv_index_max",
            "timezone": loc["timezone"]
        }
        data = self._make_request(FORECAST_URL, params)
        daily = data.get("daily", {})
        if not daily.get("time"):
            raise WeatherDateError(f"No forecast data available for {target_date}.")

        wcode = daily.get("weather_code", [0])[0]
        return {
            "location": loc,
            "date": target_date,
            "condition": WEATHER_CODE_NAMES.get(wcode, "Unknown"),
            "temp_max_c": daily.get("temperature_2m_max", [None])[0],
            "temp_min_c": daily.get("temperature_2m_min", [None])[0],
            "feels_like_max_c": daily.get("apparent_temperature_max", [None])[0],
            "feels_like_min_c": daily.get("apparent_temperature_min", [None])[0],
            "precipitation_sum_mm": daily.get("precipitation_sum", [0.0])[0],
            "rain_probability_max": daily.get("precipitation_probability_max", [0])[0],
            "wind_speed_max_kmh": daily.get("wind_speed_10m_max", [None])[0],
            "uv_index_max": daily.get("uv_index_max", [None])[0],
            "sunrise": daily.get("sunrise", [None])[0],
            "sunset": daily.get("sunset", [None])[0]
        }

    def get_hourly_forecast(self, city: str, target_date: str, hour: int) -> Dict[str, Any]:
        """Fetch forecast for a specific hour (0-23) on a specific date."""
        loc = self.get_coordinates(city)
        self.validate_date_horizon(target_date, loc["timezone"])

        if not (0 <= hour <= 23):
            raise ValueError("Hour must be an integer between 0 and 23.")

        params = {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "start_date": target_date,
            "end_date": target_date,
            "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,precipitation,weather_code,wind_speed_10m",
            "timezone": loc["timezone"]
        }
        data = self._make_request(FORECAST_URL, params)
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])

        # Match specific hour: e.g. "2026-08-20T20:00"
        target_iso_hour = f"{target_date}T{hour:02d}:00"
        matching_idx = None
        for i, t in enumerate(times):
            if t.startswith(target_iso_hour[:13]):
                matching_idx = i
                break

        if matching_idx is None or matching_idx >= len(hourly.get("temperature_2m", [])):
            raise WeatherDateError(f"Hourly data for {target_date} at {hour:02d}:00 is not available.")

        wcode = hourly.get("weather_code", [0])[matching_idx]
        return {
            "location": loc,
            "date": target_date,
            "hour": f"{hour:02d}:00",
            "condition": WEATHER_CODE_NAMES.get(wcode, "Unknown"),
            "temperature_c": hourly.get("temperature_2m", [])[matching_idx],
            "feels_like_c": hourly.get("apparent_temperature", [])[matching_idx],
            "humidity_percent": hourly.get("relative_humidity_2m", [])[matching_idx],
            "rain_probability": hourly.get("precipitation_probability", [])[matching_idx],
            "precipitation_mm": hourly.get("precipitation", [])[matching_idx],
            "wind_speed_kmh": hourly.get("wind_speed_10m", [])[matching_idx]
        }

    def get_forecast_range(self, city: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Fetch daily forecast for a date range within the 16-day window."""
        loc = self.get_coordinates(city)
        self.validate_date_horizon(start_date, loc["timezone"])
        self.validate_date_horizon(end_date, loc["timezone"])

        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) cannot be after end_date ({end_date}).")

        params = {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weather_code",
            "timezone": loc["timezone"]
        }
        data = self._make_request(FORECAST_URL, params)
        daily = data.get("daily", {})
        results = []
        for i, dt in enumerate(daily.get("time", [])):
            wcode = daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else 0
            results.append({
                "date": dt,
                "condition": WEATHER_CODE_NAMES.get(wcode, "Unknown"),
                "temp_max_c": daily.get("temperature_2m_max", [])[i],
                "temp_min_c": daily.get("temperature_2m_min", [])[i],
                "rain_prob_max": daily.get("precipitation_probability_max", [])[i],
                "precipitation_mm": daily.get("precipitation_sum", [])[i]
            })

        return {"location": loc, "range": f"{start_date} to {end_date}", "days": results}

    def get_historical_weather(self, city: str, target_date: str) -> Dict[str, Any]:
        """Fetch historical weather for a single past date."""
        loc = self.get_coordinates(city)
        self.validate_date_horizon(target_date, loc["timezone"])
        
        local_today = self.get_city_local_date(loc["timezone"])
        target_d = datetime.strptime(target_date, "%Y-%m-%d").date()

        # If target date is within the last 7 days, use high-precision forecast endpoint with past_days
        if target_d >= (local_today - timedelta(days=7)):
            params = {
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "start_date": target_date,
                "end_date": target_date,
                "daily": "temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,weather_code,wind_speed_10m_max",
                "timezone": loc["timezone"]
            }
            data = self._make_request(FORECAST_URL, params)
        else:
            params = {
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "start_date": target_date,
                "end_date": target_date,
                "daily": "temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,weather_code,wind_speed_10m_max",
                "timezone": loc["timezone"]
            }
            data = self._make_request(HISTORICAL_URL, params)

        daily = data.get("daily", {})
        if not daily.get("time"):
            raise WeatherDateError(f"No historical data available for {target_date}.")

        wcode = daily.get("weather_code", [0])[0]
        return {
            "location": loc,
            "date": target_date,
            "condition": WEATHER_CODE_NAMES.get(wcode, "Unknown"),
            "temp_max_c": daily.get("temperature_2m_max", [None])[0],
            "temp_min_c": daily.get("temperature_2m_min", [None])[0],
            "feels_like_max_c": daily.get("apparent_temperature_max", [None])[0],
            "feels_like_min_c": daily.get("apparent_temperature_min", [None])[0],
            "precipitation_sum_mm": daily.get("precipitation_sum", [0.0])[0],
            "wind_speed_max_kmh": daily.get("wind_speed_10m_max", [None])[0]
        }

    def get_historical_range(self, city: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Fetch historical weather for a past date range."""
        loc = self.get_coordinates(city)
        self.validate_date_horizon(start_date, loc["timezone"])
        self.validate_date_horizon(end_date, loc["timezone"])

        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) cannot be after end_date ({end_date}).")

        local_today = self.get_city_local_date(loc["timezone"])
        start_d = datetime.strptime(start_date, "%Y-%m-%d").date()

        # If start date is within last 7 days, use FORECAST_URL
        if start_d >= (local_today - timedelta(days=7)):
            url = FORECAST_URL
        else:
            url = HISTORICAL_URL

        params = {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "timezone": loc["timezone"]
        }
        data = self._make_request(url, params)
        daily = data.get("daily", {})
        results = []
        for i, dt in enumerate(daily.get("time", [])):
            wcode = daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else 0
            results.append({
                "date": dt,
                "condition": WEATHER_CODE_NAMES.get(wcode, "Unknown"),
                "temp_max_c": daily.get("temperature_2m_max", [])[i],
                "temp_min_c": daily.get("temperature_2m_min", [])[i],
                "precipitation_mm": daily.get("precipitation_sum", [])[i]
            })

        return {"location": loc, "range": f"{start_date} to {end_date}", "days": results}

    def get_weather(self, city: str) -> Dict[str, Any]:
        """Comprehensive weather summary helper for city dashboard snapshots."""
        loc = self.get_coordinates(city)
        params = {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure",
            "daily": "temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,precipitation_probability_max,weather_code,wind_speed_10m_max,sunrise,sunset,uv_index_max",
            "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,precipitation,weather_code,wind_speed_10m",
            "forecast_days": 16,
            "past_days": 2,
            "timezone": loc["timezone"]
        }
        data = self._make_request(FORECAST_URL, params)
        return {
            "location": loc,
            "current": data.get("current", {}),
            "daily": data.get("daily", {}),
            "hourly": data.get("hourly", {}),
            "units": data.get("current_units", {})
        }

    def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Internal cached request helper with error handling."""
        cache_key = (url, tuple(sorted(params.items())))
        now = time.time()
        if cache_key in _cache:
            cached_time, cached_val = _cache[cache_key]
            if now - cached_time < CACHE_TTL:
                return cached_val

        try:
            resp = _session.get(url, params=params, timeout=10, verify=False)
            resp.raise_for_status()
            data = resp.json()
            _cache[cache_key] = (now, data)
            return data
        except requests.exceptions.Timeout:
            raise RuntimeError("Weather API request timed out. Please try again.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RuntimeError("Weather API rate limit exceeded. Please wait a moment.")
            elif e.response.status_code >= 500:
                raise RuntimeError("Weather API is temporarily unavailable.")
            raise RuntimeError(f"Weather API returned error HTTP {e.response.status_code}.")
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to reach Weather API: {e}")