document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    setInterval(updateClock, 1000);
    checkHubStatus();
    setInterval(checkHubStatus, 3000);

    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const view = item.dataset.view;
            const url = item.dataset.url;
            const title = item.querySelector('.nav-item-left').innerText;

            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            if (view === 'overview') {
                showOverview();
            } else {
                switchView(view, url, title);
            }
        });
    });
});

function updateClock() {
    const now = new Date();
    document.getElementById('liveClock').innerText = now.toLocaleTimeString('pt-PT');
}

function showOverview() {
    document.getElementById('viewTitle').innerText = '🌐 Visão Geral do Hub (Todos os Bots)';
    document.getElementById('overviewView').style.display = 'block';
    document.getElementById('botFrame').style.display = 'none';
}

function switchView(viewKey, url, title) {
    document.getElementById('viewTitle').innerText = title;
    document.getElementById('overviewView').style.display = 'none';

    const iframe = document.getElementById('botFrame');
    iframe.style.display = 'block';
    iframe.src = url;

    // Highlight nav item
    document.querySelectorAll('.nav-item').forEach(i => {
        if (i.dataset.view === viewKey) {
            i.classList.add('active');
        } else {
            i.classList.remove('active');
        }
    });
}

async function checkHubStatus() {
    try {
        const res = await fetch('/api/hub_status');
        const data = await res.json();

        Object.entries(data).forEach(([key, info]) => {
            const dot = document.getElementById(`dot_${key}`);
            const cardStatus = document.getElementById(`card_status_${key}`);

            if (info.online) {
                if (dot) dot.classList.add('online');
                if (cardStatus) {
                    cardStatus.className = 'badge-status active';
                    cardStatus.innerText = info.is_running ? 'EM OPERAÇÃO 24/7' : 'ONLINE (PARADO)';
                }
            } else {
                if (dot) dot.classList.remove('online');
                if (cardStatus) {
                    cardStatus.className = 'badge-status';
                    cardStatus.innerText = 'OFFLINE';
                }
            }
        });

    } catch (err) {
        console.error('Erro ao verificar status do hub:', err);
    }
}
