import argparse
import logging

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
    response_text = model.invoke(prompt)

    sources = [doc.metadata.get("id") for doc, _score in results]
    logger.info("Response: %s", response_text)
    logger.info("Sources: %s", sources)
    return response_text


if __name__ == "__main__":
    main()
