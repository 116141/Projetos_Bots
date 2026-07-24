let isBotRunning = false;

document.addEventListener('DOMContentLoaded', () => {
    fetchStatus();
    setInterval(fetchStatus, 3000);

    document.getElementById('btnToggleBot').addEventListener('click', toggleBotState);
    document.getElementById('btnScanNow').addEventListener('click', forceScan);
    document.getElementById('configForm').addEventListener('submit', saveConfig);
});

async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();

        isBotRunning = data.is_running;
        const badge = document.getElementById('statusBadge');
        const statusText = document.getElementById('statusText');
        const toggleBtn = document.getElementById('btnToggleBot');

        if (isBotRunning) {
            badge.classList.add('running');
            statusText.innerText = 'AUTO-POSTING 24/7 ATIVO';
            toggleBtn.className = 'btn btn-danger';
            toggleBtn.innerText = '⏸ Pausar Varredura';
        } else {
            badge.classList.remove('running');
            statusText.innerText = 'PARADO';
            toggleBtn.className = 'btn btn-primary';
            toggleBtn.innerText = '▶ Iniciar Varredura 24/7';
        }

        document.getElementById('metricDealsCount').innerText = data.deals_found_count;
        document.getElementById('metricClicks').innerText = data.total_clicks;
        document.getElementById('metricCommissions').innerText = `€${data.estimated_commissions.toFixed(2)}`;
        document.getElementById('metricTag').innerText = data.amazon_tag || 'N/A';

        renderDeals(data.posted_deals);

    } catch (err) {
        console.error('Erro ao buscar status do bot:', err);
    }
}

function renderDeals(deals) {
    const grid = document.getElementById('dealsGrid');
    if (!deals || deals.length === 0) {
        grid.innerHTML = '<p style="color: var(--text-muted); grid-column: 1/-1; text-align: center; padding: 40px;">Nenhuma oferta capturada ainda. Clique em "Iniciar Bot" ou "Procurar Oferta Agora".</p>';
        return;
    }

    grid.innerHTML = deals.map(d => `
        <div class="deal-card">
            <span class="deal-badge">-${d.discount_pct}% OFF</span>
            <img src="${d.image_url}" class="deal-img" alt="${d.title}">
            <h3 class="deal-title">${d.title}</h3>
            <div class="deal-price-box">
                <span class="deal-price">€${d.deal_price.toFixed(2)}</span>
                <span class="deal-old-price">€${d.original_price.toFixed(2)}</span>
            </div>
            <a href="${d.affiliate_url}" target="_blank" class="btn btn-secondary" style="font-size: 13px;">
                🛒 Link Afiliado Injetado
            </a>
        </div>
    `).join('');
}

async function toggleBotState() {
    const endpoint = isBotRunning ? '/api/stop' : '/api/start';
    await fetch(endpoint, { method: 'POST' });
    fetchStatus();
}

async function forceScan() {
    const res = await fetch('/api/scan', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
        fetchStatus();
    }
}

async function saveConfig(e) {
    e.preventDefault();
    const config = {
        telegram_bot_token: document.getElementById('inputBotToken').value,
        telegram_chat_id: document.getElementById('inputChatId').value,
        amazon_tag: document.getElementById('inputAmazonTag').value
    };

    await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    });

    alert('Configurações do Telegram salvas com sucesso!');
    fetchStatus();
}
