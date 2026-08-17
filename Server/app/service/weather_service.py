import requests
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GEOCODING_URL = (
    "https://geocoding-api.open-meteo.com/v1/search"
)

FORECAST_URL = (
    "https://api.open-meteo.com/v1/forecast"
)

HISTORICAL_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)

# Reusable keep-alive session to avoid performing TLS handshake on every request
_session = requests.Session()

# Caches to avoid redundant network overhead
_geocoding_cache = {}
_forecast_cache = {}
_historical_cache = {}

CACHE_TTL = 600  # 10 minutes in seconds

class WeatherService:

    def get_coordinates(self, city: str) -> dict:
        city_key = city.strip().lower()
        if city_key in _geocoding_cache:
            return _geocoding_cache[city_key]

        response = _session.get(
            GEOCODING_URL,
            params={
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json",
            },
            timeout=10,
            verify=False,
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("results"):
            raise ValueError(
                f"Could not find location: {city}"
            )

        location = data["results"][0]

        res = {
            "name": location["name"],
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "country": location.get("country"),
        }
        
        # Indefinite cache for city-to-coordinate mapping (rarely changes)
        _geocoding_cache[city_key] = res
        return res

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
    ) -> dict:
        # Cache key rounded to 3 decimal places (approx. 100 meters precision)
        cache_key = (round(latitude, 3), round(longitude, 3))
        now = time.time()
        
        if cache_key in _forecast_cache:
            cached_time, cached_data = _forecast_cache[cache_key]
            if now - cached_time < CACHE_TTL:
                return cached_data

        response = _session.get(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
                "hourly": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "precipitation_probability,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
                "daily": (
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "apparent_temperature_max,"
                    "apparent_temperature_min,"
                    "precipitation_sum,"
                    "precipitation_probability_max,"
                    "weather_code,"
                    "wind_speed_10m_max"
                ),
                "forecast_days": 14,
                "past_days": 7,
                "timezone": "auto",
            },
            timeout=10,
            verify=False,
        )

        response.raise_for_status()
        data = response.json()
        
        _forecast_cache[cache_key] = (now, data)
        return data

    def get_historical(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
    ) -> dict:
        cache_key = (round(latitude, 3), round(longitude, 3), start_date, end_date)
        if cache_key in _historical_cache:
            return _historical_cache[cache_key]

        response = _session.get(
            HISTORICAL_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date,
                "end_date": end_date,
                "daily": (
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "apparent_temperature_max,"
                    "apparent_temperature_min,"
                    "precipitation_sum,"
                    "weather_code,"
                    "wind_speed_10m_max"
                ),
                "hourly": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
                "timezone": "auto",
            },
            timeout=10,
            verify=False,
        )

        response.raise_for_status()
        data = response.json()
        _historical_cache[cache_key] = data
        return data

    def get_weather(self, city: str) -> dict:

        location = self.get_coordinates(city)

        weather = self.get_forecast(
            latitude=location["latitude"],
            longitude=location["longitude"],
        )

        return {
            "location": location,
            "current": weather.get("current", {}),
            "hourly": weather.get("hourly", {}),
            "daily": weather.get("daily", {}),
            "units": weather.get(
                "current_units",
                {},
            ),
        }

    def get_historical_weather(self, city: str, start_date: str, end_date: str = None) -> dict:
        if not end_date:
            end_date = start_date

        location = self.get_coordinates(city)
        hist = self.get_historical(
            latitude=location["latitude"],
            longitude=location["longitude"],
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "location": location,
            "daily": hist.get("daily", {}),
            "hourly": hist.get("hourly", {}),
            "units": hist.get("daily_units", {}),
        }