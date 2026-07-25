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
            } else if (view === 'users') {
                showUsersView();
            } else {
                switchView(view, url, title);
            }
        });
    });

    const addUserForm = document.getElementById('addUserForm');
    if (addUserForm) {
        addUserForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('newUsername').value;
            const name = document.getElementById('newName').value;
            const password = document.getElementById('newPassword').value;
            const role = document.getElementById('newRole').value;

            try {
                const res = await fetch('/api/users/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, name, password, role })
                });
                const data = await res.json();
                if (data.status === 'success') {
                    alert('Utilizador criado com sucesso!');
                    window.location.reload();
                } else {
                    alert(data.message || 'Erro ao criar utilizador!');
                }
            } catch (err) {
                alert('Erro na comunicação com o servidor!');
            }
        });
    }
});

function updateClock() {
    const now = new Date();
    document.getElementById('liveClock').innerText = now.toLocaleTimeString('pt-PT');
}

function showOverview() {
    document.getElementById('viewTitle').innerText = '🌐 Visão Geral do Hub (Todos os Bots)';
    document.getElementById('overviewView').style.display = 'block';
    document.getElementById('usersView').style.display = 'none';
    document.getElementById('botFrame').style.display = 'none';
}

function showUsersView() {
    document.getElementById('viewTitle').innerText = '🔐 Gestão de Acesso & Utilizadores';
    document.getElementById('overviewView').style.display = 'none';
    document.getElementById('usersView').style.display = 'block';
    document.getElementById('botFrame').style.display = 'none';
}

function switchView(viewKey, url, title) {
    document.getElementById('viewTitle').innerText = title;
    document.getElementById('overviewView').style.display = 'none';
    document.getElementById('usersView').style.display = 'none';

    const iframe = document.getElementById('botFrame');
    iframe.style.display = 'block';
    iframe.src = url;

    document.querySelectorAll('.nav-item').forEach(i => {
        if (i.dataset.view === viewKey) {
            i.classList.add('active');
        } else {
            i.classList.remove('active');
        }
    });
}

async function logout() {
    if (confirm('Tem a certeza que deseja terminar sessão?')) {
        await fetch('/api/logout', { method: 'POST' });
        window.location.href = '/login';
    }
}

async function deleteUser(username) {
    if (confirm(`Tem a certeza que deseja eliminar o utilizador "${username}"?`)) {
        try {
            const res = await fetch('/api/users/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username })
            });
            const data = await res.json();
            if (data.status === 'success') {
                window.location.reload();
            } else {
                alert(data.message || 'Erro ao eliminar utilizador!');
            }
        } catch (err) {
            alert('Erro de comunicação!');
        }
    }
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
