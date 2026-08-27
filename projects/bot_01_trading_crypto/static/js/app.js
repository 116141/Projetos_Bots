let chart = null;
let isBotRunning = false;

document.addEventListener('DOMContentLoaded', () => {
    // Restaurar configs salvas
    const saved = localStorage.getItem('bot01_config');
    if (saved) {
        try {
            const config = JSON.parse(saved);
            if (config.symbol) document.getElementById('selectSymbol').value = config.symbol;
            if (config.strategy) document.getElementById('selectStrategy').value = config.strategy;
            if (config.trade_amount) document.getElementById('inputTradeAmount').value = config.trade_amount;
            if (config.take_profit) document.getElementById('inputTakeProfit').value = config.take_profit;
            if (config.stop_loss) document.getElementById('inputStopLoss').value = config.stop_loss;
            
            // Enviar silenciosamente para a backend
            fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
        } catch(err) {}
    }

    initChart();
    fetchStatus();
    setInterval(fetchStatus, 2000);

    document.getElementById('btnToggleBot').addEventListener('click', toggleBotState);
    document.getElementById('configForm').addEventListener('submit', saveConfig);
    document.getElementById('btnManualBuy').addEventListener('click', manualBuy);
    document.getElementById('btnManualSell').addEventListener('click', manualSell);
    document.getElementById('btnResetHistory').addEventListener('click', resetHistory);
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

        if (data.trading_mode) {
        document.getElementById('uiTradingMode').textContent = data.trading_mode;
      }
      
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
        document.getElementById('metricTradesCount').innerText = `🟢 ${data.winning_trades_count || 0} Certas | 🔴 ${data.losing_trades_count || 0} Falhadas`;

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
            const minP = Math.min(...data.price_history) - 20;
            const maxP = Math.max(...data.price_history) + 20;
            chart.options.scales.y.min = Math.floor(minP);
            chart.options.scales.y.max = Math.ceil(maxP);
            
            chart.data.labels = data.price_history.map((_, i) => `${i + 1}s`);
            chart.data.datasets[0].data = data.price_history;
            chart.update('none');
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
    if (e) e.preventDefault();
    const config = {
        trading_mode: document.getElementById('selectTradingMode') ? document.getElementById('selectTradingMode').value : 'LIVE',
        symbol: document.getElementById('selectSymbol').value,
        strategy: document.getElementById('selectStrategy').value,
        trade_amount: parseFloat(document.getElementById('inputTradeAmount').value),
        take_profit: parseFloat(document.getElementById('inputTakeProfit').value),
        stop_loss: parseFloat(document.getElementById('inputStopLoss').value)
    };

    // Guardar no browser do utilizador para sobreviver ao Vercel
    localStorage.setItem('bot01_config', JSON.stringify(config));

    await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    });

    if (e) alert('Configurações do bot atualizadas com sucesso!');
    fetchStatus();
}

async function manualBuy() {
    if (!confirm("Deseja executar uma COMPRA MANUAL a mercado agora?")) return;
    try {
        const res = await fetch('/api/buy', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        fetchStatus();
    } catch(err) {
        alert("Erro ao enviar ordem de compra manual.");
    }
}

async function manualSell() {
    if (!confirm("Deseja executar uma VENDA MANUAL a mercado agora?")) return;
    try {
        const res = await fetch('/api/sell', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        fetchStatus();
    } catch(err) {
        alert("Erro ao enviar ordem de venda manual.");
    }
}

async function resetHistory() {
    if (!confirm("Tem a certeza que deseja LIMPAR TODO O HISTÓRICO e reiniciar o contador do PNL a $0.00?")) return;
    try {
        const res = await fetch('/api/reset', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        fetchStatus();
    } catch(err) {
        alert("Erro ao resetar histórico do bot.");
    }
}
