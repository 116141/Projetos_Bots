let chart = null;
let isBotRunning = false;

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    fetchStatus();
    setInterval(fetchStatus, 2000);

    document.getElementById('btnToggleBot').addEventListener('click', toggleBotState);
    document.getElementById('configForm').addEventListener('submit', saveConfig);
});

function initChart() {
    const ctx = document.getElementById('priceChart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Preço em Tempo Real ($)',
                data: [],
                borderColor: '#00f2fe',
                borderWidth: 2.5,
                backgroundColor: 'rgba(0, 242, 254, 0.08)',
                fill: true,
                tension: 0.3,
                pointRadius: 2,
                pointBackgroundColor: '#00f2fe'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono', size: 10 } }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono', size: 11 } }
                }
            }
        }
    });
}

async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();

        // Update Status Badge
        isBotRunning = data.is_running;
        const badge = document.getElementById('statusBadge');
        const statusText = document.getElementById('statusText');
        const toggleBtn = document.getElementById('btnToggleBot');

        if (isBotRunning) {
            badge.classList.add('running');
            statusText.innerText = 'EM OPERAÇÃO 24/7';
            toggleBtn.className = 'btn btn-danger';
            toggleBtn.innerText = '⏸ Pausar Bot';
        } else {
            badge.classList.remove('running');
            statusText.innerText = 'PARADO';
            toggleBtn.className = 'btn btn-primary';
            toggleBtn.innerText = '▶ Iniciar Bot';
        }

        // Update Metrics
        document.getElementById('metricEquity').innerText = `$${data.total_equity.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        document.getElementById('metricUSDT').innerText = `Disponível: $${data.usdt_balance.toLocaleString('en-US', {minimumFractionDigits: 2})} USDT`;

        const pnlElem = document.getElementById('metricPnL');
        const pnlPctElem = document.getElementById('metricPnLPct');
        const isPos = data.net_pnl >= 0;
        
        pnlElem.className = `metric-value ${isPos ? 'text-green' : 'text-red'}`;
        pnlElem.innerText = `${isPos ? '+' : ''}$${data.net_pnl.toFixed(2)}`;
        
        pnlPctElem.className = `metric-sub ${isPos ? 'text-green' : 'text-red'}`;
        pnlPctElem.innerText = `${isPos ? '+' : ''}${data.net_pnl_pct.toFixed(2)}%`;

        document.getElementById('metricWinRate').innerText = `${data.win_rate.toFixed(1)}%`;
        document.getElementById('metricTradesCount').innerText = `${data.total_trades_count} Operações Fechadas`;

        document.getElementById('assetName').innerText = data.symbol;
        document.getElementById('metricLivePrice').innerText = `$${data.current_price.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        document.getElementById('metricRSI').innerText = `RSI (14): ${data.rsi} | SMA7: $${data.sma_fast}`;

        // Strategy name display
        const stratMap = {
            'MA_CROSSOVER': 'Crossover Média Móvel (7/25)',
            'RSI_SCALPING': 'RSI Scalping',
            'GRID_TRADING': 'Grid Trading'
        };
        document.getElementById('currentStrategyName').innerText = stratMap[data.strategy] || data.strategy;

        // Update Chart
        if (data.price_history && data.price_history.length > 0) {
            chart.data.labels = data.price_history.map((_, i) => i + 1);
            chart.data.datasets[0].data = data.price_history;
            chart.update();
        }

        // Update Trade Log
        updateTradeLog(data.trades);

    } catch (err) {
        console.error('Erro ao buscar status do bot:', err);
    }
}

function updateTradeLog(trades) {
    const tbody = document.getElementById('tradeLogBody');
    if (!trades || trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Nenhuma operação efetuada ainda. Clique em "Iniciar Bot".</td></tr>';
        return;
    }

    tbody.innerHTML = trades.map(t => {
        const isBuy = t.type === 'BUY';
        const badgeClass = isBuy ? 'badge-buy' : 'badge-sell';
        const pnlText = isBuy ? '-' : `${t.pnl >= 0 ? '+' : ''}$${t.pnl.toFixed(2)} (${t.pnl_pct.toFixed(2)}%)`;
        const pnlColor = isBuy ? '' : (t.pnl >= 0 ? 'text-green' : 'text-red');

        return `
            <tr>
                <td>${t.timestamp}</td>
                <td><strong>${t.symbol}</strong></td>
                <td><span class="badge ${badgeClass}">${t.type}</span></td>
                <td>$${t.price.toFixed(2)}</td>
                <td>${t.amount.toFixed(5)}</td>
                <td class="${pnlColor}">${pnlText}</td>
                <td style="color: var(--text-muted);">${t.reason}</td>
            </tr>
        `;
    }).join('');
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
        strategy: document.getElementById('selectStrategy').value,
        trade_amount: parseFloat(document.getElementById('inputTradeAmount').value),
        take_profit: parseFloat(document.getElementById('inputTakeProfit').value),
        stop_loss: parseFloat(document.getElementById('inputStopLoss').value)
    };

    await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    });

    alert('Configurações do bot atualizadas com sucesso!');
    fetchStatus();
}
