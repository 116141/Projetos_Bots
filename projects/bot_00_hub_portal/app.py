from flask import Flask, render_template, jsonify, request
import requests

app = Flask(__name__, static_folder='static', template_folder='templates')

BOT_SERVICES = {
    "bot_01": {"name": "QuantTrader AI", "icon": "🤖", "port": 5000, "url": "http://localhost:5000"},
    "bot_02": {"name": "DealHunter AI", "icon": "📢", "port": 5001, "url": "http://localhost:5001"},
    "bot_03": {"name": "ArbitragePro AI", "icon": "🔄", "port": 5002, "url": "http://localhost:5002"},
    "bot_04": {"name": "AutoMine Profitability AI", "icon": "⚡", "port": 5003, "url": "http://localhost:5003"},
    "bot_05": {"name": "Crypto Sentinel AI", "icon": "🧠", "port": 5004, "url": "http://localhost:5004"}
}

@app.route('/')
def index():
    return render_template('index.html', bots=BOT_SERVICES)

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

if __name__ == '__main__':
    print("==========================================================")
    print("🌐 CENTRAL HUB BOT COMMAND CENTER - SERVIDOR MASTER (PORTA 4999)")
    print("Acesse no navegador: http://localhost:4999")
    print("==========================================================")
    app.run(host='0.0.0.0', port=4999, debug=True)
