#!/usr/bin/env python3

from pathlib import Path
import yaml

PROGRAMMATIC_DIR = Path("_data/programmatic")
OUTPUT_DIR = Path("pages/programmatic")


def load_pages():
    pages = []

    for file in sorted(PROGRAMMATIC_DIR.glob("*.yml")):
        with open(file, "r", encoding="utf-8") as f:
            page = yaml.safe_load(f)

        page["_source"] = file.name
        pages.append(page)

    return pages


def render_markdown(page):
    return f"""---
layout: page
title: "{page['title']}"
permalink: /{page['slug']}/
programmatic: true
generated: true
---

# {page['title']}

> This page was generated automatically.

Programmatic SEO page.

Source: `{page['_source']}`
"""


def generate_page(page):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output = OUTPUT_DIR / f"{page['slug']}.md"

    output.write_text(
        render_markdown(page),
        encoding="utf-8",
    )

    print(f"Generated {output}")


def main():
    pages = load_pages()

    print(f"Loaded {len(pages)} page definitions")

    for page in pages:
        generate_page(page)


if __name__ == "__main__":
    main()
