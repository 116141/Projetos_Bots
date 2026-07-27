let isBotRunning = false;
let rawTradesList = [];

document.addEventListener('DOMContentLoaded', () => {
    fetchStatus();
    setInterval(fetchStatus, 2000);

    document.getElementById('btnToggleBot').addEventListener('click', toggleBotState);
    document.getElementById('configForm').addEventListener('submit', saveConfig);
    document.getElementById('selectPeriodFilter').addEventListener('change', filterAndRenderTrades);
    
    document.getElementById('btnResetDashboard').addEventListener('click', async () => {
        if (confirm('Deseja limpar todo o histórico anterior e reiniciar a contagem de lucros a $0.00 para a Conta Real?')) {
            await fetch('/api/reset', { method: 'POST' });
            alert('Painel limpo com sucesso! A contagem de lucros recomeçará do zero.');
            fetchStatus();
        }
    });
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

        if (data.last_execution_status) {
            const spanExec = document.getElementById('spanExecutionStatus');
            if (spanExec) {
                spanExec.innerText = data.last_execution_status;
            }
        }

        const isLiveMode = (data.trading_mode === 'LIVE');
        document.getElementById('equityTitle').innerText = isLiveMode ? 'Saldo Total Consolidado (CONTA REAL)' : 'Saldo Total (Banca Simulação)';
        document.getElementById('metricEquity').innerText = `$${data.total_equity.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        document.getElementById('metricProfit').innerText = `+$${data.total_profit.toFixed(2)}`;
        document.getElementById('metricOpportunities').innerText = data.opportunities_found;
        document.getElementById('assetSymbol').innerText = data.symbol;

        const binanceB = data.binance_balance || 0.0;
        const bybitB = data.bybit_balance || 0.0;
        document.getElementById('dualBalancesSub').innerText = `Binance: $${binanceB.toFixed(2)} | Bybit: $${bybitB.toFixed(2)}`;
        document.getElementById('metricExchangesSub').innerHTML = `💛 Binance: $${binanceB.toFixed(2)}<br>🖤 Bybit: $${bybitB.toFixed(2)}`;

        if (data.trading_mode && document.activeElement !== document.getElementById('selectTradingMode')) {
            document.getElementById('selectTradingMode').value = data.trading_mode;
        }
        if (data.symbol && document.activeElement !== document.getElementById('selectSymbol')) {
            document.getElementById('selectSymbol').value = data.symbol;
        }
        if (data.min_spread_pct !== undefined && document.activeElement !== document.getElementById('inputMinSpread')) {
            document.getElementById('inputMinSpread').value = data.min_spread_pct;
        }
        if (data.trade_amount !== undefined && document.activeElement !== document.getElementById('inputTradeAmount')) {
            document.getElementById('inputTradeAmount').value = data.trade_amount;
        }

        rawTradesList = data.executed_trades || [];
        renderExchangeGrid(data.latest_prices);
        filterAndRenderTrades();

    } catch (err) {
        console.error('Erro ao buscar status de arbitragem:', err);
    }
}

function filterAndRenderTrades() {
    const period = document.getElementById('selectPeriodFilter').value;
    const now = new Date();
    
    let filtered = rawTradesList.filter(t => {
        if (!t.date || period === 'TODOS') return true;
        
        const tradeDate = new Date(t.date);
        const diffDays = (now - tradeDate) / (1000 * 3600 * 24);

        if (period === 'HOJE') {
            return t.date === now.toISOString().split('T')[0];
        } else if (period === '7_DIAS') {
            return diffDays <= 7;
        } else if (period === '30_DIAS') {
            return diffDays <= 30;
        }
        return true;
    });

    renderTradeLog(filtered);
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
        trading_mode: document.getElementById('selectTradingMode').value,
        symbol: document.getElementById('selectSymbol').value,
        min_spread: parseFloat(document.getElementById('inputMinSpread').value),
        trade_amount: parseFloat(document.getElementById('inputTradeAmount').value)
    };

    await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    });

    alert(`Modo de Operação (${config.trading_mode === 'LIVE' ? 'CONTA REAL' : 'BANCA SIMULADA'}) e parâmetros salvos com sucesso!`);
    fetchStatus();
}
