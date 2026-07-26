let isBotRunning = false;
let configLoaded = false;

document.addEventListener('DOMContentLoaded', () => {
    fetchStatus();
    setInterval(fetchStatus, 3000);

    document.getElementById('btnToggleBot').addEventListener('click', toggleBotState);
    document.getElementById('btnScanNow').addEventListener('click', forceScan);
    document.getElementById('configForm').addEventListener('submit', saveConfig);
});

function isValidTag(tag) {
    if (!tag) return false;
    const clean = tag.trim().lowerCase ? tag.trim().toLowerCase() : tag.trim();
    const invalid = ["", "edmilson_ali", "edmilson_shopee", "edmilson_ebay", "edmilson-20", "ex:tag", "undefined", "none"];
    return !invalid.includes(clean);
}

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
        document.getElementById('metricTag').innerText = data.amazon_tag || 'gilsoncarvalh-21';

        // Atualizar Painel de Status Multi-Afiliados
        const hasAmazon = isValidTag(data.amazon_tag);
        const hasShopee = isValidTag(data.shopee_tag);
        const hasAli = isValidTag(data.aliexpress_tag);

        updateAffBadge('amazon', hasAmazon, data.amazon_tag || 'gilsoncarvalh-21');
        updateAffBadge('shopee', hasShopee, data.shopee_tag || 'Aguardando ID');
        updateAffBadge('aliexpress', hasAli, data.aliexpress_tag || 'Aguardando ID');

        // Preencher inputs do formulário na primeira leitura
        if (!configLoaded) {
            if (data.telegram_bot_token) document.getElementById('inputBotToken').value = data.telegram_bot_token;
            if (data.telegram_chat_id) document.getElementById('inputChatId').value = data.telegram_chat_id;
            if (data.amazon_tag) document.getElementById('inputAmazonTag').value = data.amazon_tag;
            if (data.shopee_tag && isValidTag(data.shopee_tag)) document.getElementById('inputShopeeTag').value = data.shopee_tag;
            if (data.aliexpress_tag && isValidTag(data.aliexpress_tag)) document.getElementById('inputAliexpressTag').value = data.aliexpress_tag;
            configLoaded = true;
        }

        renderDeals(data.posted_deals);

    } catch (err) {
        console.error('Erro ao buscar status do bot:', err);
    }
}

function updateAffBadge(platform, isActive, tagValue) {
    const badge = document.getElementById(`badge_${platform}`);
    const tagEl = document.getElementById(`tag_${platform}`);
    if (badge && tagEl) {
        if (isActive) {
            badge.className = 'badge-status active';
            badge.innerText = 'ATIVO';
            tagEl.style.color = 'var(--accent-green)';
            tagEl.innerText = tagValue;
        } else {
            badge.className = 'badge-status';
            badge.innerText = 'PENDENTE';
            tagEl.style.color = '#ff9800';
            tagEl.innerText = 'Aguardando ID';
        }
    }
}

function renderDeals(deals) {
    const grid = document.getElementById('dealsGrid');
    if (!deals || deals.length === 0) {
        grid.innerHTML = '<p style="color: var(--text-muted); grid-column: 1/-1; text-align: center; padding: 40px;">Nenhuma oferta capturada ainda. Clique em "Iniciar Varredura 24/7" ou "Procurar Oferta Agora".</p>';
        return;
    }

    grid.innerHTML = deals.map(d => `
        <div class="deal-card" style="border: 1px solid ${d.has_valid_affiliate ? 'rgba(76,175,80,0.3)' : 'rgba(255,152,0,0.3)'}">
            <span class="deal-badge">-${d.discount_pct}% OFF</span>
            <img src="${d.image_url}" class="deal-img" alt="${d.title}">
            <h3 class="deal-title">${d.title}</h3>
            <div style="font-size: 11px; margin-bottom: 6px; color: var(--text-muted);">
                Plataforma: <strong>${d.platform || 'Amazon'}</strong> | Telegram: <span style="color: ${d.telegram_posted ? '#4caf50' : '#ff9800'}">${d.telegram_posted ? '✓ Enviado' : '🔒 Bloqueado (Sem Afiliado)'}</span>
            </div>
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
        amazon_tag: document.getElementById('inputAmazonTag').value,
        shopee_tag: document.getElementById('inputShopeeTag').value,
        aliexpress_tag: document.getElementById('inputAliexpressTag').value
    };

    await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    });

    alert('Configurações do Telegram e Afiliados salvas com sucesso!');
    fetchStatus();
}
