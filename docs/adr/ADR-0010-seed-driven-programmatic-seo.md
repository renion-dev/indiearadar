# ADR-0010

## Title

Seed-Driven Programmatic SEO Architecture

---

## Status

Accepted

2026-07-30

---

## Context

До цього моменту `_data/programmatic/` було джерелом істини для програмних SEO-сторінок. Кожна сторінка описувалася окремим YAML-файлом.

Це працювало для 3–5 сторінок, але не масштабувалося для 50–100 сторінок, оскільки:

- кожен YAML писався вручну;
- структура сторінок повторювалася (Best AI Tools for X);
- не було єдиного місця для бізнес-даних (професії, індустрії, ціни).

Ми ввели **Seed-шар**, який став єдиним джерелом правди.

---

## Decision

Архітектура Programmatic SEO тепер будується на трьох рівнях:

### 1. Seed Layer (джерело правди)

Розташування: `_data/seed/`

Призначення: описує бізнес-сутності.

Приклад:

_data/seed/professions/professions.yml
_data/seed/industries/healthcare.yml
_data/seed/pricing/free.yml

Формат:

items:
  - slug: developers
    title: Developers
    description: Best AI tools for developers.
    tool_filters:
      categories:
        - coding
    limit: 20

Властивості:

- ✅ редагується вручну;
- ✅ єдине джерело правди;
- ✅ однакова структура для всіх типів (`items`).

---

### 2. Programmatic Definitions (згенерований артефакт)

Розташування: `_data/programmatic/`

Призначення: повні описи сторінок у форматі, зрозумілому генератору.

Генерується з Seed через `scripts/seed_generator.py`.

Властивості:

- ❌ ніколи не редагувати вручну;
- ✅ завжди перегенерується з Seed;
- ✅ якщо змінити вручну — зміни будуть втрачені.

---

### 3. Pages (згенерований артефакт)

Розташування: `pages/programmatic/`

Призначення: фінальні Markdown-сторінки.

Генеруються з Programmatic Definitions через `scripts/programmatic_generator.py`.

Властивості:

- ❌ ніколи не редагувати вручну;
- ✅ завжди перегенеруються з Programmatic Definitions.

---

## Pipeline

Seed Data
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

---

## Consequences

### Переваги

- **Єдине джерело правди** — зміни вносяться тільки в Seed.
- **Масштабування** — нова сторінка = новий рядок у Seed, без коду.
- **Консистентність** — усі сторінки одного типу мають однакову структуру.
- **Аудит** — легко перевірити, які дані були додані (git diff у `_data/seed/`).
- **Розширюваність** — нові типи сторінок (industries, pricing, platforms) додаються через новий seed-файл без зміни коду.

### Компроміси

- **Залежність від генерації** — після зміни Seed потрібно запустити генератори.
- **Дублювання файлів** — одні й ті самі дані існують у двох форматах (Seed і Programmatic). Але це компенсується автоматизацією.
- **Навчання** — нові учасники мають зрозуміти трирівневу архітектуру.

---

## Engineering Rules

1. **Ніколи не редагувати вручну:**
   - `_data/programmatic/`
   - `pages/programmatic/`

2. **Завжди змінювати Seed:**
   - `_data/seed/`

3. **Після зміни Seed запускати:**
   ```bash
   python3 scripts/seed_generator.py
   python3 scripts/programmatic_generator.py
    Якщо потрібно видалити сторінку — видалити з Seed.

    Нові типи сторінок додавати через новий seed-файл у відповідній папці _data/seed/.

Long-term Vision

Система більше не потребує Python-розробника для створення нових сторінок.

Будь-який контент-менеджер може:

    додати новий рядок у _data/seed/professions.yml;

    запустити два генератори;

    отримати нову сторінку на сайті.

Розробка зосереджується на:

    покращенні генераторів;

    розширенні можливостей Seed-моделі;

    автоматизації процесу генерації (CI/CD).

Related

    ADR-0008: Seed Data is the Source of Truth for Programmatic SEO

    ADR-0009: Programmatic generators are considered stable

    docs/architecture/programmatic-seo-overview.md (заплановано)
    EOF
