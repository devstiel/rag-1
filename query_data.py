import argparse
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

from get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    query_rag(args.query_text)


def query_rag(query_text: str):
    # Load DB
    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=get_embedding_function(),
    )

    # Retrieve
    results = db.similarity_search_with_score(query_text, k=5)
    if not results:
        print("No results found.")
        return ""

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE).format(
        context=context_text,
        question=query_text,
    )

    # LLM (Ollama)
    model = OllamaLLM(model="mistral")  # make sure you've pulled it
    response_text = model.invoke(prompt)

    sources = [doc.metadata.get("id") for doc, _score in results]
    print(f"Response: {response_text}\nSources: {sources}")
    return response_text


if __name__ == "__main__":
    main()