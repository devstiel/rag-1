import argparse
import logging
from pathlib import Path
import sys

# Ensure src/ is on sys.path for package imports when run as a script.
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rag1.settings import LOG_LEVEL


def _setup_logging():
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(levelname)s %(name)s: %(message)s",
    )


def main():
    _setup_logging()

    parser = argparse.ArgumentParser(prog="rag-1")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_pop = sub.add_parser("populate", help="Populate Chroma from PDFs")
    p_pop.add_argument("--reset", action="store_true", help="Reset the database")

    p_query = sub.add_parser("query", help="Query the RAG system")
    p_query.add_argument("query_text", type=str, help="The query text")

    p_epub = sub.add_parser("epub-to-md", help="Convert EPUB to Markdown")
    p_epub.add_argument("input", help="Path to .epub or folder with .epub")
    p_epub.add_argument("-o", "--out", default="md_out", help="Output folder")
    p_epub.add_argument("--split", action="store_true", help="Split per chapter")

    args = parser.parse_args()

    if args.cmd == "populate":
        from rag1.populate_database import main as populate_main

        populate_main(reset=args.reset)
        return

    if args.cmd == "query":
        from rag1.query_data import query_rag

        query_rag(args.query_text)
        return

    if args.cmd == "epub-to-md":
        from rag1.epub_to_md import run_cli

        run_cli(args.input, args.out, args.split)
        return


if __name__ == "__main__":
    main()
