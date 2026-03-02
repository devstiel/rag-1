import argparse
import logging
import os
import shutil

from langchain_community.document_loaders import DirectoryLoader, PyPDFDirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma

from get_embedding_function import get_embedding_function
from settings import (
    CHROMA_PATH,
    DATA_PATH,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    LOG_LEVEL,
    MAX_EMBED_CHARS,
)

logger = logging.getLogger(__name__)


def main(reset: bool = False):
    if reset:
        logger.info("Clearing database")
        clear_database()

    documents = load_documents()
    chunks = split_documents(documents)
    add_to_chroma(chunks)


def load_documents():
    documents: list[Document] = []

    pdf_dir = os.path.join(DATA_PATH, "pdf")
    if os.path.isdir(pdf_dir):
        pdf_loader = PyPDFDirectoryLoader(pdf_dir)
        pdf_docs = pdf_loader.load()
        logger.info("Loaded %s PDF docs from %s", len(pdf_docs), pdf_dir)
        documents.extend(pdf_docs)
    else:
        logger.info("No PDF folder found at %s", pdf_dir)

    md_dir = os.path.join(DATA_PATH, "md")
    if os.path.isdir(md_dir):
        md_loader = DirectoryLoader(
            md_dir,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        md_docs = md_loader.load()
        logger.info("Loaded %s Markdown docs from %s", len(md_docs), md_dir)
        documents.extend(md_docs)
    else:
        logger.info("No Markdown folder found at %s", md_dir)

    txt_loader = DirectoryLoader(
        DATA_PATH,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    txt_docs = txt_loader.load()
    if txt_docs:
        logger.info("Loaded %s text docs from %s", len(txt_docs), DATA_PATH)
        documents.extend(txt_docs)

    if not documents:
        logger.warning("No documents found in data folder")

    return documents


def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)
    return _trim_chunks(chunks)


def _trim_chunks(chunks: list[Document]) -> list[Document]:
    if MAX_EMBED_CHARS <= 0:
        return chunks

    trimmed = 0
    out: list[Document] = []
    for doc in chunks:
        text = doc.page_content
        if text and len(text) > MAX_EMBED_CHARS:
            text = text[:MAX_EMBED_CHARS]
            trimmed += 1
        out.append(Document(page_content=text, metadata=doc.metadata))

    if trimmed:
        logger.info("Trimmed %s chunks to %s chars for embeddings", trimmed, MAX_EMBED_CHARS)

    return out


def add_to_chroma(chunks: list[Document]):
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function()
    )

    chunks_with_ids = calculate_chunk_ids(chunks)

    existing_items = db.get(include=[])
    existing_ids = set(existing_items["ids"])
    logger.info("Number of existing documents in DB: %s", len(existing_ids))

    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if new_chunks:
        logger.info("Adding new documents: %s", len(new_chunks))
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        
        # --- NEW BATCHING LOGIC ---
        # Send chunks to Ollama in batches of 100 to prevent 400 Errors
        batch_size = 100 
        for i in range(0, len(new_chunks), batch_size):
            batch_chunks = new_chunks[i : i + batch_size]
            batch_ids = new_chunk_ids[i : i + batch_size]
            
            logger.info("Processing batch %s to %s...", i, i + len(batch_chunks))
            db.add_documents(batch_chunks, ids=batch_ids)
            
        logger.info("✅ Successfully finished adding all batches!")
    else:
        logger.info("No new documents to add")


def calculate_chunk_ids(chunks):
    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        chunk.metadata["id"] = chunk_id

    return chunks


def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)


if __name__ == "__main__":
    logging.basicConfig(level=LOG_LEVEL, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()
    main(reset=args.reset)
