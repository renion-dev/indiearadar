#!/usr/bin/env python3
"""
blog_generator.py — Автоматична генерація блог-постів у заданому ритмі.
Комбінує заздалегідь визначені теми з AI-покращенням.
Запускається кожні 2 години через GitHub Actions.
"""

import os
import sys
import random
import json
import time
import yaml
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Імпорт з utils
sys.path.insert(0, str(Path(__file__).parent))
from utils import logger, retry, slugify, write_file
from og_image import generate_og_image

PROJECT_ROOT = Path(__file__).parent.parent
POSTS_DIR = PROJECT_ROOT / "_posts"
THEMES_FILE = PROJECT_ROOT / "_data" / "blog_themes.yml"

# Мінімальний інтервал між постами (години)
MIN_INTERVAL_HOURS = 4
# Випадкова затримка перед публікацією (хвилини)
RANDOM_DELAY_MIN = 0
RANDOM_DELAY_MAX = 10

# Час публікації щотижневого дайджесту (п'ятниця 16:00)
DIGEST_DAY = 4  # Friday (0=Monday)
DIGEST_HOUR = 16
DIGEST_MINUTE = 0


def get_last_post_time():
    """Повертає datetime останнього посту з _posts/ або None."""
    posts = sorted(POSTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not posts:
        return None
    return datetime.fromtimestamp(posts[0].stat().st_mtime)


def should_publish(now):
    """Визначає, чи потрібно публікувати пост зараз."""
    last_time = get_last_post_time()
    if last_time is None:
        return True

    diff = now - last_time
    if diff.total_seconds() < MIN_INTERVAL_HOURS * 3600:
        logger.info(f"⏳ Last post was {diff.total_seconds()/3600:.1f} hours ago. Need {MIN_INTERVAL_HOURS}h. Skipping.")
        return False

    # Перевіряємо, чи це п'ятниця і час ≥ 16:00
    if now.weekday() == DIGEST_DAY and now.hour >= DIGEST_HOUR:
        # Перевіряємо, чи вже був дайджест цього тижня
        week_start = now - timedelta(days=now.weekday())
        digest_exists = any(
            p.name.startswith(f"{now.strftime('%Y-%m-%d')}-weekly-digest") for p in POSTS_DIR.glob("*.md")
        )
        if not digest_exists:
            logger.info("📅 Time for weekly digest!")
            return True
        else:
            logger.info("📅 Weekly digest already published this week.")
            return False

    # Якщо минуло ≥4 години і не час дайджесту — публікуємо звичайний пост
    return True


def load_themes():
    """Завантажує теми з YAML-файлу."""
    if not THEMES_FILE.exists():
        logger.warning(f"Themes file not found: {THEMES_FILE}. Using fallback.")
        return [
            {"title": "How to Build an AI-Powered Side Project for Free", "category": "tutorial", "tags": ["tutorial", "ai"]},
            {"title": "The Best AI Tools for Indie Hackers", "category": "review", "tags": ["review", "tools"]},
        ]
    with open(THEMES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def enhance_topic_with_ai(base_title, category):
    """Використовує Gemini для покращення теми (зробити більш актуальною/конкретною)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return base_title

    prompt = f"""
Given the blog topic base: "{base_title}" (category: {category}),
suggest a more specific, engaging, and timely version of this topic for indie hackers and solopreneurs.
Make it sound like a clickable blog post title.
Return only the new title, without any additional text or explanation.
"""
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.9, "maxOutputTokens": 100}
            },
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        new_title = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Якщо Gemini повернула порожній рядок або занадто довгий — залишаємо базовий
        if new_title and len(new_title) < 120:
            return new_title
        return base_title
    except Exception as e:
        logger.warning(f"AI enhancement failed: {e}. Using base title.")
        return base_title


@retry(max_retries=3, backoff_factor=2.0)
def generate_post_content(title, category):
    """Генерує контент поста за допомогою Gemini."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not set.")
        return None

    prompt = f"""
Write a blog post in the style of Indie AI Radar — a blog for indie hackers and solopreneurs.

Title: {title}
Category: {category}

Style guidelines:
- Friendly, approachable tone with a touch of humor
- Practical, actionable advice with real examples
- Use markdown formatting (## headings, bullet lists, **bold**)
- Include a short introduction, main body (2-3 sections), and conclusion
- Keep it between 350-500 words
- End with a call-to-action: "Subscribe to our weekly newsletter for more indie AI tools."

Make it engaging, valuable, and written for an audience of independent developers and makers.
"""
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.8, "maxOutputTokens": 2048}
            },
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        # Видаляємо можливі зайві рядки з промпту
        return text.strip()
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return None


def save_post(title, content, category, tags, date=None):
    """Зберігає пост у _posts/ з фронтматтером."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(title)
    filename = f"{date}-{slug}.md"
    filepath = POSTS_DIR / filename

    # Генеруємо OG-зображення
    og_path = generate_og_image(title, slug)

    frontmatter = {
        "title": title,
        "date": date,
        "layout": "post",
        "category": category,
        "tags": tags,
        "image": og_path,
    }

    yaml_lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, list):
            yaml_lines.append(f"{k}:")
            for item in v:
                yaml_lines.append(f"  - {item}")
        else:
            if isinstance(v, str):
                v = json.dumps(v)
            yaml_lines.append(f"{k}: {v}")
    yaml_lines.append("---")

    full_content = "\n".join(yaml_lines) + "\n\n" + content
    write_file(str(filepath), full_content)
    logger.info(f"✅ Post saved: {filepath}")
    return filepath


def main():
    now = datetime.now()
    logger.info(f"🕒 Checking if we should publish at {now}")

    if not should_publish(now):
        logger.info("⏭️  Skipping this cycle.")
        return 0

    # Випадкова затримка перед публікацією (щоб час не був однаковим)
    delay_seconds = random.randint(RANDOM_DELAY_MIN * 60, RANDOM_DELAY_MAX * 60)
    if delay_seconds > 0:
        logger.info(f"⏳ Waiting {delay_seconds//60} minutes before publishing...")
        time.sleep(delay_seconds)

    # Визначаємо, чи це щотижневий дайджест
    is_digest = (now.weekday() == DIGEST_DAY and now.hour >= DIGEST_HOUR)

    if is_digest:
        title = "Weekly AI Tools Digest — Top Tools for Indie Hackers"
        category = "digest"
        tags = ["digest", "weekly", "tools"]
        # Тут можна зібрати нові інструменти за тиждень (з кешу)
        # Або просто згенерувати текстовий дайджест
        content = generate_weekly_digest()  # або просто використати Gemini
    else:
        # Вибираємо тему з пулу
        themes = load_themes()
        if not themes:
            logger.error("No themes available. Exiting.")
            return 1

        chosen = random.choice(themes)
        base_title = chosen["title"]
        category = chosen["category"]
        tags = chosen.get("tags", [])

        # Покращуємо тему за допомогою AI
        title = enhance_topic_with_ai(base_title, category)
        logger.info(f"📝 Enhanced topic: {title}")

        # Генеруємо контент
        content = generate_post_content(title, category)

    if not content:
        logger.error("❌ Failed to generate content. Exiting.")
        return 1

    # Зберігаємо пост
    date_str = now.strftime("%Y-%m-%d")
    save_post(title, content, category, tags, date=date_str)

    logger.info("✅ Post published successfully!")
    return 0


def generate_weekly_digest():
    """Генерує щотижневий дайджест (можна використати Gemini для написання)."""
    # Можна зібрати дані з кешу або просто написати шаблон
    # Для простоти використаємо Gemini
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return """## This Week in AI Tools

Here are the top AI tools that caught our attention this week.

Stay tuned for next week's digest!

**Subscribe to our newsletter** to get these updates delivered to your inbox."""

    prompt = """
Write a weekly digest post for Indie AI Radar (target: indie hackers and solopreneurs).

It should include:
- A warm welcome
- A list of 3-5 recent AI tools (you can invent names or use generic descriptions)
- A key trend or insight from the week
- A call-to-action to subscribe

Keep it between 300-400 words. Use markdown formatting. Make it friendly and engaging.
"""
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.8, "maxOutputTokens": 2048}
            },
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Digest generation failed: {e}")
        return "Weekly digest coming soon!"


if __name__ == "__main__":
    sys.exit(main())