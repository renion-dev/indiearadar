---
layout: page
title: About
description: How Indie AI Radar works and why it exists.
---
## What is Indie AI Radar?

Indie AI Radar is an **autonomous curation system** that discovers, reviews, and publishes AI tools specifically for solopreneurs and indie hackers.

Unlike traditional directories that rely on manual submissions or paid placements, this site is **powered entirely by open-source automation**:

- 🤖 **Discovery** — Python script scans Product Hunt, GitHub, Reddit daily
- ✍️ **Reviews** — Google Gemini generates honest, detailed reviews
- 🎨 **Images** — AI generates OG images automatically via Pollinations.ai
- 📧 **Distribution** — Newsletter goes out via Buttondown (free up to 1000 subs)
- 🔄 **Updates** — Content refreshes daily via GitHub Actions without human intervention

## Why I Built This

As an indie hacker, I was tired of:
- Sifting through hundreds of AI tools to find the 5% that actually work
- Reading generic "top 50 AI tools" lists with zero depth
- Missing early access to tools that could 10x my workflow

This site solves that by curating **only** tools that meet three criteria:

1. **Actually useful** for solo builders (not enterprise sales decks)
2. **Has a free tier** or reasonable indie pricing
3. **Shipped recently** — no 3-year-old "AI tools" that are just ChatGPT wrappers

## How It Works

```
Data Sources → Python Script → Gemini AI → Jekyll Site → GitHub Pages
     ↓              ↓              ↓            ↓              ↓
Product Hunt   harvest.py    Generate      Markdown      Auto-Deploy
GitHub API     (venv)        Review        _tools/       (Actions)
```

## Tech Stack (All Free, No Trials)

| Layer | Tool | Cost |
|-------|------|------|
| Site | Jekyll + GitHub Pages | $0 |
| Automation | Python 3 + venv | $0 |
| CI/CD | GitHub Actions | $0 |
| AI Text | Google Gemini API | $0 (1500 req/day) |
| AI Images | Pollinations.ai | $0 (no API key) |
| Newsletter | Buttondown | $0 (1000 subs) |
| Analytics | Google Analytics 4 | $0 |

**Total monthly cost: $0**

## Contact
- Twitter/X: [@reniondev](https://twitter.com/reniondev)
- GitHub: [renion-dev/indiearadar](https://github.com/renion-dev/indiearadar)

*Built with curiosity, caffeine, and zero budget.*
