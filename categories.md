---
layout: default
title: All AI Tool Categories
permalink: /categories/
---

<div class="container" style="padding: 2rem 0;">

  <h1 class="hero-title">All AI Tool Categories</h1>
  <p class="hero-description">Explore AI tools by category, profession, and use case.</p>

  <div class="categories-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1.2rem; margin-top: 2rem;">
    {% assign programmatic_pages = site.pages | where: "programmatic", true %}
    {% for page in programmatic_pages %}
      <a href="{{ page.url | relative_url }}" class="category-card" style="display: block; padding: 1.5rem 1rem; text-align: center; background: var(--bg-card, #1a1a24); border: 1px solid var(--border, #2a2a3a); border-radius: 12px; font-weight: 600; color: var(--text-primary, #f8fafc); transition: all 0.2s; text-decoration: none;">
        {{ page.title | replace: "Best AI Tools for ", "" }}
        <span style="display: block; font-size: 0.75rem; font-weight: 400; color: var(--text-muted, #64748b); margin-top: 0.3rem;">{{ page.tool_count | default: 0 }} tools</span>
      </a>
    {% endfor %}
  </div>

</div>
