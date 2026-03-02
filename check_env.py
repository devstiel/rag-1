from __future__ import annotations

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from settings import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL, OLLAMA_LLM_MODEL

logger = logging.getLogger(__name__)


def _get_available_models() -> set[str]:
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    req = Request(url, method="GET")
    try:
        with urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (URLError, HTTPError) as exc:
        raise SystemExit(
            f"Ollama not reachable at {OLLAMA_BASE_URL}. "
            f"Start Ollama and try again. Error: {exc}"
        ) from exc

    models = {m.get("name") for m in data.get("models", []) if m.get("name")}
    # Normalize by also allowing base names without tag (e.g., "mistral" for "mistral:latest")
    base_names = {name.split(":", 1)[0] for name in models}
    return models | base_names


def preflight_check() -> None:
    logger.debug("Running Ollama preflight check")
    models = _get_available_models()
    missing = [m for m in [OLLAMA_LLM_MODEL, OLLAMA_EMBED_MODEL] if m not in models]
    if missing:
        missing_list = ", ".join(missing)
        available_list = ", ".join(sorted(models)) or "(none)"
        raise SystemExit(
            "Missing Ollama model(s): "
            f"{missing_list}. Available models: {available_list}. "
            "Pull the model(s) or update environment variables."
        )
