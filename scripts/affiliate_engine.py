# scripts/affiliate_engine.py
#!/usr/bin/env python3
"""
Affiliate Engine — автоматична підстановка реферальних посилань у файли інструментів.
Використовує базу _data/affiliates.yml.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional

import yaml

# Додаємо корінь проєкту в sys.path для імпорту utils
sys.path.insert(0, str(Path(__file__).parent))
from utils import setup_logger, slugify

logger = setup_logger("affiliate_engine")

PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "_tools"
AFFILIATES_FILE = PROJECT_ROOT / "_data" / "affiliates.yml"
FRONTMATTER_DELIMITER = "---"


def load_affiliates() -> Dict[str, dict]:
    """Завантажує базу реферальних посилань з YAML-файлу."""
    if not AFFILIATES_FILE.exists():
        logger.warning(f"Файл {AFFILIATES_FILE} не знайдено. Створіть його.")
        return {}
    with open(AFFILIATES_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if data else {}


def extract_frontmatter(content: str) -> tuple[dict, str]:
    """
    Розбирає frontmatter і повертає (frontmatter_dict, body).
    Якщо frontmatter немає — повертає ({}, content).
    """
    lines = content.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return {}, content

    # Шукаємо другий роздільник
    end_index = None
    for i in range(1, len(lines)):
        if lines[i].strip() == FRONTMATTER_DELIMITER:
            end_index = i
            break

    if end_index is None:
        return {}, content

    frontmatter_text = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1:])

    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as e:
        logger.error(f"Помилка парсингу frontmatter: {e}")
        frontmatter = {}

    return frontmatter, body


def build_frontmatter_str(frontmatter: dict) -> str:
    """Перетворює словник frontmatter на рядок YAML з коректним форматуванням."""
    if not frontmatter:
        return ""
    # Використовуємо yaml.dump для гарантовано коректного формату
    return yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)


def process_tool_file(file_path: Path, affiliates: Dict[str, dict]) -> bool:
    """
    Обробляє один файл інструменту.
    Повертає True, якщо файл було змінено.
    """
    slug = file_path.stem  # ім'я файлу без .md

    with open(file_path, "r", encoding="utf-8") as f:
        original_content = f.read()

    frontmatter, body = extract_frontmatter(original_content)

    # Перевіряємо, чи є збіг за slug або за доменом (з поля website/link)
    affiliate_data = None
    if slug in affiliates:
        affiliate_data = affiliates[slug]
        logger.debug(f"Збіг за slug: {slug}")
    else:
        # Шукаємо за доменом у frontmatter
        website = frontmatter.get("website") or frontmatter.get("link") or ""
        if website:
            # Простий пошук: витягуємо домен (без протоколу та www)
            domain_match = re.search(r"(?:https?://)?(?:www\.)?([^/]+)", website)
            if domain_match:
                domain = domain_match.group(1)
                # Шукаємо в affiliates за ключем, який може бути доменом
                # Або проходимо по всіх ключах і перевіряємо, чи входить ключ у домен
                for key, data in affiliates.items():
                    if key in domain or domain in key:
                        affiliate_data = data
                        logger.debug(f"Збіг за доменом: {domain} -> {key}")
                        break

    # Оновлюємо frontmatter
    changed = False
    if affiliate_data:
        new_affiliate_url = affiliate_data.get("url")
        if frontmatter.get("affiliate_url") != new_affiliate_url:
            frontmatter["affiliate_url"] = new_affiliate_url
            changed = True
        if not frontmatter.get("affiliate_banner"):
            frontmatter["affiliate_banner"] = True
            changed = True
        # Можна також зберегти комісію для відображення
        if affiliate_data.get("commission"):
            frontmatter["affiliate_commission"] = affiliate_data.get("commission")
            changed = True
    else:
        # Видаляємо афілейтні поля, якщо вони були
        if "affiliate_url" in frontmatter:
            del frontmatter["affiliate_url"]
            changed = True
        if "affiliate_banner" in frontmatter:
            del frontmatter["affiliate_banner"]
            changed = True
        if "affiliate_commission" in frontmatter:
            del frontmatter["affiliate_commission"]
            changed = True

    if not changed:
        return False

    # Збираємо новий вміст
    new_frontmatter_str = build_frontmatter_str(frontmatter)
    new_content = f"{FRONTMATTER_DELIMITER}\n{new_frontmatter_str}{FRONTMATTER_DELIMITER}\n{body}"

    # Записуємо файл
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True


def main():
    """Основний цикл."""
    affiliates = load_affiliates()
    if not affiliates:
        logger.info("База афілейтів порожня. Нічого не робимо.")
        return

    if not TOOLS_DIR.exists():
        logger.error(f"Директорія {TOOLS_DIR} не існує.")
        return

    tool_files = list(TOOLS_DIR.glob("*.md"))
    logger.info(f"Знайдено {len(tool_files)} файлів інструментів.")

    modified_count = 0
    for file_path in tool_files:
        try:
            if process_tool_file(file_path, affiliates):
                modified_count += 1
                logger.info(f"Оновлено: {file_path.name}")
        except Exception as e:
            logger.error(f"Помилка обробки {file_path.name}: {e}")

    logger.info(f"Оброблено {len(tool_files)} файлів, змінено {modified_count}.")


if __name__ == "__main__":
    main()