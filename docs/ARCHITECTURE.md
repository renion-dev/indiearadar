### 🧠 Поточний стек, логіка та архітектура Indie AI Radar

Ось повний зріз проєкту — як він влаштований, з чого складається і як працює. Це можна використовувати як документацію для себе або для залучення нових людей.

---

## 1. Технологічний стек

| Компонент | Технологія | Призначення |
|-----------|------------|-------------|
| **Генерація сайту** | Jekyll (Ruby) | Перетворює Markdown + YAML + Liquid у статичний HTML |
| **Мова скриптів** | Python 3.10+ | Збір даних, генерація YAML, нормалізація, автоматизація |
| **Хостинг** | GitHub Pages | Безкоштовний деплой статичного сайту |
| **CI/CD** | GitHub Actions | Автоматичний щоденний запуск (збір → генерація → деплой) |
| **База даних (файлова)** | `_data/`, `_tools/`, `_posts/` | YAML, Markdown, JSON — усе в репозиторії |
| **Аналітика посилань** | Dub.co | Короткі посилання, кліки, джерела трафіку |
| **Розсилка** | Buttondown | Email-підписка, дайджести |
| **Зовнішні API** | Product Hunt GraphQL, Google Gemini API | Збір інструментів, генерація оглядів |
| **Логотипи** | Каскадний завантажувач (unavatar, icon.horse, favicon.ico) | Автоматичне підтягування логотипів для інструментів |
| **OG-зображення** | Pollinations.ai (заглушка) / дефолтне зображення | Соціальна картинка для постів і сторінок |
| **Структуровані дані** | JSON-LD (Schema.org) | SEO-розмітка: CollectionPage, ItemList, FAQPage, SoftwareApplication |

---

## 2. Архітектура даних

Уся логіка побудована на **трирівневій моделі**, яка забезпечує масштабування без зміни коду:

```
Seed-дані (бізнес-сутності)
        ↓
Програмні визначення (артефакт)
        ↓
Сторінки (артефакт)
        ↓
Статичний сайт
```

### Рівень 1: Seed-дані (`_data/seed/`)
**Джерело істини.** Усе, що описує бізнес:
- Професії (`professions/professions.yml`)
- Індустрії, категорії, ціни, платформи (заплановано)

Приклад:
```yaml
items:
  - slug: developers
    title: Developers
    description: Best AI tools for developers.
    tool_filters:
      categories:
        - code
    limit: 20
    faq: [...]
```

### Рівень 2: Програмні визначення (`_data/programmatic/`)
**Артефакт.** Генеруються з Seed через `seed_generator.py`. Не редагуються вручну.

Структура відповідає таксономії:
```
_data/programmatic/
  best-tools/professions/developers.yml
  alternatives/cursor.yml
  collections/
  comparisons/
```

### Рівень 3: Сторінки (`pages/programmatic/`)
**Артефакт.** Генеруються з програмних визначень через `programmatic_generator.py`. Не редагуються вручну.

Містять:
- frontmatter (layout, title, permalink, programmatic: true, related_tools, tool_count, faq)
- тіло (рендериться через `_layouts/programmatic.html`)

---

## 3. Пайплайни (автоматизація)

### A. Щоденний збір інструментів (GitHub Actions)
- Запуск о 8:00 UTC
- `harvest.py` → Product Hunt API → нові інструменти в `_tools/`
- `seed_generator.py` → оновлення `_data/programmatic/`
- `programmatic_generator.py` → оновлення `pages/programmatic/`
- `jekyll build` → оновлення `_site/`
- Коміт і пуш змін

### B. Ручний збір за діапазон (для історичного наповнення)
- `harvest_range.py --days 180 --min-votes 10` → великий збір за період
- Використовується одноразово для наповнення каталогу

### C. Нормалізація даних
- `normalize_frontmatter.py` → виправляє `category`, `tags`, `rating`, `domain`, `affiliate_link`
- Запускається вручну при необхідності

### D. Синхронізація категорій
- `sync_categories.py` → автоматично додає нові категорії з інструментів у Seed

---

## 4. Логіка роботи компонентів

### `harvest.py`
- Отримує пости з Product Hunt за сьогодні
- Фільтрує за AI-релевантністю та голосами
- Генерує огляд через Gemini (якщо є ключ)
- Зберігає інструмент у `_tools/{slug}.md`
- Створює дайджест у `_posts/`

### `seed_generator.py`
- Читає `_data/seed/professions/professions.yml`
- Для кожного елемента `items` створює YAML-файл у `_data/programmatic/best-tools/professions/`
- Копіює `tool_filters`, `limit`, `faq`, `category`

### `programmatic_generator.py`
- Рекурсивно читає всі `_data/programmatic/**/*.yml`
- Для кожного визначення завантажує `_tools/*.md`
- Фільтрує інструменти за `tool_filters.categories`
- Обмежує кількість (`limit`)
- Генерує Markdown-файл у `pages/programmatic/` з `related_tools` у frontmatter

### `_layouts/programmatic.html`
- Рендерить сторінку з:
  - Hero-секція (title, description, stats)
  - Сітка інструментів (через `tool-card.html`)
  - Similar AI Tools (через `site.tools` і `page.category`)
  - FAQ (якщо є)
  - JSON-LD (через `_includes/structured-data.html`)

### `_includes/tool-card.html`
- Відображення картки інструменту
- Каскадне завантаження логотипів (SVG → unavatar → icon.horse → favicon → Google Favicon)
- Мета-дані: рейтинг, категорія, теги, кнопки Review / Visit

### `_includes/structured-data.html`
- Генерує JSON-LD:
  - `CollectionPage` (загальна інформація)
  - `ItemList` (список інструментів із `SoftwareApplication`)
  - `FAQPage` (якщо є)

---

## 5. Ключові принципи (ADR)

### ADR-0008: Seed — єдине джерело правди
- Усі бізнес-дані зберігаються в `_data/seed/`
- `_data/programmatic/` — артефакт генерації
- Не редагувати вручну

### ADR-0009: Генератори стабільні
- Не переробляти без реальних багів
- Весь розвиток — через розширення даних, а не коду

### ADR-0010: Seed-Driven Architecture
- Три рівні: Seed → Definitions → Pages
- Python відповідає за логіку, Jekyll — за рендеринг
- Нова сторінка = новий рядок у Seed

---

## 6. Поточні метрики (на момент написання)

| Показник | Значення |
|----------|----------|
| Інструментів у каталозі | 75+ |
| Програмних сторінок | 30+ |
| Блог-постів | 30+ |
| URL у sitemap | 140+ |
| Категорій інструментів | 5 (`code`, `content`, `design`, `marketing`, `productivity`) |
| Автоматизація | GitHub Actions (щоденний запуск) |
| Аналітика | Dub.co (посилання) |
| Email-підписка | Buttondown (назва розсилки: `indieradar`) |

---

## 7. Як додати нову сторінку (без коду)

1. Відкрий `_data/seed/professions/professions.yml`
2. Додай новий елемент у `items`:
   ```yaml
   - slug: new-category
     title: New Category
     description: Best AI tools for new category.
     tool_filters:
       categories:
         - category1
         - category2
     limit: 20
     faq:
       - question: Question?
         answer: Answer.
   ```
3. Запусти `python3 scripts/seed_generator.py` і `python3 scripts/programmatic_generator.py`
4. Нова сторінка з’явиться за адресою: `/best-ai-tools-for-new-category/`

---

## 8. Як додати новий інструмент (автоматично)

- GitHub Actions щодня додає нові інструменти з Product Hunt
- Або вручну: `python3 scripts/harvest.py`
- Або за діапазон: `python3 scripts/harvest_range.py --days 30 --min-votes 5`

---

## 9. Важливі файли та папки

| Шлях | Призначення |
|------|-------------|
| `_data/seed/` | Бізнес-дані (єдине джерело правди) |
| `_data/programmatic/` | Програмні визначення (артефакт) |
| `_tools/` | Інструменти (Markdown з frontmatter) |
| `_posts/` | Блог і дайджести |
| `pages/programmatic/` | Згенеровані програмні сторінки |
| `_includes/` | Частини шаблонів (header, footer, tool-card, structured-data) |
| `_layouts/` | Шаблони сторінок (default, home, post, tool, programmatic) |
| `assets/` | CSS, JS, зображення, OG-картинки |
| `scripts/` | Усі Python-скрипти (збір, генерація, нормалізація) |
| `.github/workflows/autopilot.yml` | GitHub Actions workflow |
| `docs/` | Документація (ADR, архітектура, roadmap) |

---

## 10. Дорожня карта (що далі)

- [ ] Збільшення каталогу до 300+ інструментів
- [ ] Розширення Seed-даних (індустрії, ціни, платформи)
- [ ] Покращення Related Tools (алгоритм рекомендацій)
- [ ] A/B тести для заголовків і CTA
- [ ] Автоматична генерація sitemap
- [ ] Підключення Google Search Console
- [ ] Запуск платної підписки або реклами

---

**Цей документ можна зберегти як `docs/ARCHITECTURE.md` і використовувати як довідник.** Якщо потрібно щось додати або уточнити — я доповню.