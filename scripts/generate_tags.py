#!/usr/bin/env python3
"""
generate_tags.py — автоматична генерація сторінок для тегів.
"""

import sys
from pathlib import Path
import yaml
import shutil

sys.path.insert(0, str(Path(__file__).parent))
from utils import logger, slugify, write_file, parse_front_matter

PROJECT_ROOT = Path(__file__).parent.parent
POSTS_DIR = PROJECT_ROOT / "_posts"
TOOLS_DIR = PROJECT_ROOT / "_tools"
TAG_DIR = PROJECT_ROOT / "tag"
LAYOUTS_DIR = PROJECT_ROOT / "_layouts"

# Нормалізація: що замінити на що
TAG_ALIASES = {
    "tools": "tool",
    # додавай сюди інші, якщо треба: "startups": "startup",
}


def clean_tag(raw):
    """Очищає тег: нижній регістр, strip, видаляє обгортки []\"' """
    return str(raw).strip().lower().strip('[]"\'')


def collect_tags():
    """Збирає всі теги з постів та інструментів."""
    tags = set()
    for md_path in list(POSTS_DIR.glob("*.md")) + list(TOOLS_DIR.glob("*.md")):
        fm = parse_front_matter(str(md_path))
        if fm and "tags" in fm:
            tag_list = fm["tags"]
            if isinstance(tag_list, list):
                for t in tag_list:
                    tag = clean_tag(t)
                    if tag:
                        tags.add(TAG_ALIASES.get(tag, tag))
            elif isinstance(tag_list, str):
                for t in tag_list.split(","):
                    tag = clean_tag(t)
                    if tag:
                        tags.add(TAG_ALIASES.get(tag, tag))
    return sorted(tags)


def generate_tag_pages():
    tags = collect_tags()

    logger.info(f"Collected tags: {tags}")

    if not tags:
        logger.warning("No tags found. Skipping tag pages generation.")
        return

    # Очистити старі теги перед генерацією (опціонально, прибери якщо не треба)
    if TAG_DIR.exists():
        shutil.rmtree(TAG_DIR)
    TAG_DIR.mkdir(parents=True, exist_ok=True)

    for tag in tags:
        slug = slugify(tag)
        if not slug:
            logger.warning(f"Empty slug for tag '{tag}', skipping.")
            continue

        filepath = TAG_DIR / f"{slug}.md"
        if filepath.exists():
            logger.info(f"Tag page already exists: {filepath}")
            continue

        title = f"{tag.title()} — Posts and Tools"
        frontmatter = {
            "layout": "tag",
            "title": title,
            "tag": tag,
            "permalink": f"/tag/{slug}/"
        }
        yaml_str = yaml.dump(
            frontmatter,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            default_style=None,
            indent=2
        ).strip()
        content = f"---\n{yaml_str}\n---\n"
        write_file(str(filepath), content)
        logger.info(f"Generated tag page: {filepath}")

    # Створюємо layout, якщо немає
    layout_path = LAYOUTS_DIR / "tag.html"
    if not layout_path.exists():
        layout_content = """---
layout: default
---

<div class="tag-page">
  <h1>#{{ page.tag | capitalize }}</h1>
  <p class="tag-description">All content tagged with <strong>{{ page.tag }}</strong></p>

  <h2>Tools</h2>
  <div class="tool-grid">
    {% assign tools = site.tools | where_exp: "tool", "tool.tags contains page.tag" %}
    {% if tools.size == 0 %}
      <p>No tools with this tag yet.</p>
    {% else %}
      {% for tool in tools %}
        {% include tool-card.html tool=tool %}
      {% endfor %}
    {% endif %}
  </div>

  <h2>Blog Posts</h2>
  <div class="post-list">
    {% assign posts = site.posts | where_exp: "post", "post.tags contains page.tag" %}
    {% if posts.size == 0 %}
      <p>No blog posts with this tag yet.</p>
    {% else %}
      <ul>
      {% for post in posts %}
        <li><a href="{{ post.url }}">{{ post.title }}</a> <time>{{ post.date | date: "%b %-d, %Y" }}</time></li>
      {% endfor %}
      </ul>
    {% endif %}
  </div>
</div>
"""
        write_file(str(layout_path), layout_content)
        logger.info(f"Created tag layout: {layout_path}")


if __name__ == "__main__":
    generate_tag_pages()