# Indie AI Radar

Autonomous AI tool curation directory for solopreneurs. Built with Jekyll, powered by Python + venv, hosted for free on GitHub Pages.

## Quick Start (Local)

```bash
# 1. Install Ruby dependencies
bundle config set --local path 'vendor/bundle'
bundle install

# 2. Run locally
bundle exec jekyll serve
# → http://localhost:4000/indiearadar/
```

## Python Automation (venv)

```bash
# 1. Create venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 2. Install Python deps
pip install -r requirements.txt

# 3. Run harvester (needs PH_API_TOKEN and GEMINI_API_KEY env vars)
python scripts/harvest.py
```

## GitHub Secrets Required

| Secret | Where to get | Free? |
|--------|-------------|-------|
| `PH_API_TOKEN` | [developer.producthunt.com](https://developer.producthunt.com) | ✅ Yes |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/app/apikey) | ✅ Yes (1500/day) |

## Structure

```
├── scripts/harvest.py      # Python automation (Product Hunt → Gemini → Markdown)
├── requirements.txt        # Python deps (requests, python-dotenv)
├── .github/workflows/      # GitHub Actions (venv + harvest + deploy)
├── _tools/                 # Tool reviews (auto-generated)
├── _layouts/               # Jekyll templates
├── assets/                 # CSS, JS, images
└── _config.yml             # Site config
```

## Automation Flow

```
GitHub Actions (daily cron)
    ↓
Python venv + scripts/harvest.py
    ↓
Product Hunt API → Filter AI tools → Gemini AI → Markdown
    ↓
Auto-commit → Jekyll build → GitHub Pages deploy
```

## License

MIT
