import os
import time
from google import genai
from google.genai import errors

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

DEFAULT_MODEL = "gemini-2.5-flash"
FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-3.6-flash"]


def _try_model(model, prompt, max_retries=2):
    """Attempt to call a single model with retries and exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            return response.text
        except errors.APIError as e:
            last_error = e
            time.sleep(2 ** (attempt + 1))  # 2s, 4s
    raise last_error


def generate_content(prompt, model=DEFAULT_MODEL):
    """
    Gemini API call with retry + multi-model fallback logic.
    Tries the primary model first, then each fallback model in order,
    so a single deprecated/overloaded/quota-exhausted model doesn't block the request.
    """
    last_error = None

    try:
        return _try_model(model, prompt)
    except errors.APIError as e:
        last_error = e

    for fallback_model in FALLBACK_MODELS:
        if fallback_model == model:
            continue
        try:
            return _try_model(fallback_model, prompt)
        except errors.APIError as e:
            last_error = e

    raise Exception(f"Gemini API failed after retries and fallback: {last_error}")