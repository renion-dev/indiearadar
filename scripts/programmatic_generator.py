#!/usr/bin/env python3

from pathlib import Path
import yaml


PROGRAMMATIC_DIR = Path("_data/programmatic")


def load_pages():
    pages = []

    for file in sorted(PROGRAMMATIC_DIR.glob("*.yml")):
        with open(file, "r", encoding="utf-8") as f:
            page = yaml.safe_load(f)

        page["_source"] = file.name
        pages.append(page)

    return pages


def main():
    pages = load_pages()

    print(f"Loaded {len(pages)} programmatic page definitions\n")

    for page in pages:
        print(
            f"- {page['title']} "
            f"({page['slug']}) "
            f"[{page['_source']}]"
        )


if __name__ == "__main__":
    main()
