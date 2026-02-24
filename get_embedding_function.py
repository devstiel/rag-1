from langchain_ollama import OllamaEmbeddings

def get_embedding_function():
    return OllamaEmbeddings(
        model="all-minilm",          # atau "embeddinggemma" / "qwen3-embedding"
        base_url="http://localhost:11434",
    )