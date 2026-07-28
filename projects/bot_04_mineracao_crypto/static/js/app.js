// YieldPro AI App.js

function updateTime() {
    const now = new Date();
    document.getElementById('currentTime').textContent = now.toLocaleTimeString();
}

setInterval(updateTime, 1000);
updateTime();

// Elementos
const toggleBtn = document.getElementById('btnToggleBot');
const saveBtn = document.getElementById('btnSaveConfig');
const statusBadge = document.getElementById('botStatusBadge');

// Fetch Status
async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        
        // Update Header and Status
        if (data.is_running) {
            statusBadge.textContent = 'MONITORANDO YIELD 24/7';
            statusBadge.className = 'badge online';
            toggleBtn.innerHTML = '<i class="fa-solid fa-stop"></i> Parar Motor';
            toggleBtn.className = 'btn btn-danger';
        } else {
            statusBadge.textContent = 'MOTOR PARADO';
            statusBadge.className = 'badge offline';
            toggleBtn.innerHTML = '<i class="fa-solid fa-play"></i> Iniciar Motor';
            toggleBtn.className = 'btn btn-primary';
        }

        // Update Top Cards
        document.getElementById('valUserBalance').textContent = data.user_balance.toFixed(2);
        document.getElementById('valActiveCoin').textContent = data.active_coin;
        document.getElementById('valDailyUsd').textContent = data.best_daily_usd.toFixed(4);
        document.getElementById('valTotalYield').textContent = data.total_yield_earned.toFixed(8);

        // Update Best Opportunity Card
        if (data.opportunities && data.opportunities.length > 0) {
            const best = data.opportunities[0];
            document.getElementById('bestPlatform').textContent = best.platform;
            document.getElementById('bestType').textContent = best.type;
            document.getElementById('bestApy').textContent = best.apy.toFixed(2);
            document.getElementById('bestMonthly').textContent = best.monthly_usd.toFixed(4);
            document.getElementById('bestRisk').textContent = best.risk;
            
            // Alert logic
            if (best.apy >= data.min_apy_alert) {
                document.getElementById('bestApy').style.color = '#ffaa00'; // Gold alert
            } else {
                document.getElementById('bestApy').style.color = 'var(--accent-green)';
            }
        }

        // Update Table
        const tbody = document.getElementById('yieldTableBody');
        tbody.innerHTML = '';
        
        if (data.opportunities && data.opportunities.length > 0) {
            data.opportunities.forEach((opp, index) => {
                const tr = document.createElement('tr');
                // Highlight row 1
                if(index === 0) tr.style.backgroundColor = 'rgba(0, 242, 254, 0.05)';
                
                tr.innerHTML = `
                    <td><strong>${opp.platform}</strong></td>
                    <td>${opp.type}</td>
                    <td style="color: var(--accent-green); font-weight: bold;">${opp.apy.toFixed(2)}%</td>
                    <td>$${opp.daily_usd.toFixed(4)}</td>
                    <td><span class="badge ${opp.risk.includes('Baixo') ? 'online' : 'offline'}">${opp.risk}</span></td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">Nenhuma oportunidade encontrada.</td></tr>';
        }
        
    } catch (err) {
        console.error('Erro ao buscar status', err);
    }
}

// Botões
toggleBtn.addEventListener('click', async () => {
    const isStop = toggleBtn.classList.contains('btn-danger');
    const endpoint = isStop ? '/api/stop' : '/api/start';
    
    await fetch(endpoint, { method: 'POST' });
    fetchStatus();
});

saveBtn.addEventListener('click', async () => {
    const config = {
        active_coin: document.getElementById('selectCoin').value,
        user_balance: document.getElementById('inputBalance').value,
        min_apy_alert: document.getElementById('inputMinApy').value
    };
    
    await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    });
    
    fetchStatus();
    
    // Pequeno feedback visual no botão
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fa-solid fa-check"></i> Salvo!';
    setTimeout(() => {
        saveBtn.innerHTML = originalText;
    }, 2000);
});

// Init
setInterval(fetchStatus, 3000);
fetchStatus();
