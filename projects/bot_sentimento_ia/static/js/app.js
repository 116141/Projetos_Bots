let isBotRunning = false;

document.addEventListener('DOMContentLoaded', () => {
    fetchStatus();
    setInterval(fetchStatus, 2000);

    document.getElementById('btnToggleBot').addEventListener('click', toggleBotState);
    document.getElementById('btnScanNow').addEventListener('click', forceScan);
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
            statusText.innerText = 'MONITORIZAÇÃO IA EM TEMPO REAL ATIVA';
            toggleBtn.className = 'btn btn-danger';
            toggleBtn.innerText = '⏸ Pausar Sentinela';
        } else {
            badge.classList.remove('running');
            statusText.innerText = 'PARADO';
            toggleBtn.className = 'btn btn-primary';
            toggleBtn.innerText = '▶ Iniciar Varredura 24/7';
        }

        document.getElementById('metricFearGreed').innerText = `${data.fear_greed_index} / 100`;
        document.getElementById('metricFearGreedText').innerText = data.fear_greed_text;
        document.getElementById('metricArticles').innerText = data.articles_analyzed_count;
        document.getElementById('metricSignals').innerText = data.signals_emitted_count;

        renderNewsFeed(data.sentiment_history);
        renderSignalsLog(data.signals_log);

    } catch (err) {
        console.error('Erro ao buscar status do Sentinel AI:', err);
    }
}

function renderNewsFeed(news) {
    const tbody = document.getElementById('newsFeedBody');
    if (!news || news.length === 0) return;

    tbody.innerHTML = news.map(n => `
        <tr>
            <td>${n.timestamp}</td>
            <td><strong>${n.source}</strong></td>
            <td>${n.title}</td>
            <td><span class="badge-bullish">${n.sentiment_type}</span></td>
            <td style="color: var(--accent-purple);"><strong>${n.impact_score}%</strong></td>
        </tr>
    `).join('');
}

function renderSignalsLog(signals) {
    const tbody = document.getElementById('signalsLogBody');
    if (!signals || signals.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">Nenhum sinal VIP disparado ainda.</td></tr>';
        return;
    }

    tbody.innerHTML = signals.map(s => `
        <tr>
            <td>${s.timestamp}</td>
            <td><strong>${s.asset}</strong></td>
            <td><span class="badge-signal">${s.signal_type}</span></td>
            <td style="color: var(--accent-green);"><strong>${s.confidence_pct}%</strong></td>
            <td style="color: var(--text-muted);">${s.reason}</td>
        </tr>
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
