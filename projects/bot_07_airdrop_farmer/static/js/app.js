const toggleBtn = document.getElementById('btnToggle');
const generateBtn = document.getElementById('btnGenerate');
const statusBadge = document.getElementById('statusBadge');
const walletTableBody = document.getElementById('walletTableBody');
const logsContainer = document.getElementById('logsContainer');
const networkName = document.getElementById('networkName');

async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        
        // Update Network
        networkName.textContent = data.network;

        // Update Status Badge
        if (data.is_farming) {
            statusBadge.className = 'badge online';
            statusBadge.innerHTML = '<i class="fa-solid fa-satellite-dish fa-spin"></i> FARMING ATIVO';
            toggleBtn.className = 'btn btn-danger';
            toggleBtn.innerHTML = '<i class="fa-solid fa-stop"></i> PARAR FARMING';
            generateBtn.disabled = true;
            generateBtn.style.opacity = '0.5';
        } else {
            statusBadge.className = 'badge offline';
            statusBadge.innerHTML = '<i class="fa-solid fa-power-off"></i> OFFLINE';
            toggleBtn.className = 'btn btn-primary';
            toggleBtn.innerHTML = '<i class="fa-solid fa-play"></i> INICIAR FARMING';
            generateBtn.disabled = false;
            generateBtn.style.opacity = '1';
        }

        // Update Wallets
        walletTableBody.innerHTML = '';
        if (data.wallets && data.wallets.length > 0) {
            data.wallets.forEach(w => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="font-mono">${w.address}</td>
                    <td style="color: ${w.balance > 0 ? '#00e676' : 'var(--text-muted)'}">${w.balance.toFixed(4)} ETH</td>
                    <td><span class="badge ${w.txs > 0 ? 'online' : 'offline'}" style="display:inline-block">${w.txs} Txs</span></td>
                `;
                walletTableBody.appendChild(tr);
            });
        } else {
            walletTableBody.innerHTML = '<tr><td colspan="3" style="text-align:center;">Nenhuma carteira gerada.</td></tr>';
        }

        // Update Logs
        logsContainer.innerHTML = '';
        if (data.logs && data.logs.length > 0) {
            data.logs.forEach(log => {
                const div = document.createElement('div');
                div.className = 'log-entry';
                // highlight addresses or hashes
                let formattedLog = log.replace(/0x[a-fA-F0-9]{4,}/g, match => `<span style="color:#8b5cf6">${match}</span>`);
                if(formattedLog.includes('Erro') || formattedLog.includes('insuficiente')) {
                    formattedLog = `<span style="color:#ef4444">${formattedLog}</span>`;
                } else if(formattedLog.includes('✅')) {
                    formattedLog = `<span style="color:#00e676">${formattedLog}</span>`;
                }
                div.innerHTML = formattedLog;
                logsContainer.appendChild(div);
            });
        }
        
    } catch(e) {
        console.error("Erro de conexão", e);
    }
}

toggleBtn.addEventListener('click', async () => {
    const isStop = toggleBtn.classList.contains('btn-danger');
    const endpoint = isStop ? '/api/stop' : '/api/start';
    await fetch(endpoint, { method: 'POST' });
    fetchStatus();
});

generateBtn.addEventListener('click', async () => {
    const originalText = generateBtn.innerHTML;
    generateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> A GERAR...';
    generateBtn.disabled = true;
    
    await fetch('/api/generate', { method: 'POST' });
    await fetchStatus();
    
    generateBtn.innerHTML = originalText;
    generateBtn.disabled = false;
});

setInterval(fetchStatus, 3000);
fetchStatus();
