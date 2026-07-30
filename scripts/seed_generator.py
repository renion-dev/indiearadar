#!/usr/bin/env python3

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent

SEED = ROOT / "_data" / "seed" / "professions" / "professions.yml"
OUTPUT = ROOT / "_data" / "programmatic" / "best-tools" / "professions"

OUTPUT.mkdir(parents=True, exist_ok=True)

data = yaml.safe_load(SEED.read_text())

count = 0

for item in data["items"]:

    page = {
        "title": f"Best AI Tools for {item['title']}",
        "slug": f"best-ai-tools-for-{item['slug']}",
        "description": item["description"],
        "tool_filters": item["tool_filters"],
        "limit": item.get("limit", 20),
    }

    outfile = OUTPUT / f"{item['slug']}.yml"

    outfile.write_text(
        yaml.safe_dump(page, sort_keys=False, allow_unicode=True)
    )

    count += 1

print(f"Generated {count} page definitions")
