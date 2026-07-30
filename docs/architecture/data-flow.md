# Потоки даних

## Поточний пайплайн

    Seed Data
    _data/seed/professions/professions.yml
    │
    ▼

    Seed Generator
    python scripts/seed_generator.py
    │
    ▼

    Page Definitions
    _data/programmatic/best-tools/professions/*.yml
    │
    ▼

    Programmatic Generator
    python scripts/programmatic_generator.py
    │
    ▼

    Markdown Pages
    pages/programmatic/*.md
    │
    ▼

    Jekyll Build
    bundle exec jekyll build
    │
    ▼

    Static Website
    _site/

## Розширений пайплайн (майбутнє)

_seed/
professions.yml → best-tools/professions/.yml
industries.yml → best-tools/industries/.yml
pricing.yml → best-tools/pricing/.yml
platforms.yml → best-tools/platforms/.yml
alternatives.yml → alternatives/.yml
comparisons.yml → comparisons/.yml
## Принципи

- Кожен генератор робить одну річ.
- Дані переходять від більш абстрактних до більш конкретних.
- Жоден генератор не знає про внутрішню структуру іншого.
- Можна перебудувати всю систему, видаливши `_data/programmatic/` і `pages/programmatic/`.
