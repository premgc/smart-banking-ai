from __future__ import annotations

import os
import requests
from typing import Tuple


# =========================================================
# ENV VARIABLES (SET IN AZURE APP SERVICE)
# =========================================================
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_API_VERSION = os.getenv(
    "AZURE_OPENAI_API_VERSION", "2024-02-15-preview"
)

REQUEST_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))


# =========================================================
# VALIDATION
# =========================================================
def _validate_config():
    if not AZURE_OPENAI_ENDPOINT:
        raise RuntimeError("AZURE_OPENAI_ENDPOINT is not set")

    if not AZURE_OPENAI_API_KEY:
        raise RuntimeError("AZURE_OPENAI_API_KEY is not set")

    if not AZURE_OPENAI_DEPLOYMENT:
        raise RuntimeError("AZURE_OPENAI_DEPLOYMENT is not set")


# =========================================================
# HEALTH CHECK
# =========================================================
def check_openai_health() -> Tuple[bool, str]:
    try:
        _validate_config()

        url = (
            f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/"
            f"{AZURE_OPENAI_DEPLOYMENT}/chat/completions"
            f"?api-version={AZURE_OPENAI_API_VERSION}"
        )

        headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_OPENAI_API_KEY,
        }

        payload = {
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5,
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=10,
        )

        if response.status_code == 200:
            return True, "Azure OpenAI reachable"

        return False, f"Azure OpenAI error: {response.status_code} {response.text}"

    except Exception as e:
        return False, f"Azure OpenAI not reachable: {e}"


# =========================================================
# MAIN GENERATION FUNCTION
# =========================================================
def generate_response(prompt: str) -> str:
    if not prompt or not str(prompt).strip():
        raise ValueError("Prompt is empty.")

    _validate_config()

    url = (
        f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/"
        f"{AZURE_OPENAI_DEPLOYMENT}/chat/completions"
        f"?api-version={AZURE_OPENAI_API_VERSION}"
    )

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_API_KEY,
    }

    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a smart banking assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 800,
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

    except requests.exceptions.Timeout as e:
        raise RuntimeError(
            f"Azure OpenAI request timed out after {REQUEST_TIMEOUT}s"
        ) from e

    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            "Unable to connect to Azure OpenAI. Check endpoint/network."
        ) from e

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Azure OpenAI request failed: {e}") from e

    if response.status_code != 200:
        raise RuntimeError(
            f"Azure OpenAI returned {response.status_code}: {response.text}"
        )

    try:
        data = response.json()
    except ValueError as e:
        raise RuntimeError("Azure OpenAI returned invalid JSON") from e

    try:
        result = (
            data["choices"][0]["message"]["content"]
            .strip()
        )
    except Exception:
        raise RuntimeError(f"Unexpected response format: {data}")

    if not result:
        raise RuntimeError("Empty response from Azure OpenAI")

    return result