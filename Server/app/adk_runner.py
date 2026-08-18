import os
import logging
from typing import Dict, Any, List
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from app.adk_agent import create_adk_agent

logger = logging.getLogger("weather_agent.adk_runner")

# Candidate models for resilient fallbacks
CANDIDATE_MODELS = [
    os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    "gemini-2.5-flash",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.7-flash"
]

# Shared In-Memory session service to keep conversation state across fallbacks
session_service = InMemorySessionService()

# Pre-build runners for all candidate models
_runners: Dict[str, Runner] = {}

def get_runner(model_name: str) -> Runner:
    if model_name not in _runners:
        agent = create_adk_agent(model_name)
        _runners[model_name] = Runner(
            app_name=f"weather_app_{model_name.replace('-', '_').replace('.', '_')}",
            agent=agent,
            session_service=session_service,
            auto_create_session=True
        )
    return _runners[model_name]

async def ask_adk_agent(
    message: str,
    session_id: str,
    user_id: str = "default_user"
) -> Dict[str, Any]:
    """
    Executes a user query through Google ADK Runner with automatic multi-model fallback.
    """
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=message)]
    )

    last_error = None

    for model_name in CANDIDATE_MODELS:
        try:
            runner = get_runner(model_name)
            full_reply_text = ""
            executed_tool_calls: List[Dict[str, Any]] = []

            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            ):
                if event.content:
                    for part in event.content.parts:
                        if part.function_call:
                            executed_tool_calls.append({
                                "name": part.function_call.name,
                                "args": dict(part.function_call.args) if part.function_call.args else {}
                            })
                        elif part.text:
                            full_reply_text += part.text

            if full_reply_text:
                return {
                    "reply": full_reply_text.strip(),
                    "tool_calls": executed_tool_calls,
                    "model": model_name
                }

        except Exception as e:
            err_str = str(e)
            logger.warning(f"Google ADK model '{model_name}' failed with {type(e).__name__}: {err_str}. Trying next candidate...")
            last_error = e
            continue

    if last_error:
        raise last_error

    return {
        "reply": "I'm having trouble retrieving weather data right now. Please try again in a moment.",
        "tool_calls": [],
        "model": "none"
    }
