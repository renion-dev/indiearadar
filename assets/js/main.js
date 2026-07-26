document.addEventListener('DOMContentLoaded', () => {
    // Меню-бургер
    const menuToggle = document.getElementById('menuToggle');
    const mainNav = document.getElementById('mainNav');

    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', () => {
            mainNav.classList.toggle('active');
            const spans = menuToggle.querySelectorAll('span');

            if (mainNav.classList.contains('active')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px,5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(5px,-5px)';
            } else {
                spans[0].style.transform = '';
                spans[1].style.opacity = '';
                spans[2].style.transform = '';
            }
        });
    }

    // Пошук
    const searchToggle = document.getElementById('searchToggle');
    const searchOverlay = document.getElementById('searchOverlay');
    const searchClose = document.getElementById('searchClose');
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');

    const openSearch = () => {
        if (searchOverlay) {
            searchOverlay.classList.add('active');
            setTimeout(() => {
                if (searchInput) searchInput.focus();
            }, 150);
        }
    };

    const closeSearch = () => {
        if (searchOverlay) searchOverlay.classList.remove('active');
    };

    if (searchToggle) searchToggle.addEventListener('click', openSearch);
    if (searchClose) searchClose.addEventListener('click', closeSearch);

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeSearch();
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            openSearch();
        }
    });

    if (searchInput && searchResults) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            if (query.length < 2) {
                searchResults.innerHTML = '';
                return;
            }

            const cards = document.querySelectorAll('.tool-card');
            let html = '';

            cards.forEach((card) => {
                const titleEl = card.querySelector('.tool-card-title');
                const taglineEl = card.querySelector('.tool-card-tagline, .tool-card-excerpt');
                const categoryEl = card.querySelector('.tool-card-category');
                const linkEl = card.querySelector('.tool-card-title a');

                const title = titleEl ? titleEl.textContent : '';
                const tagline = taglineEl ? taglineEl.textContent : '';
                const category = categoryEl ? categoryEl.textContent : '';
                const link = linkEl ? linkEl.href : '#';

                if (
                    title.toLowerCase().includes(query) ||
                    tagline.toLowerCase().includes(query) ||
                    category.toLowerCase().includes(query)
                ) {
                    html += `
                        <a href="${link}"
                           style="display:block;padding:12px 16px;border-bottom:1px solid var(--border);color:var(--text-primary);text-decoration:none;"
                           onmouseover="this.style.background='var(--bg-elevated)'"
                           onmouseout="this.style.background=''">
                            <div style="font-weight:600;margin-bottom:4px;">${title}</div>
                            <div style="font-size:0.875rem;color:var(--text-secondary);">${tagline.substring(0, 80)}...</div>
                        </a>
                    `;
                }
            });

            searchResults.innerHTML = html || '<div style="padding:16px;color:var(--text-muted);">No results found</div>';
        });
    }

    // Фільтр категорій
    const categoryPills = document.querySelectorAll('.category-pill');
    const toolCards = document.querySelectorAll('.tool-card');

    categoryPills.forEach((pill) => {
        pill.addEventListener('click', () => {
            categoryPills.forEach((p) => p.classList.remove('active'));
            pill.classList.add('active');

            const filter = pill.dataset.filter;
            toolCards.forEach((card) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(10px)';

                setTimeout(() => {
                    const shouldShow = (filter === 'all' || card.dataset.category === filter);
                    card.style.display = shouldShow ? '' : 'none';
                    if (shouldShow) {
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }
                }, 150);
            });
        });
    });

    // Попап підписки
    const popup = document.getElementById('newsletterPopup');
    const popupClose = document.getElementById('popupClose');
    const popupShown = sessionStorage.getItem('indiearadar_popup');

    const showPopup = () => {
        if (!popupShown && popup) {
            popup.classList.add('active');
            sessionStorage.setItem('indiearadar_popup', '1');
        }
    };

    setTimeout(showPopup, 30000);

    let scrollTriggered = false;
    window.addEventListener('scroll', () => {
        if (!scrollTriggered && (window.scrollY + window.innerHeight) / document.body.scrollHeight > 0.7) {
            scrollTriggered = true;
            showPopup();
        }
    });

    if (popupClose) {
        popupClose.addEventListener('click', () => {
            if (popup) popup.classList.remove('active');
        });
    }

    // Плавний скрол до якорів
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    // Lazy loading зображень
    const lazyImages = document.querySelectorAll('img[loading="lazy"]');
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.style.opacity = '0';
                    img.style.transition = 'opacity 0.5s ease';
                    img.onload = () => {
                        img.style.opacity = '1';
                    };
                    if (img.complete && img.naturalHeight !== 0) {
                        img.style.opacity = '1';
                    }
                    imageObserver.unobserve(img);
                }
            });
        });
        lazyImages.forEach((img) => imageObserver.observe(img));
    }
});