import logging

from langchain_ollama import OllamaEmbeddings

from settings import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL

logger = logging.getLogger(__name__)


def get_embedding_function():
    logger.debug("Using embedding model=%s base_url=%s", OLLAMA_EMBED_MODEL, OLLAMA_BASE_URL)
    return OllamaEmbeddings(
        model=OLLAMA_EMBED_MODEL,
        base_url=OLLAMA_BASE_URL,
    )
