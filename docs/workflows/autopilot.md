# Autopilot Workflow

## Опис

`autopilot.yml` — це GitHub Actions workflow, який запускається щодня о 8:00 UTC і виконує повний цикл оновлення сайту:

1. Збір нових інструментів з Product Hunt (`harvest.py`).
2. Генерація програмних визначень із Seed-даних (`seed_generator.py`).
3. Генерація програмних сторінок (`programmatic_generator.py`).
4. Збірка Jekyll (`bundle exec jekyll build`).
5. Коміт і пуш змін у репозиторій.

## Ручний запуск

Можна запустити вручну з вкладки **Actions** на GitHub, натиснувши `Run workflow`.

## Необхідні секрети

- `PH_API_TOKEN` — токен Product Hunt Developer API.
- `GEMINI_API_KEY` — ключ Google Gemini API (для генерації оглядів).

## Логування

Логи workflow доступні в GitHub Actions. У разі помилок workflow зупиняється, але зміни не комітяться.

## Виключення з коміту

Workflow комітить тільки зміни в:
- `_tools/` (нові інструменти)
- `_data/programmatic/` (оновлені програмні визначення)
- `pages/programmatic/` (оновлені сторінки)
- `_site/` (оновлений sitemap.xml)

Якщо змін немає — коміт не створюється.
