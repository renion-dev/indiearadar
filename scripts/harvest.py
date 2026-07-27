#!/usr/bin/env python3
"""
Indie AI Radar — Data Harvester
Автоматичний збір AI-інструментів з Product Hunt, генерація оглядів через Gemini,
створення OG-зображень, збереження у _tools/ та _posts/.
Використовує спільні утиліти з utils.py.

Usage:
    python scripts/harvest.py

Environment:
    PH_API_TOKEN     — Product Hunt Developer Token (free)
    GEMINI_API_KEY   — Google AI Studio API Key (free, 1500 req/day)
    SITE_URL         — (опціонально) для посилань у дайджесті
"""

import os
import sys
import re
import time
import json
from datetime import datetime
from pathlib import Path
import requests 
# Додаємо корінь проєкту до sys.path, щоб імпортувати scripts
sys.path.insert(0, str(Path(__file__).parent))

# Імпорт з utils
from utils import (
    logger, retry, Cache, RateLimiter,
    slugify, is_ai_related, write_file
)

# Імпорт з og_image
from og_image import generate_tool_og

# Налаштування шляхів
PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "_tools"
POSTS_DIR = PROJECT_ROOT / "_posts"
CACHE_PATH = PROJECT_ROOT / "_cache" / "harvest_cache.json"

# Мінімальна кількість голосів для фільтрації
MIN_VOTES = 10

# Обмеження частоти запитів до Product Hunt (безкоштовно — 100 запитів на 15 хв)
PH_RATE_LIMIT = RateLimiter(calls=90, period=900)   # 90 запитів за 15 хв
GEMINI_RATE_LIMIT = RateLimiter(calls=60, period=60)  # 60 запитів за хвилину (безпечний запас)


@retry(max_retries=3, backoff_factor=2.0, exceptions=(Exception,))
def fetch_product_hunt():
    """Fetch top posts from Product Hunt via GraphQL API."""
    token = os.environ.get("PH_API_TOKEN")
    if not token:
        logger.error("PH_API_TOKEN not set. Set it as GitHub Secret or env var.")
        logger.info("Get free token at: https://developer.producthunt.com")
        return []

    # Чекаємо, щоб не перевищити ліміт
    PH_RATE_LIMIT.wait()

    query = """
    query {
      posts(first: 20, order: VOTES, postedAfter: "YYYY-MM-DDT00:00:00Z") {
        edges {
          node {
            id
            name
            tagline
            url
            website
            description
            votesCount
            topics { edges { node { name } } }
            thumbnail { url }
          }
        }
      }
    }
    """.replace("YYYY-MM-DD", datetime.now().strftime("%Y-%m-%d"))

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    resp = requests.post(
        "https://api.producthunt.com/v2/api/graphql",
        headers=headers,
        json={"query": query},
        timeout=30
    )
    resp.raise_for_status()
    data = resp.json()
    edges = data.get("data", {}).get("posts", {}).get("edges", [])
    logger.info(f"Fetched {len(edges)} posts from Product Hunt")
    return edges


@retry(max_retries=3, backoff_factor=2.0, exceptions=(Exception,))
def generate_review_with_gemini(tool_data):
    """Generate full review using Google Gemini API (free tier)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not set. Using template review.")
        return None

    name = tool_data["name"]
    tagline = tool_data.get("tagline", "")
    url = tool_data.get("url", "")

    prompt = f"""Write a detailed product review for an AI tool called "{name}".
Tagline: {tagline}
Website: {url}

Format as Markdown with these sections:
## What is {name}?
(2-3 sentences explaining what the tool does)

## Key Features
- (3-5 bullet points with specific features)

## Pricing
| Plan | Price | Best For |
|------|-------|----------|
| Free | $0 | (who) |
| Pro | $X/mo | (who) |
| Enterprise | Custom | (who) |

## Why Indie Hackers Love It
(1 paragraph with specific use case)

## Verdict
**Best for:** (target audience)
**Skip if:** (who shouldn't use it)

Keep it honest, practical, and under 400 words."""

    # Чекаємо перед запитом до Gemini
    GEMINI_RATE_LIMIT.wait()

    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-lite:generateContent?key={api_key}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}
        },
        timeout=60
    )
    resp.raise_for_status()
    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return text


def resolve_real_url(ph_tracking_url: str) -> str:
    """Follow Product Hunt redirect to get real website URL."""
    if not ph_tracking_url or "producthunt.com" not in ph_tracking_url:
        return ph_tracking_url
    try:
        resp = requests.get(
            ph_tracking_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            allow_redirects=True,
            timeout=10,
        )
        return resp.url.split("?")[0]
    except Exception:
        return ph_tracking_url


def generate_digest_post(new_tools, date_str):
    """Create a daily digest post in _posts/ with links to new tools."""
    if not new_tools:
        return None

    slug = f"{date_str}-daily-ai-tools-digest"
    title = f"Daily AI Tools Digest — {datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y')}"

    frontmatter = {
        "title": title,
        "date": date_str,
        "layout": "post",
        "category": "digest",
        "tags": ["ai", "tools", "daily"]
    }

    # Будуємо тіло поста
    lines = [
        f"## 🚀 New AI Tools Today ({len(new_tools)})",
        "",
        "Here are the latest AI tools that appeared on Product Hunt today, curated for indie hackers:",
        ""
    ]

    for tool in new_tools:
        lines.append(f"### [{tool['name']}]({tool['url']})")
        lines.append(f"*{tool['tagline']}*")
        lines.append("")
        lines.append(f"[Read full review →](/tool/{tool['slug']}/)")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_Want these delivered to your inbox weekly? [Subscribe to our newsletter](/newsletter/)._")

    body = "\n".join(lines)

    # Збираємо YAML фронтматтер
    yaml = "---\n"
    for k, v in frontmatter.items():
        if isinstance(v, list):
            yaml += f"{k}:\n"
            for item in v:
                yaml += f"  - {item}\n"
        else:
            yaml += f"{k}: {json.dumps(v) if isinstance(v, str) else v}\n"
    yaml += "---\n\n"

    content = yaml + body
    filepath = POSTS_DIR / f"{slug}.md"
    write_file(str(filepath), content)
    logger.info(f"Created digest post: {filepath}")
    return filepath


def main():
    logger.info("🚀 Starting Indie AI Radar — Daily Harvest")
    logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info("-" * 50)

    # 1. Ініціалізуємо кеш
    cache = Cache(str(CACHE_PATH))

    # 2. Отримуємо дані з Product Hunt
    logger.info("📡 Fetching Product Hunt...")
    edges = fetch_product_hunt()
    if not edges:
        logger.warning("No data from Product Hunt. Exiting.")
        return 0

    # 3. Фільтруємо AI-інструменти та перевіряємо, чи вже оброблені
    new_tools = []
    processed_count = 0
    for edge in edges:
        node = edge.get("node", {})
        tool_id = node.get("id")
        name = node.get("name", "")
        tagline = node.get("tagline", "")
        votes = node.get("votesCount", 0)
        description = node.get("description", "")

        # Перевіряємо, чи вже оброблено (за ID)
        if cache.is_processed(tool_id):
            processed_count += 1
            continue

        # Перевіряємо AI-релевантність
        text = f"{name} {tagline} {description}"
        if not is_ai_related(text, threshold=1):
            continue

        # Перевіряємо голоси
        if votes < MIN_VOTES:
            continue

        # Все добре — додаємо
        new_tools.append({
            "id": tool_id,
            "name": name,
            "tagline": tagline,
            "url": node.get("website") or node.get("url", ""),
            "votes": votes,
            "description": description,
            "thumbnail": node.get("thumbnail", {}).get("url", "")
        })

    logger.info(f"🤖 AI tools found: {len(new_tools)} (skipped {processed_count} already processed)")

    if not new_tools:
        logger.info("✨ No new AI tools today. Exiting.")
        return 0

    # 4. Генеруємо огляди для кожного нового інструменту
    generated = 0
    for tool in new_tools:
        logger.info(f"📝 Generating review for: {tool['name']}")

        # Генеруємо слаг
        slug = slugify(tool['name'])
        tool['slug'] = slug

        # Генеруємо OG-зображення (шлях до файлу)
        og_path = generate_tool_og(
            tool_name=tool['name'],
            category="productivity",
            slug=slug,
            output_dir="assets/images/og"
        )
        tool['og_image'] = og_path

        # Генеруємо текст огляду
        review_text = generate_review_with_gemini(tool)

        if not review_text:
            logger.warning(f"⚠️  Failed to generate review for {slug}, using fallback.")
            review_text = f"## What is {tool['name']}?\n\n{tool['tagline']}\n\n## Key Features\n\n- Feature 1\n- Feature 2\n- Feature 3\n\n## Verdict\n\n**Best for:** Indie hackers looking for AI tools."

        # Отримуємо реальний URL
        real_url = resolve_real_url(tool['url'])
        domain = ""
        if real_url:
            raw_domain = re.sub(r"^https?://", "", real_url)
            domain = raw_domain.split("/")[0].split("?")[0]

        # Збираємо фронтматтер
        frontmatter = {
            "name": tool['name'],
            "slug": slug,
            "title": f"{tool['name']} — {tool['tagline'][:60]}",
            "tagline": tool['tagline'],
            "category": "productivity",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "rating": 4.0,
            "pricing": "freemium",
            "affiliate_link": real_url,
            "domain": domain,
            "image": og_path,   # шлях до OG-зображення
            "tags": ["ai", "tool"],
            "source": "producthunt"
        }

        # Будуємо YAML + тіло
        yaml_lines = ["---"]
        for key, val in frontmatter.items():
            if isinstance(val, list):
                yaml_lines.append(f"{key}:")
                for item in val:
                    yaml_lines.append(f"  - {item}")
            else:
                # Екранування простих рядків
                if isinstance(val, str):
                    val = json.dumps(val)  # додає лапки
                yaml_lines.append(f"{key}: {val}")
        yaml_lines.append("---")
        content = "\n".join(yaml_lines) + "\n\n" + review_text

        # Зберігаємо файл інструменту
        tool_path = TOOLS_DIR / f"{slug}.md"
        write_file(str(tool_path), content)

        # Позначаємо в кеші як оброблений
        cache.mark_processed(tool['id'])

        generated += 1
        logger.info(f"✅ Saved: {tool_path}")

        # Невелика пауза між генераціями
        time.sleep(1)

    # 5. Створюємо щоденний дайджест
    digest_date = datetime.now().strftime("%Y-%m-%d")
    digest_file = generate_digest_post(new_tools, digest_date)

    logger.info(f"🎉 Done! Generated {generated} new reviews and daily digest.")
    logger.info(f"Cache stats: {cache.get_processed_count()} total processed items.")
    return 0


if __name__ == "__main__":
    sys.exit(main())