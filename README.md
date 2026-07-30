# Indie AI Radar

[![Autopilot — Daily Harvest & Deploy](https://github.com/renion-dev/indiearadar/actions/workflows/autopilot.yml/badge.svg)](https://github.com/renion-dev/indiearadar/actions/workflows/autopilot.yml)

**Indie AI Radar** — це повністю автономна SEO-фабрика, яка щодня збирає AI-інструменти з Product Hunt, генерує програмні SEO-сторінки та автоматично деплоїть сайт.

---

## 🚀 Особливості

- **Автоматичний збір інструментів** — щоденний парсинг Product Hunt через GraphQL API.
- **Програмні SEO-сторінки** — генерація сотень сторінок на основі Seed-даних (професії, категорії, ціни).
- **Структуровані дані** — JSON-LD (ItemList, FAQPage, CollectionPage) для покращення видимості в пошуку.
- **Внутрішня перелінковка** — блоки "Similar AI Tools" на сторінках інструментів і категорій.
- **Повна автоматизація** — GitHub Actions запускає збір, генерацію та деплой щодня о 8:00 UTC.
- **Сучасний дизайн** — темна тема, адаптивна сітка, каскадні логотипи.

---

## 🏗 Архітектура

Seed Data (_data/seed/)
│
▼
scripts/seed_generator.py
│
▼
Programmatic Definitions (_data/programmatic/)
│
▼
scripts/programmatic_generator.py
│
▼
Pages (pages/programmatic/)
│
▼
Jekyll
│
▼
Static Site (_site/)

**Принципи:**
- **Seed — джерело істини** (бізнес-сутності: професії, категорії, ціни).
- **Programmatic Definitions — артефакт генерації** (ніколи не редагувати вручну).
- **Pages — артефакт генерації** (ніколи не редагувати вручну).

---

## 📦 Встановлення та запуск

### Локальний розвиток

1. Клонувати репозиторій:
   ```bash
   git clone https://github.com/renion-dev/indiearadar.git
   cd indiearadar
Встановити залежності Python:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Встановити залежності Ruby:
bundle install

cp .env.example .env
# Додати PH_API_TOKEN та GEMINI_API_KEY

python3 scripts/seed_generator.py
python3 scripts/programmatic_generator.py
bundle exec jekyll serve
    Відкрити http://localhost:4000/indiearadar/

🔧 Основні скрипти
Скрипт	Призначення
scripts/harvest.py	Щоденний збір нових інструментів з Product Hunt
scripts/harvest_range.py	Збір за вказану кількість днів (з порогом голосів)
scripts/seed_generator.py	Генерація програмних визначень із Seed-даних
scripts/programmatic_generator.py	Генерація Markdown-сторінок із програмних визначень
scripts/normalize_frontmatter.py	Нормалізація frontmatter для всіх інструментів
scripts/sync_categories.py	Автоматичне додавання нових категорій у Seed
🤖 Автоматизація

GitHub Actions workflow (.github/workflows/autopilot.yml) запускається щодня о 8:00 UTC:

    Запускає harvest.py для збору нових інструментів.

    Запускає seed_generator.py та programmatic_generator.py.

    Будує сайт через Jekyll.

    Комітить і пушить зміни (нові інструменти, сторінки, sitemap).

📁 Структура проєкту
.
├── _data/
│   ├── seed/                    # Джерело істини (професії, категорії)
│   └── programmatic/            # Згенеровані визначення сторінок (артефакт)
├── _tools/                      # Інструменти (Markdown з frontmatter)
├── _posts/                      # Блог-пости та дайджести
├── _layouts/                    # Шаблони Jekyll
├── _includes/                   # Частини шаблонів (tool-card, structured-data)
├── pages/
│   └── programmatic/            # Згенеровані програмні сторінки (артефакт)
├── scripts/                     # Усі скрипти Python
├── assets/                      # Стилі, зображення, OG-картинки
├── docs/                        # Документація (ADR, архітектура, roadmap)
├── .github/workflows/           # GitHub Actions
├── _config.yml                  # Конфігурація Jekyll
├── Gemfile                      # Залежності Ruby
├── requirements.txt             # Залежності Python
└── README.md                    # Цей файл

🧠 Як додати нову категорію сторінок

    Відредагувати _data/seed/professions/professions.yml:
- slug: new-category
  title: New Category
  description: Best AI tools for new category.
  tool_filters:
    categories:
      - category1
      - category2
  limit: 20

Запустити генерацію:
bash

python3 scripts/seed_generator.py
python3 scripts/programmatic_generator.py

    Нова сторінка з'явиться за адресою:
    /best-ai-tools-for-new-category/

📊 Поточний стан
Метрика	Значення
Інструментів	75+
Програмних сторінок	24+
Блог-постів	30+
Sitemap URL	140+
Автоматизація	✅ GitHub Actions
📖 Документація

    Архітектура

    ADR (Architecture Decision Records)

    Roadmap

    Монетизація

    Workflows

📝 Ліцензія

MIT © renion-dev
