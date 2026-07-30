#!/usr/bin/env python3
"""
Виправлення рейтингів у файлах _tools/*.md на основі votes.
"""

import os
import sys
import re
import json
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import logger

PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "_tools"

def parse_frontmatter(content):
    """Парсить YAML frontmatter з markdown файлу."""
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not match:
        return {}, content
    frontmatter_text = match.group(1)
    body = match.group(2)
    # Спрощений парсинг YAML
    frontmatter = {}
    lines = frontmatter_text.split('\n')
    current_key = None
    current_list = []
    for line in lines:
        if not line.strip():
            continue
        if line.startswith('  - '):
            if current_key:
                current_list.append(line[4:].strip())
            continue
        if ': ' in line:
            if current_key and current_list:
                frontmatter[current_key] = current_list
            key, value = line.split(': ', 1)
            if value.startswith('"') and value.endswith('"'):
                value = json.loads(value)
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            if value == '[' and line.endswith(':'):
                current_key = key
                current_list = []
                continue
            elif value == '[]':
                frontmatter[key] = []
            else:
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except:
                    pass
                frontmatter[key] = value
        elif line.endswith(':'):
            current_key = line[:-1].strip()
            current_list = []
    if current_key and current_list:
        frontmatter[current_key] = current_list
    return frontmatter, body

def generate_rating(votes):
    """Обчислює рейтинг на основі голосів (з розкидом)."""
    if votes < 10:
        rating = 3.0
    elif votes < 50:
        rating = 3.5 + (votes - 10) / 40 * 0.8
    elif votes < 150:
        rating = 4.3 + (votes - 50) / 100 * 0.5
    else:
        rating = 5.0
    rating = rating + random.uniform(-0.2, 0.2)
    return round(max(1.0, min(5.0, rating)), 1)

def fix_file(filepath):
    """Оновлює рейтинг у файлі."""
    content = filepath.read_text(encoding='utf-8')
    frontmatter, body = parse_frontmatter(content)
    if 'votes' not in frontmatter:
        logger.info(f"⏭️ Пропускаємо {filepath.name}: немає votes")
        return False
    votes = frontmatter.get('votes')
    if not isinstance(votes, (int, float)):
        logger.info(f"⏭️ Пропускаємо {filepath.name}: votes не число")
        return False
    new_rating = generate_rating(votes)
    if 'rating' in frontmatter and abs(frontmatter['rating'] - new_rating) < 0.01:
        return False
    frontmatter['rating'] = new_rating
    # Перебудовуємо frontmatter
    lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            if isinstance(value, str):
                value = json.dumps(value)
            lines.append(f"{key}: {value}")
    lines.append("---")
    new_content = "\n".join(lines) + "\n\n" + body
    filepath.write_text(new_content, encoding='utf-8')
    logger.info(f"✅ Оновлено {filepath.name}: rating {new_rating} (votes {votes})")
    return True

def main():
    logger.info("🚀 Виправлення рейтингів у _tools/")
    fixed = 0
    for filepath in TOOLS_DIR.glob("*.md"):
        if fix_file(filepath):
            fixed += 1
    logger.info(f"🎉 Готово! Оновлено {fixed} файлів.")

if __name__ == "__main__":
    main()
