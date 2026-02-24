from __future__ import annotations

import argparse
import re
from pathlib import Path

from ebooklib import epub
from bs4 import BeautifulSoup
from markdownify import markdownify as md


def slugify(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s_-]+", "-", name)
    return name.strip("-") or "book"


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    # Buang script/style
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Convert <br> jadi newline biar rapi
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # Ambil body kalau ada, biar nggak kebawa head dll
    body = soup.body if soup.body else soup
    return str(body)


def epub_to_markdown(epub_path: Path, out_dir: Path, split_chapters: bool = False) -> Path:
    book = epub.read_epub(str(epub_path))

    title = book.get_metadata("DC", "title")
    title = title[0][0] if title else epub_path.stem
    base_name = slugify(title)

    out_dir.mkdir(parents=True, exist_ok=True)

    # Ambil urutan spine supaya babnya berurutan
    spine_ids = [item[0] for item in book.spine if isinstance(item, tuple)]
    id_to_item = {it.get_id(): it for it in book.get_items()}

    chapters = []
    for item_id in spine_ids:
        it = id_to_item.get(item_id)
        if not it:
            continue
        if it.get_type() == 9:  # ebooklib.ITEM_DOCUMENT = 9
            html = it.get_content().decode("utf-8", errors="ignore")
            chapters.append((it.get_name(), html))

    if not chapters:
        # Fallback: ambil semua dokumen
        for it in book.get_items():
            if it.get_type() == 9:
                html = it.get_content().decode("utf-8", errors="ignore")
                chapters.append((it.get_name(), html))

    if split_chapters:
        book_folder = out_dir / base_name
        book_folder.mkdir(parents=True, exist_ok=True)

        index_lines = [f"# {title}\n", "\n## Chapters\n"]
        for i, (name, html) in enumerate(chapters, start=1):
            cleaned = clean_html(html)
            md_text = md(cleaned, heading_style="ATX")
            chapter_file = book_folder / f"{i:03d}-{slugify(Path(name).stem)}.md"
            chapter_file.write_text(md_text.strip() + "\n", encoding="utf-8")
            index_lines.append(f"- [{chapter_file.stem}]({chapter_file.name})\n")

        index_path = book_folder / "README.md"
        index_path.write_text("".join(index_lines), encoding="utf-8")
        return book_folder

    # Gabung jadi satu file .md
    parts = [f"# {title}\n"]
    for i, (name, html) in enumerate(chapters, start=1):
        cleaned = clean_html(html)
        md_text = md(cleaned, heading_style="ATX")
        parts.append(f"\n\n## Chapter {i}\n")
        parts.append(md_text.strip())

    out_path = out_dir / f"{base_name}.md"
    out_path.write_text("\n".join(parts).strip() + "\n", encoding="utf-8")
    return out_path


def main():
    ap = argparse.ArgumentParser(description="Convert EPUB to Markdown (.md)")
    ap.add_argument("input", help="Path ke file .epub atau folder yang berisi .epub")
    ap.add_argument("-o", "--out", default="md_out", help="Folder output (default: md_out)")
    ap.add_argument("--split", action="store_true", help="Pisah output per chapter (folder)")
    args = ap.parse_args()

    inp = Path(args.input)
    out_dir = Path(args.out)

    if inp.is_dir():
        epubs = sorted(inp.rglob("*.epub"))
        if not epubs:
            raise SystemExit(f"Tidak ada .epub di folder: {inp}")
        for p in epubs:
            result = epub_to_markdown(p, out_dir, split_chapters=args.split)
            print(f"✅ {p.name} -> {result}")
    else:
        if inp.suffix.lower() != ".epub":
            raise SystemExit("Input harus .epub atau folder berisi .epub")
        result = epub_to_markdown(inp, out_dir, split_chapters=args.split)
        print(f"✅ {inp.name} -> {result}")


if __name__ == "__main__":
    main()