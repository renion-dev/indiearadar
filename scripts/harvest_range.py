#!/usr/bin/env python3
"""
Indie AI Radar — Data Harvester with date range
Збір AI-інструментів з Product Hunt за вказану кількість днів.
"""

import os
import sys
import re
import time
import json
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import logger, retry, Cache, RateLimiter, slugify, is_ai_related, write_file
from og_image import generate_tool_og

PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "_tools"
POSTS_DIR = PROJECT_ROOT / "_posts"
CACHE_PATH = PROJECT_ROOT / "_cache" / "harvest_cache.json"

MIN_VOTES = 10
PH_RATE_LIMIT = RateLimiter(calls=90, period=900)
GEMINI_RATE_LIMIT = RateLimiter(calls=60, period=60)

def generate_rating(votes):
    """Обчислює рейтинг на основі голосів (з випадковим розкидом)."""
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

@retry(max_retries=3, backoff_factor=2.0, exceptions=(Exception,))
def fetch_ph_posts_for_date(date_str):
    token = os.environ.get("PH_API_TOKEN")
    if not token:
        logger.error("PH_API_TOKEN not set")
        return []

    PH_RATE_LIMIT.wait()

    query = f"""
    query {{
      posts(first: 20, order: VOTES, postedAfter: "{date_str}T00:00:00Z") {{
        edges {{
          node {{
            id
            name
            tagline
            url
            website
            description
            votesCount
            topics {{ edges {{ node {{ name }} }} }}
            thumbnail {{ url }}
          }}
        }}
      }}
    }}
    """

    resp = requests.post(
        "https://api.producthunt.com/v2/api/graphql",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"query": query},
        timeout=30
    )
    resp.raise_for_status()
    data = resp.json()
    edges = data.get("data", {}).get("posts", {}).get("edges", [])
    logger.info(f"📅 {date_str}: отримано {len(edges)} постів")
    return edges

@retry(max_retries=3, backoff_factor=2.0, exceptions=(Exception,))
def generate_review_with_gemini(tool_data):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    name = tool_data["name"]
    tagline = tool_data.get("tagline", "")
    url = tool_data.get("url", "")

    prompt = f"""Write a detailed product review for an AI tool called "{name}".
Tagline: {tagline}
Website: {url}

Format as Markdown with sections:
## What is {name}?
## Key Features
## Pricing
## Why Indie Hackers Love It
## Verdict

Keep it under 400 words."""

    GEMINI_RATE_LIMIT.wait()
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={api_key}",
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}},
        timeout=60
    )
    if resp.status_code == 200:
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return None

def resolve_real_url(ph_tracking_url: str) -> str:
    if not ph_tracking_url or "producthunt.com" not in ph_tracking_url:
        return ph_tracking_url
    try:
        resp = requests.get(
            ph_tracking_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            allow_redirects=True,
            timeout=10,
        )
        return resp.url.split("?")[0]
    except Exception:
        return ph_tracking_url

def process_tool(node, cache, force=False):
    tool_id = node.get("id")
    if not force and cache.is_processed(tool_id):
        return None

    name = node.get("name", "")
    tagline = node.get("tagline", "")
    votes = node.get("votesCount", 0)
    description = node.get("description", "")
    website = node.get("website")
    ph_url = node.get("url")

    topics = node.get("topics", {}).get("edges", [])
    topic_names = [t.get("node", {}).get("name", "").lower() for t in topics if t.get("node")]

    text = f"{name} {tagline} {description}"
    if not is_ai_related(text, threshold=1):
        return None

    raw_url = website or ph_url
    real_url = resolve_real_url(raw_url)
    if not real_url:
        return None

    domain = re.sub(r"^https?://", "", real_url).split("/")[0].split("?")[0]
    if domain.startswith("www."):
        domain = domain[4:]

    category = "productivity"
    for topic in topic_names:
        if "code" in topic or "developer" in topic:
            category = "code"
            break
        elif "design" in topic:
            category = "design"
            break
        elif "marketing" in topic:
            category = "marketing"
            break
        elif "video" in topic or "content" in topic:
            category = "content"
            break

    slug = slugify(name)
    filepath = TOOLS_DIR / f"{slug}.md"

    # ---------- ПЕРЕВІРКА НА ДУБЛІКАТ ----------
    if filepath.exists() and not force:
        logger.info(f"⏭️  Пропускаємо {name}: файл вже існує")
        cache.mark_processed(tool_id)
        return None
    # ---------------------------------------------

    # ---------- ПРАВИЛЬНИЙ РЕЙТИНГ ----------
    rating = generate_rating(votes)
    # ---------------------------------------

    og_path = ""

    review_text = generate_review_with_gemini({
        "name": name,
        "tagline": tagline,
        "url": real_url
    })

    if not review_text:
        review_text = f"## What is {name}?\n\n{tagline}\n\n## Key Features\n\n- Feature 1\n- Feature 2\n- Feature 3\n\n## Verdict\n\n**Best for:** Indie hackers looking for AI tools."

    frontmatter = {
        "name": name,
        "slug": slug,
        "title": f"{name} — {tagline[:60]}",
        "tagline": tagline,
        "category": category,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "rating": rating,
        "pricing": "freemium",
        "affiliate_link": real_url,
        "domain": domain,
        "image": og_path,
        "tags": ["ai", category] + topic_names[:3],
        "source": "producthunt",
        "votes": votes
    }

    yaml_lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, list):
            yaml_lines.append(f"{k}:")
            for item in v:
                yaml_lines.append(f"  - {item}")
        else:
            yaml_lines.append(f"{k}: {json.dumps(v) if isinstance(v, str) else v}")
    yaml_lines.append("---")
    content = "\n".join(yaml_lines) + "\n\n" + review_text

    write_file(str(filepath), content)
    cache.mark_processed(tool_id)
    logger.info(f"✅ Додано: {name} (голосів: {votes}, рейтинг: {rating}, категорія: {category}, домен: {domain})")
    return filepath

def generate_digest(new_tools, date_str):
    if not new_tools:
        return
    slug = f"{date_str}-daily-ai-tools-digest"
    title = f"Daily AI Tools Digest — {datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y')}"

    frontmatter = {
        "title": title,
        "date": date_str,
        "layout": "post",
        "category": "digest",
        "tags": ["ai", "tools", "daily"]
    }
    lines = [f"## 🚀 New AI Tools Today ({len(new_tools)})", ""]
    for tool in new_tools:
        lines.append(f"### [{tool['name']}]({tool['url']})")
        lines.append(f"*{tool['tagline']}*")
        lines.append("")
        lines.append(f"[Read full review →](/tool/{tool['slug']}/)")
        lines.append("")
    lines.append("---")
    body = "\n".join(lines)
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
    logger.info(f"📄 Digest created: {filepath}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=1, help="Кількість днів для збору")
    parser.add_argument("--min-votes", type=int, default=10)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    logger.info(f"🚀 Запуск збору за {args.days} днів, мін. голосів {args.min_votes}")
    cache = Cache(str(CACHE_PATH))
    total_added = 0
    all_new_tools = []
    start_date = datetime.now() - timedelta(days=args.days)

    for i in range(args.days):
        date = start_date + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        edges = fetch_ph_posts_for_date(date_str)
        if not edges:
            continue

        daily_tools = []
        for edge in edges:
            node = edge.get("node", {})
            votes = node.get("votesCount", 0)
            if votes < args.min_votes:
                continue
            result = process_tool(node, cache, force=args.force)
            if result:
                total_added += 1
                daily_tools.append({
                    "name": node.get("name"),
                    "tagline": node.get("tagline"),
                    "slug": slugify(node.get("name")),
                    "url": node.get("website") or node.get("url")
                })
                time.sleep(0.5)

        if daily_tools:
            generate_digest(daily_tools, date_str)
            all_new_tools.extend(daily_tools)

    logger.info(f"🎉 Готово! Додано {total_added} інструментів за {args.days} днів.")

if __name__ == "__main__":
    main()
