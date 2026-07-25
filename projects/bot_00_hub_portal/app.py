import os
import json
import requests
from flask import Flask, render_template, jsonify, request, session, redirect, url_for

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)

USERS_FILE = os.path.join(os.path.dirname(__file__), 'users_db.json')

# Default users if file doesn't exist
DEFAULT_USERS = {
    "admin": {"password": "admin123", "role": "ADMIN", "name": "Edmilson (Administrador)"},
    "operador": {"password": "operador123", "role": "OPERATOR", "name": "Operador Convidado"}
}

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_USERS

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

BOT_SERVICES = {
    "bot_01": {"name": "QuantTrader AI", "icon": "🤖", "port": 5000, "url": "http://localhost:5000"},
    "bot_02": {"name": "DealHunter AI", "icon": "📢", "port": 5001, "url": "http://localhost:5001"},
    "bot_03": {"name": "ArbitragePro AI", "icon": "🔄", "port": 5002, "url": "http://localhost:5002"},
    "bot_04": {"name": "AutoMine Profitability AI", "icon": "⚡", "port": 5003, "url": "http://localhost:5003"},
    "bot_05": {"name": "Crypto Sentinel AI", "icon": "🧠", "port": 5004, "url": "http://localhost:5004"}
}

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    users = load_users()
    current_user = users.get(session['username'], {"role": "OPERATOR", "name": session['username']})
    return render_template('index.html', bots=BOT_SERVICES, current_user=current_user, users_db=users)

@app.route('/login')
def login_page():
    if 'username' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    username = str(data.get('username', '')).strip().lower()
    password = str(data.get('password', ''))

    users = load_users()
    if username in users and users[username]['password'] == password:
        session['username'] = username
        session['role'] = users[username]['role']
        return jsonify({"status": "success", "user": users[username]})

    return jsonify({"status": "error", "message": "Utilizador ou palavra-passe incorretos!"}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"status": "success"})

@app.route('/api/hub_status', methods=['GET'])
def get_hub_status():
    status_summary = {}
    for key, info in BOT_SERVICES.items():
        try:
            res = requests.get(f"{info['url']}/api/status", timeout=1.5)
            if res.status_code == 200:
                data = res.json()
                status_summary[key] = {
                    "online": True,
                    "is_running": data.get("is_running", False),
                    "details": data
                }
            else:
                status_summary[key] = {"online": False, "is_running": False}
        except Exception:
            status_summary[key] = {"online": False, "is_running": False}
            
    return jsonify(status_summary)

@app.route('/api/users/add', methods=['POST'])
def add_user():
    if session.get('role') != 'ADMIN':
        return jsonify({"status": "error", "message": "Apenas Administradores podem gerir utilizadores!"}), 403

    data = request.json or {}
    username = str(data.get('username', '')).strip().lower()
    password = str(data.get('password', ''))
    name = str(data.get('name', '')).strip()
    role = str(data.get('role', 'OPERATOR')).upper()

    if not username or not password:
        return jsonify({"status": "error", "message": "Utilizador e palavra-passe são obrigatórios!"}), 400

    users = load_users()
    users[username] = {"password": password, "role": role, "name": name or username}
    save_users(users)
    return jsonify({"status": "success", "users": users})

@app.route('/api/users/delete', methods=['POST'])
def delete_user():
    if session.get('role') != 'ADMIN':
        return jsonify({"status": "error", "message": "Apenas Administradores podem gerir utilizadores!"}), 403

    data = request.json or {}
    username = str(data.get('username', '')).strip().lower()

    if username == 'admin':
        return jsonify({"status": "error", "message": "Não é possível eliminar a conta Administrador principal!"}), 400

    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
    return jsonify({"status": "success", "users": users})

@app.route('/api/users/change_password', methods=['POST'])
def change_password():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Não autenticado!"}), 401

    data = request.json or {}
    new_password = str(data.get('new_password', '')).strip()

    if not new_password:
        return jsonify({"status": "error", "message": "A nova palavra-passe não pode estar vazia!"}), 400

    users = load_users()
    username = session['username']
    if username in users:
        users[username]['password'] = new_password
        save_users(users)
        return jsonify({"status": "success", "message": "Palavra-passe alterada com sucesso!"})

    return jsonify({"status": "error", "message": "Utilizador não encontrado!"}), 404

if __name__ == '__main__':
    # Initialize users DB if missing
    if not os.path.exists(USERS_FILE):
        save_users(DEFAULT_USERS)

    print("==========================================================")
    print("🌐 CENTRAL HUB BOT COMMAND CENTER - SERVIDOR MASTER (PORTA 4999)")
    print("Acesse no navegador: http://localhost:4999")
    print("==========================================================")
    app.run(host='0.0.0.0', port=4999, debug=True)
