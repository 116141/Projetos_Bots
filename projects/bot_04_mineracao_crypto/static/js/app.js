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
            statusText.innerText = 'MINERAÇÃO & AUTO-SWITCH ATIVOS';
            toggleBtn.className = 'btn btn-danger';
            toggleBtn.innerText = '⏸ Pausar Mineração';
        } else {
            badge.classList.remove('running');
            statusText.innerText = 'PARADO';
            toggleBtn.className = 'btn btn-primary';
            toggleBtn.innerText = '▶ Iniciar Mineração 24/7';
        }

        document.getElementById('metricActiveCoin').innerText = data.active_coin || '---';
        document.getElementById('metricActiveAlgo').innerText  = (data.coin_rankings || []).find(c => c.is_active)?.algo || '';
        document.getElementById('metricNetDaily').innerText    = `$${(data.active_net_daily || 0).toFixed(4)} / dia`;
        document.getElementById('metricMonthlyEst').innerText  = `$${(data.active_monthly_est || 0).toFixed(2)} / mês`;
        document.getElementById('metricPower').innerText       = `${data.power_consumption_watts}W (${data.rig_hashrate_mhs} MH/s)`;
        document.getElementById('metricElecCost').innerText    = `$${(data.electricity_cost_kwh || 0).toFixed(3)} / kWh`;

        // Lucro acumulado na sessão
        document.getElementById('metricNetProfit').innerText  = `$${(data.net_profit_usd || 0).toFixed(6)}`;
        document.getElementById('metricMinedTotal').innerText = `Minerado: $${(data.total_mined_usd || 0).toFixed(6)} | Energia: $${(data.total_electricity_usd || 0).toFixed(6)}`;

        // Estado da conta NiceHash
        const rigsEl  = document.getElementById('metricNicehashRigs');
        const statEl  = document.getElementById('metricNicehashStatus');
        if (data.nicehash_rigs_count > 0) {
            rigsEl.innerText = `✅ ${data.nicehash_rigs_count} Rig(s) Ativo(s)`;
            rigsEl.style.color = 'var(--accent-green)';
        } else if (data.account_accessible) {
            rigsEl.innerText = '⚠️ Conta acessível';
            rigsEl.style.color = 'var(--accent-orange)';
        } else {
            rigsEl.innerText = 'ℹ️ Sem hardware';
            rigsEl.style.color = 'var(--text-muted)';
        }
        statEl.innerText = data.nicehash_rigs_status || '';

        renderRankings(data.coin_rankings);
        renderSwitchLog(data.switch_history);

    } catch (err) {
        console.error('Erro ao buscar status de mineração:', err);
    }
}

function renderRankings(rankings) {
    const tbody = document.getElementById('coinRankingsBody');
    if (!rankings || rankings.length === 0) return;

    tbody.innerHTML = rankings.map(r => `
        <tr>
            <td><strong>${r.name}</strong><br><small style="color:var(--text-muted)">${r.algo}</small></td>
            <td style="color: #00f2fe;">$${r.gross_daily.toFixed(4)}</td>
            <td style="color: var(--accent-orange);">$${r.elec_cost_daily.toFixed(4)}</td>
            <td style="color: var(--accent-green);"><strong>+$${r.net_daily.toFixed(4)}</strong></td>
            <td><span style="font-size:0.75rem; color:var(--text-muted);">${r.data_source || 'Estimativa'}</span></td>
            <td><span class="${r.is_active ? 'badge-active' : 'badge-idle'}">${r.is_active ? 'MINERANDO' : 'DISPONÍVEL'}</span></td>
        </tr>
    `).join('');
}

function renderSwitchLog(history) {
    const tbody = document.getElementById('switchLogBody');
    if (!history || history.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">Nenhuma troca efetuada ainda. O bot seleciona automaticamente a moeda mais rentável.</td></tr>';
        return;
    }

    tbody.innerHTML = history.map(h => `
        <tr>
            <td>${h.timestamp}</td>
            <td style="color: var(--text-muted);">${h.from_coin}</td>
            <td style="color: var(--accent-green);"><strong>${h.to_coin}</strong></td>
            <td style="color: var(--text-muted);">${h.reason}</td>
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
        hashrate: parseFloat(document.getElementById('inputHashrate').value),
        watts: parseFloat(document.getElementById('inputWatts').value),
        elec_cost: parseFloat(document.getElementById('inputElecCost').value),
        auto_switch: true
    };

    await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    });

    alert('Parâmetros de mineração salvos com sucesso!');
    fetchStatus();
}
