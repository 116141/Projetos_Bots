let isBotRunning = false;

document.addEventListener('DOMContentLoaded', () => {
    fetchStatus();
    setInterval(fetchStatus, 2000);

    document.getElementById('btnToggleBot').addEventListener('click', toggleBotState);
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
            statusText.innerText = 'VARREDURA EM TEMPO REAL ATIVA';
            toggleBtn.className = 'btn btn-danger';
            toggleBtn.innerText = '⏸ Pausar Arbitragem';
        } else {
            badge.classList.remove('running');
            statusText.innerText = 'PARADO';
            toggleBtn.className = 'btn btn-primary';
            toggleBtn.innerText = '▶ Iniciar Arbitragem 24/7';
        }

        document.getElementById('metricEquity').innerText = `$${data.total_equity.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        document.getElementById('metricProfit').innerText = `+$${data.total_profit.toFixed(2)}`;
        document.getElementById('metricOpportunities').innerText = data.opportunities_found;
        document.getElementById('metricMinSpread').innerText = `${data.min_spread_pct}%`;
        document.getElementById('assetSymbol').innerText = data.symbol;

        renderExchangeGrid(data.latest_prices);
        renderTradeLog(data.executed_trades);

    } catch (err) {
        console.error('Erro ao buscar status de arbitragem:', err);
    }
}

function renderExchangeGrid(prices) {
    const grid = document.getElementById('exchangeGrid');
    if (!prices || Object.keys(prices).length === 0) return;

    const values = Object.values(prices);
    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);

    grid.innerHTML = Object.entries(prices).map(([ex, price]) => {
        let highlight = '';
        if (price === minVal) highlight = 'color: var(--accent-green);';
        if (price === maxVal) highlight = 'color: #00f2fe;';

        return `
            <div class="exchange-card">
                <span class="exchange-name">${ex}</span>
                <span class="exchange-price" style="${highlight}">$${price.toLocaleString('en-US', {minimumFractionDigits: 2})}</span>
            </div>
        `;
    }).join('');
}

function renderTradeLog(trades) {
    const tbody = document.getElementById('tradeLogBody');
    if (!trades || trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">Nenhuma arbitragem executada ainda. Clique em "Iniciar Arbitragem 24/7".</td></tr>';
        return;
    }

    tbody.innerHTML = trades.map(t => `
        <tr>
            <td>${t.timestamp}</td>
            <td><strong>${t.symbol}</strong></td>
            <td style="color: var(--accent-green);">Comprar na ${t.buy_exchange} ($${t.buy_price.toFixed(2)})</td>
            <td style="color: #00f2fe;">Vender na ${t.sell_exchange} ($${t.sell_price.toFixed(2)})</td>
            <td>+${t.gross_spread_pct.toFixed(2)}%</td>
            <td class="text-green">+${t.net_spread_pct.toFixed(2)}%</td>
            <td class="text-green"><strong>+$${t.net_profit.toFixed(2)}</strong></td>
            <td><span class="badge-executed">${t.status}</span></td>
        </tr>
    `).join('');
}

async function toggleBotState() {
    const endpoint = isBotRunning ? '/api/stop' : '/api/start';
    await fetch(endpoint, { method: 'POST' });
    fetchStatus();
}

async function saveConfig(e) {
    e.preventDefault();
    const config = {
        symbol: document.getElementById('selectSymbol').value,
        min_spread: parseFloat(document.getElementById('inputMinSpread').value),
        trade_amount: parseFloat(document.getElementById('inputTradeAmount').value)
    };

    await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    });

    alert('Configurações de Arbitragem salvas com sucesso!');
    fetchStatus();
}
