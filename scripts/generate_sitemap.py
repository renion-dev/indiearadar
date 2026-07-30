#!/usr/bin/env python3
"""
Генератор sitemap.xml для Indie AI Radar
Сканує _site/ і будує sitemap з урахуванням пріоритетів.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom import minidom

SITE_URL = "https://indieairadar.com"
SITE_DIR = Path("_site")
OUTPUT_FILE = Path("_site/sitemap.xml")

# Пріоритети за типами сторінок
PRIORITY_MAP = {
    "/": 1.0,
    "/best-ai-tools-for-": 0.9,      # програмні сторінки
    "/tools/": 0.8,                   # сторінки інструментів
    "/blog/": 0.7,                    # пости
    "/tags/": 0.5,
    "/categories/": 0.5,
}

CHANGEFREQ_MAP = {
    "/": "daily",
    "/best-ai-tools-for-": "daily",
    "/tools/": "weekly",
    "/blog/": "weekly",
    "/tags/": "monthly",
    "/categories/": "monthly",
}

def get_priority(url: str) -> float:
    for pattern, priority in PRIORITY_MAP.items():
        if pattern in url:
            return priority
    return 0.5

def get_changefreq(url: str) -> str:
    for pattern, freq in CHANGEFREQ_MAP.items():
        if pattern in url:
            return freq
    return "monthly"

def get_lastmod(filepath: Path) -> str:
    mtime = filepath.stat().st_mtime
    return datetime.fromtimestamp(mtime).isoformat()

def generate_sitemap():
    if not SITE_DIR.exists():
        print("❌ _site/ не знайдено. Спочатку запустіть jekyll build")
        return

    root = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    # Рекурсивно шукаємо всі .html файли (крім тих, що у виключених папках)
    exclude = {"assets", "feed.xml", "robots.txt", "sitemap.xml"}
    html_files = []
    for filepath in SITE_DIR.rglob("*.html"):
        rel_path = filepath.relative_to(SITE_DIR)
        if any(part in exclude for part in rel_path.parts):
            continue
        html_files.append(filepath)

    for filepath in sorted(html_files):
        rel_path = filepath.relative_to(SITE_DIR)
        url_path = "/" + str(rel_path).replace("index.html", "").replace("\\", "/")
        if url_path.endswith("/") is False and not url_path.endswith(".html"):
            url_path += "/"
        # Якщо це не головна, нормалізуємо
        if url_path == "//":
            url_path = "/"

        full_url = SITE_URL + url_path

        url_elem = ET.SubElement(root, "url")
        loc = ET.SubElement(url_elem, "loc")
        loc.text = full_url

        lastmod = ET.SubElement(url_elem, "lastmod")
        lastmod.text = get_lastmod(filepath)

        changefreq = ET.SubElement(url_elem, "changefreq")
        changefreq.text = get_changefreq(url_path)

        priority = ET.SubElement(url_elem, "priority")
        priority.text = f"{get_priority(url_path):.1f}"

    # Додаємо головну окремо, якщо не потрапила
    index_path = SITE_DIR / "index.html"
    if index_path.exists() and not any(elem.find("loc").text == SITE_URL + "/" for elem in root.findall("url")):
        url_elem = ET.SubElement(root, "url")
        loc = ET.SubElement(url_elem, "loc")
        loc.text = SITE_URL + "/"
        lastmod = ET.SubElement(url_elem, "lastmod")
        lastmod.text = get_lastmod(index_path)
        changefreq = ET.SubElement(url_elem, "changefreq")
        changefreq.text = "daily"
        priority = ET.SubElement(url_elem, "priority")
        priority.text = "1.0"

    # Гарне форматування XML
    rough_string = ET.tostring(root, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty = reparsed.toprettyxml(indent="  ")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(pretty.split("<?xml", 1)[-1].strip())

    print(f"✅ Sitemap згенеровано: {OUTPUT_FILE} (знайдено {len(html_files)} сторінок)")

if __name__ == "__main__":
    generate_sitemap()