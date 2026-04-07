from __future__ import annotations

import requests

from config.settings import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_TIMEOUT


def get_ollama_url() -> str:
    return f'{OLLAMA_HOST}/api/generate'


def check_ollama_health() -> tuple[bool, str]:
    try:
        response = requests.get(OLLAMA_HOST, timeout=5)
        if response.status_code < 500:
            return True, 'Ollama reachable'
        return False, f'Ollama unhealthy: HTTP {response.status_code}'
    except requests.RequestException as e:
        return False, f'Ollama not reachable: {e}'


def generate_response(prompt: str) -> str:
    if not prompt or not str(prompt).strip():
        raise ValueError('Prompt is empty.')

    payload = {
        'model': OLLAMA_MODEL,
        'prompt': prompt,
        'stream': False,
    }

    try:
        response = requests.post(
            get_ollama_url(),
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        )
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            'Unable to connect to Ollama. Start Ollama with: ollama serve'
        ) from e
    except requests.exceptions.Timeout as e:
        raise RuntimeError(
            f'Ollama request timed out after {OLLAMA_TIMEOUT} seconds.'
        ) from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f'Ollama request failed: {e}') from e

    if response.status_code != 200:
        raise RuntimeError(
            f'Ollama returned status {response.status_code}: {response.text}'
        )

    try:
        data = response.json()
    except ValueError as e:
        raise RuntimeError('Ollama returned invalid JSON.') from e

    result = str(data.get('response', '')).strip()
    if not result:
        raise RuntimeError(f'Empty response from Ollama. Raw response: {data}')

    return result
