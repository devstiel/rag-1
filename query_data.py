import argparse
import logging
import sys
import threading
import time

from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

from check_env import preflight_check
from get_embedding_function import get_embedding_function
from settings import CHROMA_PATH, LOG_LEVEL, OLLAMA_BASE_URL, OLLAMA_LLM_MODEL

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""


def main():
    logging.basicConfig(level=LOG_LEVEL, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    query_rag(args.query_text)


def query_rag(query_text: str):
    preflight_check()

    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=get_embedding_function(),
    )

    t0 = time.perf_counter()
    results = db.similarity_search_with_score(query_text, k=5)
    if not results:
        logger.warning("No results found")
        return ""

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE).format(
        context=context_text,
        question=query_text,
    )

    model = OllamaLLM(model=OLLAMA_LLM_MODEL, base_url=OLLAMA_BASE_URL)

    stop_event = threading.Event()
    spinner_thread = threading.Thread(
        target=_spinner,
        args=("Generating answer... ", stop_event),
        daemon=True,
    )
    spinner_thread.start()
    try:
        response_text = model.invoke(prompt)
    finally:
        stop_event.set()
        spinner_thread.join(timeout=1)
        _clear_line()

    sources = [doc.metadata.get("id") for doc, _score in results]
    logger.info("Query time: %.2fs", time.perf_counter() - t0)
    logger.info("Response: %s", response_text)
    logger.info("Sources: %s", sources)
    return response_text


def _spinner(message: str, stop_event: threading.Event) -> None:
    frames = "|/-\\"
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{message}{frames[idx % len(frames)]}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)


def _clear_line() -> None:
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
