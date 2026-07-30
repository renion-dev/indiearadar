#!/usr/bin/env python3

from pathlib import Path
import yaml

PROGRAMMATIC_DIR = Path("_data/programmatic")
TOOLS_DIR = Path("_tools")
OUTPUT_DIR = Path("pages/programmatic")


def load_pages():
    pages = []

    for file in sorted(PROGRAMMATIC_DIR.glob("*.yml")):
        with open(file, "r", encoding="utf-8") as f:
            page = yaml.safe_load(f)

        page["_source"] = file.name
        pages.append(page)

    return pages


def parse_front_matter(path: Path):
    text = path.read_text(encoding="utf-8")

    if not text.startswith("---"):
        return None

    parts = text.split("---", 2)

    if len(parts) < 3:
        return None

    return yaml.safe_load(parts[1])


def load_tools():
    tools = []

    for file in sorted(TOOLS_DIR.glob("*.md")):
        data = parse_front_matter(file)

        if not data:
            print(f"Skipping {file}: no front matter")
            continue

        if "slug" not in data:
            print(f"Missing slug: {file}")
            print(data)
            continue

        data["_source"] = file.name
        tools.append(data)

    return tools


def filter_tools(page, tools):
    filters = page.get("tool_filters", {})
    categories = set(filters.get("categories", []))

    if not categories:
        return tools

    matched = []

    for tool in tools:
        if tool.get("category") in categories:
            matched.append(tool)

    return matched


def render_markdown(page, tools):

    related_tools = "\n".join(
        f"  - {tool['slug']}"
        for tool in tools
    )

    return f"""---
layout: programmatic
title: "{page['title']}"
permalink: /{page['slug']}/
programmatic: true
generated: true

related_tools:
{related_tools}
---

## Recommended AI Tools

Automatically selected tools for this category.
"""


def generate_page(page, tools):

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output = OUTPUT_DIR / f"{page['slug']}.md"

    output.write_text(
        render_markdown(page, tools),
        encoding="utf-8",
    )

    print(
        f"Generated {output} ({len(tools)} tools)"
    )


def main():

    pages = load_pages()

    tools = load_tools()

    print(f"Loaded {len(tools)} tools")
    print(f"Loaded {len(pages)} page definitions\n")

    for page in pages:

        matched = filter_tools(page, tools)

        print(
            f"{page['title']}: {len(matched)} matching tools"
        )

        generate_page(page, matched)


if __name__ == "__main__":
    main()
