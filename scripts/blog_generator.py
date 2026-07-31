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
MIN_INTERVAL_HOURS = 0
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
Generate 3 different titles for my blog post based on the base topic: "{base_title}" (category: {category}).
Target audience: Indie hackers and solopreneurs (busy, result-driven, love data).

Requirements for each title:

    Must be under 60 characters (for SEO).

    Must include a specific number, time frame, or dollar amount if applicable.

    Must use one of these 3 distinct angles:

        Angle A: Contrarian (challenge a common belief in this niche).

        Angle B: Actionable/Recipe (promise a specific step-by-step outcome).

        Angle C: Status/Validation (use social proof or personal win).

Output format: Only the 3 titles, numbered 1-3. No extra text.
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
Write a blog post for Indie AI Radar — a no-BS blog for solopreneurs who hate fluff.

Title: {title}
Category: {category}

STRUCTURAL RULES (MANDATORY):

    The Hook (first sentence): Start with a bold, single-sentence hot take or a specific failure/success metric. NO greetings, NO "In today's world". Example: "If you use this tool wrong, you'll lose 5 hours of your week — I just did it so you don't have to."

    TL;DR Box: Immediately after the intro, add a > **⚡ TL;DR** section with 3 bullet points summarizing the verdict (must include a "Skip this if..." caveat).

    Signature Sections: Use these exact subheadings in the body:

        ## 🧠 The Reality Check (debunk 1 common myth about this tool/method).

        ## ⚙️ The Solopreneur Playbook (step-by-step, but keep each step to 1-2 sentences).

        ## 📉 The Catch (aka The Fine Print) (this is crucial! Write what sucks about it).

    The "Builders' Math": Include one short calculation (e.g., "Cost: $20/mo. Time saved: 3 hrs/week. At $50/hr — it pays off in 2 days.")

TONE & VOICE:

    Write like a tired but enthusiastic indie dev who has tried 100 tools this month.

    Use short, punchy sentences (max 15 words per sentence on average).

    Be brutally objective. If the tool is overhyped — say it. If it's a game-changer — explain why in 1 specific case.

    Humor is allowed ONLY as self-deprecation (e.g., "Yes, I broke the production server testing this. Twice.").

LENGTH: 350-500 words.

CTA: End with a rough, non-corporate CTA. Instead of "Subscribe to our weekly newsletter", 
write: "P.S. We send 1 weekly radar ping with tools that actually survive the 7-day test. No spam. Just signal. Drop your email [link]."
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
    og_path = generate_og_image(title, category, slug)

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
Write a weekly "Indie AI Radar" newsletter for busy solopreneurs.

Style:
- zero fluff
- practical
- concise
- markdown
- 300–400 words
- avoid marketing buzzwords
- focus on saving time and making money

Structure:

# 👋 Welcome
Write a short welcoming introduction (2-3 sentences).

# 🚀 AI Tools
List 3-5 real AI tools released or significantly updated during the last 7 days.

For each tool include:
- what it does
- why it matters
- who should use it

Keep each description under 40 words.

# 📈 Weekly Insight
Summarize one important trend from this week's AI ecosystem and explain why it matters to indie founders.

# 📬 Subscribe
End with a short CTA encouraging readers to subscribe for next week's digest.
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