#!/usr/bin/env python3
"""
Нормалізація frontmatter для всіх інструментів у _tools/
Виправляє: category, tags, domain, affiliate_link, image, rating
"""

import os
import sys
import re
import json
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import logger, slugify

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
    """Обчислює рейтинг на основі голосів."""
    if not votes:
        return 4.0
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

def infer_category(name, tags, existing_category):
    """Визначає категорію на основі назви, тегів або існуючої."""
    if existing_category and existing_category != 'productivity':
        return existing_category
    text = name.lower()
    if any(word in text for word in ['code', 'programming', 'developer', 'dev', 'coding', 'api']):
        return 'code'
    if any(word in text for word in ['design', 'ui', 'ux', 'graphic', 'creative', 'visual', 'figma']):
        return 'design'
    if any(word in text for word in ['marketing', 'seo', 'social', 'email', 'growth', 'ads']):
        return 'marketing'
    if any(word in text for word in ['content', 'video', 'animation', 'writing', 'blog', 'article']):
        return 'content'
    if any(word in text for word in ['analytics', 'data', 'insights', 'metrics', 'reporting']):
        return 'analytics'
    if any(word in text for word in ['automation', 'workflow', 'zapier', 'integrations']):
        return 'automation'
    if any(word in text for word in ['audio', 'music', 'podcast', 'voice', 'speech']):
        return 'audio'
    if any(word in text for word in ['image', 'photo', 'art', 'generative']):
        return 'image'
    if tags:
        tag_text = ' '.join(tags).lower()
        if 'code' in tag_text or 'developer' in tag_text:
            return 'code'
        if 'design' in tag_text or 'ui' in tag_text:
            return 'design'
        if 'marketing' in tag_text or 'seo' in tag_text:
            return 'marketing'
        if 'content' in tag_text or 'writing' in tag_text:
            return 'content'
    return 'productivity'

def infer_tags(name, category, existing_tags):
    """Доповнює теги, якщо їх менше 3."""
    tags = existing_tags if existing_tags else []
    if not tags:
        tags = ['ai']
    if category and category not in tags:
        tags.append(category)
    # Додаємо слова з назви
    words = re.findall(r'\b[a-zA-Z]{3,}\b', name)
    stopwords = {'the', 'for', 'and', 'with', 'by', 'of', 'to', 'from', 'a', 'an', 'studio', 'tool'}
    for w in words:
        w_lower = w.lower()
        if w_lower not in stopwords and w_lower not in tags and len(w_lower) > 2:
            tags.append(w_lower)
            if len(tags) >= 5:
                break
    # Якщо все ще менше 3, додаємо загальні теги
    extra = ['automation', 'marketing', 'design', 'code', 'analytics', 'content', 'productivity']
    while len(tags) < 3:
        for e in extra:
            if e not in tags:
                tags.append(e)
                break
    return tags[:5]

def extract_domain(url):
    if not url:
        return ""
    domain = re.sub(r'^https?://', '', url)
    domain = domain.split('/')[0].split('?')[0]
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain.lower()

def normalize_file(filepath):
    """Нормалізує frontmatter у файлі."""
    content = filepath.read_text(encoding='utf-8')
    frontmatter, body = parse_frontmatter(content)
    
    # Пропускаємо, якщо немає name
    if 'name' not in frontmatter:
        return False
    
    name = frontmatter.get('name')
    votes = frontmatter.get('votes', 0)
    existing_category = frontmatter.get('category', '')
    existing_tags = frontmatter.get('tags', [])
    affiliate_link = frontmatter.get('affiliate_link', '')
    domain = frontmatter.get('domain', '')
    image = frontmatter.get('image', '')
    rating = frontmatter.get('rating', 4.0)
    
    # 1. Category
    new_category = infer_category(name, existing_tags, existing_category)
    
    # 2. Tags
    new_tags = infer_tags(name, new_category, existing_tags)
    
    # 3. Domain
    if not domain and affiliate_link:
        domain = extract_domain(affiliate_link)
    elif not domain and 'domain' in frontmatter:
        domain = frontmatter.get('domain')
    
    # 4. Affiliate link
    if not affiliate_link and 'url' in frontmatter:
        affiliate_link = frontmatter.get('url')
    elif not affiliate_link and 'website' in frontmatter:
        affiliate_link = frontmatter.get('website')
    
    # 5. Image
    if not image:
        slug = frontmatter.get('slug', slugify(name))
        image = f"/assets/images/og/tool-{slug}.png"
    
    # 6. Rating
    new_rating = generate_rating(votes)
    
    # Оновлюємо frontmatter
    frontmatter['category'] = new_category
    frontmatter['tags'] = new_tags
    frontmatter['domain'] = domain
    frontmatter['affiliate_link'] = affiliate_link
    frontmatter['image'] = image
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
    logger.info(f"✅ Нормалізовано {filepath.name} (категорія: {new_category}, тегів: {len(new_tags)}, рейтинг: {new_rating})")
    return True

def main():
    logger.info("🚀 Нормалізація frontmatter для інструментів")
    fixed = 0
    for filepath in TOOLS_DIR.glob("*.md"):
        if normalize_file(filepath):
            fixed += 1
    logger.info(f"🎉 Готово! Нормалізовано {fixed} файлів.")

if __name__ == "__main__":
    main()
