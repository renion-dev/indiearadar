#!/usr/bin/env python3
"""
Programmatic Page Generator
Reads all YAML definitions from _data/programmatic/**/*.yml
and generates Markdown pages in pages/programmatic/
"""

from pathlib import Path
import yaml
import frontmatter
from datetime import datetime
import frontmatter
ROOT = Path(__file__).resolve().parent.parent
DEFINITIONS_DIR = ROOT / "_data" / "programmatic"
PAGES_DIR = ROOT / "pages" / "programmatic"
TOOLS_DIR = ROOT / "_tools"

def load_tools():
    tools = []
    for tool_file in TOOLS_DIR.glob("*.md"):
        try:
            post = frontmatter.load(tool_file)
            data = post.metadata
            if 'slug' not in data:
                print(f"Skipping {tool_file.name}: missing slug")
                continue
            tools.append(data)
        except Exception as e:
            print(f"⚠️ Error loading {tool_file}: {e}")
    return tools

def filter_tools(tools, tool_filters):
    filtered = tools.copy()
    for key, value in tool_filters.items():
        if key == "categories":
            filtered = [t for t in filtered if any(cat in t.get("categories", []) for cat in value)]
        elif key == "pricing":
            filtered = [t for t in filtered if t.get("pricing") == value]
    return filtered

def generate_page(definition_file):
    with open(definition_file, 'r', encoding='utf-8') as f:
        definition = yaml.safe_load(f)

    slug = definition_file.stem  # використовуємо ім'я файлу як slug
    title = definition.get('title', slug.replace('-', ' ').title())
    description = definition.get('description', '')
    tool_filters = definition.get('tool_filters', {})
    limit = definition.get('limit', 20)
    faq = definition.get('faq', [])
    category = definition.get('category', 'unknown')

    all_tools = load_tools()
    filtered = filter_tools(all_tools, tool_filters)
    limited = filtered[:limit]

    fm = {
        'layout': 'programmatic',
        'title': title,
        'description': description,
        'permalink': f'/{slug}/',
        'programmatic': True,
        'related_tools': [t.get('slug') for t in limited if t.get('slug')],
        'tool_count': len(limited),
        'category': category,
        'faq': faq,
        'last_modified': datetime.now().isoformat()
    }

    out_file = PAGES_DIR / f"{slug}.md"
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write("---\n")
        f.write(yaml.dump(fm, allow_unicode=True, sort_keys=False))
        f.write("---\n")

    print(f"✅ Generated: {out_file} ({len(limited)} tools)")

def main():
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    for def_file in DEFINITIONS_DIR.glob('**/*.yml'):
        generate_page(def_file)

if __name__ == "__main__":
    main()
