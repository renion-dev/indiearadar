---
layout: page
title: All Tools
description: AI tools for indie hackers. Updated daily.
---

<style>
  /* Додаткові стилі для сторінки */
  .tools-hero {
    text-align: center;
    padding: 4rem 0 3rem;
    position: relative;
  }
  .tools-hero::before {
    content: '';
    position: absolute;
    top: -30%;
    left: 50%;
    transform: translateX(-50%);
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%);
    pointer-events: none;
  }
  .tools-hero h1 {
    font-size: clamp(2.5rem, 6vw, 4rem);
    margin-bottom: 0.5rem;
  }
  .tools-hero .sub {
    font-size: 1.2rem;
    color: var(--text-secondary);
    max-width: 500px;
    margin: 0 auto 1.5rem;
  }
  .tools-stats {
    display: flex;
    justify-content: center;
    gap: 2.5rem;
    flex-wrap: wrap;
    margin-top: 1.5rem;
  }
  .tools-stats .stat-item {
    text-align: center;
  }
  .tools-stats .stat-number {
    font-size: 1.8rem;
    font-weight: 800;
    font-family: var(--font-mono);
    background: var(--accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .tools-stats .stat-label {
    font-size: 0.85rem;
    color: var(--text-muted);
    display: block;
  }

  /* Sticky-фільтри */
  .filter-bar {
    position: sticky;
    top: 64px;
    z-index: 50;
    background: rgba(10,10,15,0.85);
    backdrop-filter: blur(12px);
    padding: 1rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
  }
  .filter-bar .container {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
  }
  .filter-bar .filter-label {
    color: var(--text-muted);
    font-size: 0.85rem;
    font-weight: 600;
    margin-right: 0.5rem;
  }
  .filter-pill {
    padding: 0.4rem 1rem;
    border-radius: var(--radius-full);
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text-secondary);
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
  }
  .filter-pill:hover {
    border-color: var(--border-hover);
    color: var(--text-primary);
  }
  .filter-pill.active {
    background: var(--accent-primary);
    border-color: var(--accent-primary);
    color: white;
    box-shadow: 0 0 20px rgba(99,102,241,0.3);
  }
  /* Кольори категорій */
  .filter-pill[data-filter="content-creation"] { --cat-color: #a78bfa; }
  .filter-pill[data-filter="code"] { --cat-color: #60a5fa; }
  .filter-pill[data-filter="design"] { --cat-color: #f472b6; }
  .filter-pill[data-filter="marketing"] { --cat-color: #fb923c; }
  .filter-pill[data-filter="productivity"] { --cat-color: #34d399; }
  .filter-pill[data-filter="analytics"] { --cat-color: #22d3ee; }
  .filter-pill[data-filter="automation"] { --cat-color: #fbbf24; }
  .filter-pill.active[data-filter] {
    background: var(--cat-color, var(--accent-primary));
    border-color: var(--cat-color, var(--accent-primary));
  }

  /* Сітка карток */
  .tools-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.5rem;
  }
  .no-results {
    grid-column: 1 / -1;
    text-align: center;
    padding: 4rem 1rem;
    color: var(--text-muted);
    font-size: 1.1rem;
  }

  @media (max-width: 600px) {
    .tools-grid { grid-template-columns: 1fr; }
    .filter-bar .container { gap: 0.3rem; }
    .filter-pill { font-size: 0.75rem; padding: 0.3rem 0.7rem; }
  }
</style>

<!-- HERO -->
<section class="tools-hero">
  <h1>🔍 Discover the best tools<br>for indie hackers.</h1>
  <p class="sub">Curated AI tools, SaaS, and open‑source gems — all in one place.</p>
  <div style="max-width: 500px; margin: 0 auto 1.5rem;">
    <input type="text" id="searchTools" placeholder="Search tools by name, tag, or category…" style="width:100%; padding:0.8rem 1.2rem; border-radius:var(--radius-full); border:1px solid var(--border); background:var(--bg-card); color:var(--text-primary); font-size:1rem; outline:none; transition:border 0.2s;" onfocus="this.style.borderColor='var(--accent-primary)'" onblur="this.style.borderColor='var(--border)'">
  </div>
  <div class="tools-stats">
    <div class="stat-item">
      <span class="stat-number">{{ site.tools | size }}</span>
      <span class="stat-label">Tools</span>
    </div>
    <div class="stat-item">
      {% assign categories = site.tools | map: 'category' | compact | uniq %}
      <span class="stat-number">{{ categories | size }}</span>
      <span class="stat-label">Categories</span>
    </div>
    <div class="stat-item">
      {% assign open_source = site.tools | where_exp: 'tool', 'tool.pricing contains "open source" or tool.pricing contains "Open Source" or tool.tags contains "open-source" or tool.tags contains "Open Source"' %}
      <span class="stat-number">{{ open_source | size }}</span>
      <span class="stat-label">Open Source</span>
    </div>
    <div class="stat-item">
      <span class="stat-number">📅</span>
      <span class="stat-label">Updated {{ site.time | date: "%b %d" }}</span>
    </div>
  </div>
</section>

<!-- Sticky фільтри -->
<div class="filter-bar">
  <div class="container">
    <span class="filter-label">Category:</span>
    <button class="filter-pill active" data-filter="all">All</button>
    <button class="filter-pill" data-filter="content-creation">Content</button>
    <button class="filter-pill" data-filter="code">Code</button>
    <button class="filter-pill" data-filter="design">Design</button>
    <button class="filter-pill" data-filter="marketing">Marketing</button>
    <button class="filter-pill" data-filter="productivity">Productivity</button>
    <button class="filter-pill" data-filter="analytics">Analytics</button>
    <button class="filter-pill" data-filter="automation">Automation</button>
  </div>
</div>

<!-- Сітка -->
<div class="container" style="padding-top:0;">
  <div class="tools-grid" id="toolsGrid">
    {% assign sorted_tools = site.tools | sort: 'date' | reverse %}
    {% for tool in sorted_tools %}
      {% include tool-card.html tool=tool %}
    {% endfor %}
  </div>
</div>

<!-- JavaScript для фільтрів та пошуку -->
<script>
  document.addEventListener('DOMContentLoaded', function() {
    const grid = document.getElementById('toolsGrid');
    const cards = grid.querySelectorAll('.tool-card');
    const filterPills = document.querySelectorAll('.filter-pill');
    const searchInput = document.getElementById('searchTools');

    function filterTools(category) {
      cards.forEach(card => {
        const cardCat = card.dataset.category;
        card.style.display = (category === 'all' || cardCat === category) ? 'flex' : 'none';
      });
      // Показати повідомлення, якщо нічого не знайдено
      const visible = grid.querySelectorAll('.tool-card[style*="display: flex"]');
      let noMsg = grid.querySelector('.no-results');
      if (visible.length === 0) {
        if (!noMsg) {
          noMsg = document.createElement('div');
          noMsg.className = 'no-results';
          noMsg.textContent = '😕 No tools found for this category.';
          grid.appendChild(noMsg);
        }
        noMsg.style.display = 'block';
      } else if (noMsg) {
        noMsg.style.display = 'none';
      }
    }

    filterPills.forEach(pill => {
      pill.addEventListener('click', function() {
        filterPills.forEach(p => p.classList.remove('active'));
        this.classList.add('active');
        filterTools(this.dataset.filter);
        if (searchInput) searchInput.value = '';
      });
    });

    if (searchInput) {
      searchInput.addEventListener('input', function() {
        const query = this.value.toLowerCase().trim();
        cards.forEach(card => {
          const text = card.textContent.toLowerCase();
          card.style.display = text.includes(query) ? 'flex' : 'none';
        });
        filterPills.forEach(p => p.classList.remove('active'));
        document.querySelector('.filter-pill[data-filter="all"]')?.classList.add('active');
        const visible = grid.querySelectorAll('.tool-card[style*="display: flex"]');
        let noMsg = grid.querySelector('.no-results');
        if (visible.length === 0 && query.length > 0) {
          if (!noMsg) {
            noMsg = document.createElement('div');
            noMsg.className = 'no-results';
            noMsg.textContent = `😕 No tools found for “${query}”.`;
            grid.appendChild(noMsg);
          } else {
            noMsg.textContent = `😕 No tools found for “${query}”.`;
            noMsg.style.display = 'block';
          }
        } else if (noMsg) {
          noMsg.style.display = 'none';
        }
      });
    }
  });
</script>