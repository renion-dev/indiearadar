---
layout: home
---

## Popular AI Tool Categories

<div class="categories-grid">
  <a href="/indiearadar/best-ai-tools-for-developers/" class="category-card">💻 Developers</a>
  <a href="/indiearadar/best-ai-tools-for-designers/" class="category-card">🎨 Designers</a>
  <a href="/indiearadar/best-ai-tools-for-marketers/" class="category-card">📈 Marketers</a>
  <a href="/indiearadar/best-ai-tools-for-founders/" class="category-card">🚀 Founders</a>
  <a href="/indiearadar/best-ai-tools-for-students/" class="category-card">🎓 Students</a>
  <a href="/indiearadar/best-ai-tools-for-content/" class="category-card">✍️ Content</a>
  <a href="/indiearadar/best-ai-tools-for-automation/" class="category-card">⚡ Automation</a>
  <a href="/indiearadar/best-ai-tools-for-analytics/" class="category-card">📊 Analytics</a>
</div>

<style>
.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1rem;
  margin: 1.5rem 0;
}
.category-card {
  display: block;
  padding: 1.2rem 0.8rem;
  text-align: center;
  background: var(--bg-card, #1a1a24);
  border: 1px solid var(--border, #2a2a3a);
  border-radius: 12px;
  font-weight: 600;
  color: var(--text-primary, #f8fafc);
  transition: all 0.2s;
  text-decoration: none;
  font-size: 1rem;
}
.category-card:hover {
  transform: translateY(-3px);
  border-color: var(--accent-primary, #6366f1);
  box-shadow: 0 8px 24px rgba(99,102,241,0.15);
}
</style>
{% include categories-grid.html %}
