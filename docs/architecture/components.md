# Компоненти системи

## 1. Збір даних
- **harvest.py** — щоденний збір з Product Hunt
- **harvest_range.py** — збір за діапазон дат
- **og_image.py** — генерація зображень

## 2. Seed-дані
- **professions.yml** — список професій
- **industries.yml** — список індустрій
- **pricing.yml** — цінові категорії
- **platforms.yml** — платформи

## 3. Генератори
- **seed_generator.py** — Seed → Programmatic YAML
- **programmatic_generator.py** — Programmatic YAML → Markdown

## 4. Представлення
- **Jekyll** — генерація статичного сайту
- **_layouts/programmatic.html** — шаблон для SEO-сторінок
- **tool-card.html** — картка інструменту

## 5. Інфраструктура
- **_cache/** — кеш API-запитів
- **_posts/** — блог (дайджести)
- **_tools/** — каталог інструментів
- **pages/programmatic/** — згенеровані SEO-сторінки

## Залежності

- Python 3.10+
- Ruby + Jekyll
- Product Hunt API
- Google Gemini API (для оглядів)
