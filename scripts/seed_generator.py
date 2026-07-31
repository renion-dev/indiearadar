#!/usr/bin/env python3
"""
Seed Generator - creates programmatic definitions from ALL seed data.
Scans _data/seed/**/*.yml and generates definitions in _data/programmatic/<category>/
"""

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = ROOT / "_data" / "seed"
PROGRAMMATIC_DIR = ROOT / "_data" / "programmatic"

def process_seed_file(seed_file):
    """Process a single seed YAML file and generate programmatic definitions."""
    with open(seed_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not data or 'items' not in data:
        print(f"⚠️ No 'items' in {seed_file}, skipping.")
        return

    # Визначаємо категорію — назва батьківської папки
    category = seed_file.parent.name  # e.g., professions, industries, pricing
    print(f"📂 Processing category: {category}")

    for item in data['items']:
        slug = item.get('slug')
        if not slug:
            print(f"⚠️ Item without slug in {seed_file}, skipping.")
            continue

        # Папка призначення: _data/programmatic/<category>/
        out_dir = PROGRAMMATIC_DIR / category
        out_dir.mkdir(parents=True, exist_ok=True)

        out_file = out_dir / f"{slug}.yml"

        # Формуємо визначення сторінки
        definition = {
            'title': item.get('title'),
            'description': item.get('description'),
            'tool_filters': item.get('tool_filters', {}),
            'limit': item.get('limit', 20),
            'faq': item.get('faq', []),
            'category': category  # додаємо категорію для шаблону
        }

        with open(out_file, 'w', encoding='utf-8') as f:
            yaml.dump(definition, f, allow_unicode=True, sort_keys=False)

        print(f"✅ Generated: {out_file}")

def main():
    # Рекурсивно шукаємо всі .yml файли в _data/seed/
    seed_files = list(SEED_DIR.glob('**/*.yml'))
    if not seed_files:
        print("⚠️ No seed files found in _data/seed/")
        return

    print(f"📂 Found {len(seed_files)} seed files.")
    for seed_file in seed_files:
        process_seed_file(seed_file)

    print("✅ All definitions generated successfully.")

if __name__ == "__main__":
    main()
