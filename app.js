// Dynamic Logic for Coffee Price Tracker
const productGrid = document.getElementById('productGrid');
const brandSearch = document.getElementById('brandSearch');
const syncBtn = document.getElementById('syncBtn');
const sourcesList = document.getElementById('sourcesList');
const filterBtns = document.querySelectorAll('.filter-btn');

const RETAILERS = ["Olímpica", "Éxito", "Carulla", "Jumbo", "Metro", "Makro", "D1", "Alkosto", "Ara", "PriceSmart"];
let currentFilter = 'all';
let currentData = [];
let currentSearchTerm = "";
let lastUpdateStr = "";

// Detect if running locally or in production
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:8000'
    : window.location.origin;

function renderSources() {
    sourcesList.innerHTML = '';
    RETAILERS.forEach(name => {
        const tag = document.createElement('div');
        tag.className = 'source-tag';
        tag.dataset.retailer = name;
        tag.innerHTML = `<span class="dot"></span> <span class="retailer-name">${name}</span> <span class="status-icon"></span>`;
        sourcesList.appendChild(tag);
    });
}

function updateRetailerStatus(retailer, status, message = '') {
    const tag = document.querySelector(`.source-tag[data-retailer="${retailer}"]`);
    if (!tag) return;

    tag.classList.remove('starting', 'success', 'error', 'skipped');
    tag.classList.add(status);

    const statusIcon = tag.querySelector('.status-icon');
    const icons = {
        'starting': '⏳',
        'success': '✓',
        'error': '✗',
        'skipped': '○'
    };
    statusIcon.textContent = icons[status] || '';

    if (message) {
        tag.title = message;
    }
}

function showFinalStats(progress) {
    const stats = {
        total: RETAILERS.length,
        success: 0,
        error: 0,
        skipped: 0
    };

    progress.forEach(p => {
        if (p.status === 'success') stats.success++;
        else if (p.status === 'error') stats.error++;
        else if (p.status === 'skipped') stats.skipped++;
    });

    const statsDiv = document.createElement('div');
    statsDiv.className = 'search-stats';
    statsDiv.innerHTML = `
        <strong>Resumen:</strong> 
        <span class="stat-success">${stats.success} exitosos</span> • 
        <span class="stat-error">${stats.error} errores</span> • 
        <span class="stat-skipped">${stats.skipped} omitidos</span>
    `;

    const existing = document.querySelector('.search-stats');
    if (existing) existing.remove();

    statusConsole.parentElement.insertBefore(statsDiv, statusConsole.nextSibling);
}

function formatPrice(price) {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        maximumFractionDigits: 0
    }).format(price);
}

function renderProducts(data = currentData) {
    productGrid.innerHTML = '';

    if (!data || data.length === 0) {
        productGrid.innerHTML = `<p style="grid-column: 1/-1; text-align: center; opacity: 0.5;">No hay resultados para "${currentSearchTerm}" en tiempo real.</p>`;
        return;
    }

    const filtered = data.filter(p => {
        return currentFilter === 'all' || p.category === currentFilter;
    });

    if (filtered.length === 0) {
        productGrid.innerHTML = `<p style="grid-column: 1/-1; text-align: center; opacity: 0.5;">No hay resultados en la categoría "${currentFilter}".</p>`;
        return;
    }

    filtered.forEach(p => {
        const minPrice = Math.min(...p.prices.map(pr => pr.price));

        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <div class="badge">${p.category}</div>
            <h3>${p.name}</h3>
            <div class="size">${p.size}</div>
            <div class="price-list">
                ${p.prices.sort((a, b) => a.price - b.price).map(pr => `
                    <div class="price-item">
                        <span class="market-name">${pr.supermarket}</span>
                        <span class="market-price">
                            ${formatPrice(pr.price)}
                            ${pr.price === minPrice ? '<span class="best-price">¡EL MEJOR!</span>' : ''}
                            <a href="${pr.url}" target="_blank" class="view-link">Ver en tienda →</a>
                        </span>
                    </div>
                `).join('')}
            </div>
        `;
        productGrid.appendChild(card);
    });
}

async function startSync() {
    const term = brandSearch.value.trim() || "cafe buendia";
    statusConsole.innerText = `Buscando "${term}" en tiempo real...`;
    syncBtn.disabled = true;
    syncBtn.style.opacity = "0.5";

    // Reset all retailers to neutral state
    document.querySelectorAll('.source-tag').forEach(tag => {
        tag.classList.remove('starting', 'success', 'error', 'skipped');
        tag.querySelector('.status-icon').textContent = '';
    });

    // Remove previous stats
    const existingStats = document.querySelector('.search-stats');
    if (existingStats) existingStats.remove();

    try {
        const response = await fetch(`${API_URL}/sync?q=${encodeURIComponent(term)}`);
        const result = await response.json();

        // Process progress updates
        if (result.progress && result.progress.length > 0) {
            result.progress.forEach(p => {
                updateRetailerStatus(p.retailer, p.status, p.message);
            });
            showFinalStats(result.progress);
        }

        if (result.status === "success") {
            const totalProducts = result.results.reduce((sum, r) => sum + r.prices.length, 0);
            statusConsole.innerText = `✓ Búsqueda completada: ${result.results.length} productos únicos, ${totalProducts} precios encontrados`;
            currentData = result.results;
            currentSearchTerm = result.query;
            lastUpdateStr = result.timestamp;

            updateUpdateInfo();
            renderProducts();
        } else {
            statusConsole.innerText = "Error: " + (result.message || "Desconocido");
        }
    } catch (err) {
        statusConsole.innerText = "Error: El servidor local no está respondiendo.";
        console.error(err);
    } finally {
        syncBtn.disabled = false;
        syncBtn.style.opacity = "1";
    }
}

function updateUpdateInfo() {
    const existing = document.querySelector('.sync-status');
    if (existing) existing.remove();

    if (lastUpdateStr) {
        const statusDiv = document.createElement('div');
        statusDiv.className = 'sync-status';
        statusDiv.innerHTML = `<span class="sync-dot"></span> Búsqueda en vivo para "${currentSearchTerm}": ${lastUpdateStr}`;
        document.querySelector('.search-container').appendChild(statusDiv);
    }
}

syncBtn.addEventListener('click', startSync);

filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.filter;
        renderProducts();
    });
});

// Initial Setup
renderSources();
renderProducts([]); // Empty start
