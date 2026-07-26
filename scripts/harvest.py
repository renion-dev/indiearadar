#!/usr/bin/env python3
"""
Indie AI Radar — Data Harvester
Збирає AI-інструменти з Product Hunt API
Free tier, no trials, no paid services.

Usage:
    python scripts/harvest.py

Environment:
    PH_API_TOKEN — Product Hunt Developer Token (free)
    GEMINI_API_KEY — Google AI Studio API Key (free, 1500 req/day)
"""

import os
import sys
import json
import re
import time          # ← додано для retry
import requests
from datetime import datetime
from pathlib import Path


# ─── Retry Decorator ──────────────────────────────────────────────
def with_retry(max_retries=3, backoff=2):
    """Повторює виконання функції при винятках із зростаючою затримкою."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise   # остання спроба – піднімаємо виняток
                    wait = backoff ** (attempt - 1)  # 1, 2, 4, 8...
                    print(f"⚠️  Retry {attempt}/{max_retries} for {func.__name__} after {wait}s due to: {e}")
                    time.sleep(wait)
            return None
        return wrapper
    return decorator


# ─── Configuration ───
PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "_tools"
IMAGES_DIR = PROJECT_ROOT / "assets" / "images" / "tools"
OG_DIR = PROJECT_ROOT / "assets" / "images" / "og"

AI_KEYWORDS = [
    "ai", "artificial intelligence", "gpt", "llm", "machine learning",
    "automation", "assistant", "generator", "copilot", "chatbot",
    "neural", "deep learning", "nlp", "computer vision", "text-to-image",
    "text-to-speech", "voice", "code generation", "no-code", "low-code"
]

MIN_VOTES = 10  # мінімум голосів для фільтрації


@with_retry(max_retries=3, backoff=2)   # ← додано
def fetch_product_hunt():
    """Fetch top posts from Product Hunt via GraphQL API."""
    token = os.environ.get("PH_API_TOKEN", "")
    if not token:
        print("⚠️  PH_API_TOKEN not set. Set it as GitHub Secret or env var.")
        print("   Get free token at: https://developer.producthunt.com")
        return []

    query = """
    query {
      posts(first: 20, order: VOTES, postedAfter: "YYYY-MM-DDT00:00:00Z") {
        edges {
          node {
            id
            name
            tagline
            url
            website        # ← реальний сайт інструменту
            description    # ← опис для AI-фільтра
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

    try:
        resp = requests.post(
            "https://api.producthunt.com/v2/api/graphql",
            headers=headers,
            json={"query": query},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("posts", {}).get("edges", [])
    except Exception as e:
        print(f"❌ Product Hunt API error: {e}")
        return []   # повертаємо порожній список, не піднімаємо виняток – це дозволяє продовжити роботу


def is_ai_tool(post):
    """Check if post is AI-related and has enough votes."""
    node = post.get("node", {})
    name = node.get("name", "").lower()
    tagline = node.get("tagline", "").lower()
    votes = node.get("votesCount", 0)
    topics = [t["node"]["name"].lower() for t in node.get("topics", {}).get("edges", [])]

    text = f"{name} {tagline}"
    has_ai = any(kw in text or any(kw in t for t in topics) for kw in AI_KEYWORDS)
    return has_ai and votes >= MIN_VOTES


def slugify(name):
    """Convert tool name to URL-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[\s]+", "-", slug)
    return slug.strip("-")[:50]


def tool_exists(slug):
    """Check if tool already reviewed."""
    return (TOOLS_DIR / f"{slug}.md").exists()


def generate_og_image(tool_name, category):
    """Generate OG image via Pollinations.ai (free, no API key)."""
    prompt = f"{tool_name} AI tool interface dark mode minimal futuristic {category}"
    encoded = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1200&height=630&nologo=true&seed={hash(tool_name) % 10000}"
    return url


@with_retry(max_retries=3, backoff=2)   # ← додано
def generate_review_with_gemini(tool_data):
    """Generate full review using Google Gemini API (free tier)."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("⚠️  GEMINI_API_KEY not set. Using template review.")
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

    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={api_key}",
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
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return None

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
        return resp.url.split("?")[0]  # прибираємо ?ref=producthunt
    except Exception:
        return ph_tracking_url



def save_tool_review(slug, tool_data, review_body, og_image_url):
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    # ---- Заміни цей рядок ----
    ph_url = tool_data.get("website") or tool_data.get("url", "")
    url = resolve_real_url(ph_url)
    # --------------------------

    domain = ""
    if url:
        raw_domain = re.sub(r"^https?://", "", url)
        domain = raw_domain.split("/")[0].split("?")[0]

    frontmatter = {
        "name": tool_data['name'],
        "slug": slug,
        "title": f"{tool_data['name']} — {tool_data.get('tagline', 'AI Tool')[:60]}",
        "tagline": tool_data.get("tagline", ""),
        "category": "productivity",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "rating": 4.0,
        "pricing": "freemium",
        "affiliate_link": url,
        "domain": domain,   # ← тепер реальний домен
        "image": f"/assets/images/tools/{slug}.jpg",
        "tags": ["ai", "tool"],
        "source": "producthunt"
    }

    # Build YAML frontmatter
    yaml_lines = ["---"]
    for key, val in frontmatter.items():
        if isinstance(val, list):
            yaml_lines.append(f"{key}:")
            for item in val:
                yaml_lines.append(f"  - {item}")
        else:
            yaml_lines.append(f"{key}: {json.dumps(val) if isinstance(val, str) else val}")
    yaml_lines.append("---")

    content = "\n".join(yaml_lines) + "\n\n" + (review_body or "")

    filepath = TOOLS_DIR / f"{slug}.md"
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✅ Saved: {filepath}")
    return filepath


def main():
    print("🚀 Indie AI Radar — Daily Harvest")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("-" * 50)

    # 1. Fetch from Product Hunt
    print("📡 Fetching Product Hunt...")
    posts = fetch_product_hunt()
    print(f"   Found {len(posts)} posts")

    # 2. Filter AI tools
    ai_tools = [p for p in posts if is_ai_tool(p)]
    print(f"🤖 AI tools filtered: {len(ai_tools)}")

    # 3. Skip existing
    new_tools = []
    for post in ai_tools:
        slug = slugify(post["node"]["name"])
        if not tool_exists(slug):
            new_tools.append((slug, post["node"]))
        else:
            print(f"   ⏭️  Skipping existing: {slug}")

    print(f"🆕 New tools to review: {len(new_tools)}")

    if not new_tools:
        print("✨ Nothing new today. Exiting.")
        return 0

    # 4. Generate reviews
    generated = 0
    for slug, tool_data in new_tools:
        print(f"\n📝 Generating review for: {tool_data['name']}")

        review = generate_review_with_gemini(tool_data)
        og_url = generate_og_image(tool_data["name"], "productivity")

        if review:
            save_tool_review(slug, tool_data, review, og_url)
            generated += 1
        else:
            print(f"   ⚠️  Failed to generate review for {slug}")

        # Пауза 5 секунд, щоб не перевищити 15 запитів за хвилину (безкоштовний тариф Gemini)
        time.sleep(5)

    print(f"\n🎉 Done! Generated {generated} new reviews.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
