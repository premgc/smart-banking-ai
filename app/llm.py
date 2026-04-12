from __future__ import annotations

import os
from typing import Tuple
from pathlib import Path

from dotenv import load_dotenv
from openai import AzureOpenAI

from app.retriever import AZURE_OPENAI_DEPLOYMENT


# =========================================================
# LOAD ENV (ROBUST)
# =========================================================
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


# =========================================================
# ENV VARIABLES
# =========================================================
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_API_VERSION = os.getenv(
    "AZURE_OPENAI_API_VERSION", "2024-12-01-preview"
)

REQUEST_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))


print("Using deployment:", AZURE_OPENAI_DEPLOYMENT)
# =========================================================
# VALIDATION
# =========================================================
def _validate_config():
    if not AZURE_OPENAI_ENDPOINT:
        raise RuntimeError("❌ AZURE_OPENAI_ENDPOINT is not set")

    if not AZURE_OPENAI_API_KEY:
        raise RuntimeError("❌ AZURE_OPENAI_API_KEY is not set")

    if not AZURE_OPENAI_CHAT_DEPLOYMENT:
        raise RuntimeError("❌ AZURE_OPENAI_CHAT_DEPLOYMENT is not set")


# =========================================================
# CLIENT (Singleton style)
# =========================================================
def get_openai_client() -> AzureOpenAI:
    _validate_config()

    return AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
    )


# =========================================================
# HEALTH CHECK
# =========================================================
def check_openai_health() -> Tuple[bool, str]:
    try:
        client = get_openai_client()

        response = client.chat.completions.create(
            model=AZURE_OPENAI_CHAT_DEPLOYMENT,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )

        return True, "✅ Azure OpenAI reachable"

    except Exception as e:
        return False, f"❌ Azure OpenAI error: {e}"


# =========================================================
# MAIN GENERATION FUNCTION
# =========================================================
def generate_response(prompt: str) -> str:
    if not prompt or not str(prompt).strip():
        raise ValueError("Prompt is empty")

    try:
        client = get_openai_client()

        response = client.chat.completions.create(
            model=AZURE_OPENAI_CHAT_DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a smart banking assistant. "
                        "Help users analyze their spending, detect patterns, "
                        "and provide financial insights clearly."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=800,
        )

        result = response.choices[0].message.content.strip()

        if not result:
            raise RuntimeError("Empty response from Azure OpenAI")

        return result

    except Exception as e:
        raise RuntimeError(f"❌ Azure OpenAI failed: {e}")