import os
import logging
from typing import List
import httpx
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from google.genai.errors import ServerError, APIError, ClientError

from app.tools import (
    get_current_weather,
    get_weather_forecast,
    get_hourly_forecast,
    get_weather_forecast_range,
    get_historical_weather,
    get_historical_weather_range
)

logger = logging.getLogger("weather_agent.llm")

# Load environment configuration
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.warning("Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set in environment or .env file.")

primary_model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Candidate fallback pool ordered by latency and capability
FALLBACK_CANDIDATES = [
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.7-flash"
]

# Transient infrastructure errors that qualify for candidate fallback
RETRYABLE_EXCEPTIONS = (
    ServerError,                # 500, 502, 503, 504 Service Overloaded
    APIError,                   # 429 Rate Limits / Quotas
    httpx.TimeoutException,     # Network Timeout
    httpx.ConnectError,         # Connection Failure
    TimeoutError
)

def create_chat_model(model_name: str) -> ChatGoogleGenerativeAI:
    """Instantiate a ChatGoogleGenerativeAI model with production timeout and retry limits."""
    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0,
        max_retries=1,          # Fast single retry before triggering model fallback
        request_timeout=15,     # 15s timeout prevents hanging requests
        google_api_key=api_key
    )

# 1. Instantiate Primary Model
primary_model = create_chat_model(primary_model_name)

# 2. Instantiate Fallback Candidate Models
fallback_models: List[ChatGoogleGenerativeAI] = [
    create_chat_model(name)
    for name in FALLBACK_CANDIDATES
    if name != primary_model_name
]

# 3. Attach fallback models strictly for transient errors
# exceptions_to_handle ensures 401 (Auth) or 400 (Bad Request) fail fast without looping
model_with_fallbacks = primary_model.with_fallbacks(
    fallback_models,
    exceptions_to_handle=RETRYABLE_EXCEPTIONS
)

# 4. Bind all 6 Granular Weather Tools
ALL_TOOLS = [
    get_current_weather,
    get_weather_forecast,
    get_hourly_forecast,
    get_weather_forecast_range,
    get_historical_weather,
    get_historical_weather_range
]

llm_tools = model_with_fallbacks.bind_tools(ALL_TOOLS)