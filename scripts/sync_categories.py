#!/usr/bin/env python3
"""
Автоматично додає категорії з інструментів у seed, якщо їх немає.
"""

import yaml
from pathlib import Path

TOOLS_DIR = Path("_tools")
SEED_FILE = Path("_data/seed/professions/professions.yml")

# Зчитуємо всі категорії з інструментів
categories = set()
for file in TOOLS_DIR.glob("*.md"):
    content = file.read_text()
    if "category:" in content:
        for line in content.split("\n"):
            if line.strip().startswith("category:"):
                cat = line.split(":", 1)[1].strip().strip('"')
                if cat and cat != "productivity":
                    categories.add(cat)

# Зчитуємо поточний seed
seed_data = yaml.safe_load(SEED_FILE.read_text())
existing_slugs = {item["slug"] for item in seed_data["items"]}

# Додаємо нові категорії
added = 0
for cat in sorted(categories):
    if cat not in existing_slugs:
        seed_data["items"].append({
            "slug": cat,
            "title": cat.title(),
            "description": f"Best AI tools for {cat}.",
            "tool_filters": {"categories": [cat]},
            "limit": 20
        })
        added += 1

if added:
    SEED_FILE.write_text(yaml.dump(seed_data, allow_unicode=True, sort_keys=False))
    print(f"Додано {added} нових категорій")
else:
    print("Нових категорій немає")
