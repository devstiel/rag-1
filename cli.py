import argparse
import logging

from settings import LOG_LEVEL


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
        from populate_database import main as populate_main

        populate_main(reset=args.reset)
        return

    if args.cmd == "query":
        from query_data import query_rag

        query_rag(args.query_text)
        return

    if args.cmd == "epub-to-md":
        from epub_to_md import run_cli

        run_cli(args.input, args.out, args.split)
        return


if __name__ == "__main__":
    main()
