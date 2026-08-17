from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from app.tools import get_weather, get_historical_weather

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

primary_model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Create primary model
primary_model = ChatGoogleGenerativeAI(
    model=primary_model_name,
    temperature=0,
    max_retries=2,
    request_timeout=20,
)

# Robust fallback models in case of high demand (503) or rate limits (429)
fallback_candidates = ["gemini-flash-lite-latest", "gemini-3.1-flash-lite", "gemini-3.7-flash"]
fallback_models = [
    ChatGoogleGenerativeAI(model=m, temperature=0, max_retries=2, request_timeout=20)
    for m in fallback_candidates
    if m != primary_model_name
]

# Attach fallbacks to primary model
model_with_fallbacks = primary_model.with_fallbacks(fallback_models)

llm_tools = model_with_fallbacks.bind_tools(
    [get_weather, get_historical_weather]
)