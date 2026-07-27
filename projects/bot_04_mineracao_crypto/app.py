import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, jsonify, request
from mining_engine import AutoMineEngine

app = Flask(__name__, static_folder='static', template_folder='templates')
bot = AutoMineEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(bot.get_status())

@app.route('/api/start', methods=['POST'])
def start_bot():
    bot.start()
    return jsonify({"status": "started", "is_running": bot.is_running})

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    bot.stop()
    return jsonify({"status": "stopped", "is_running": bot.is_running})

@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.json or {}
    hashrate = float(data.get('hashrate', 250.0))
    watts = float(data.get('watts', 600.0))
    elec_cost = float(data.get('elec_cost', 0.12))
    auto_switch = bool(data.get('auto_switch', True))
    
    bot.update_config(hashrate, watts, elec_cost, auto_switch)
    return jsonify({"status": "updated", "config": data})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    print("==========================================================")
    print(f"🚀 AUTOMINE PROFITABILITY AI BOT - SERVIDOR WEB (PORTA {port})")
    print("==========================================================")
    app.run(host='0.0.0.0', port=port, debug=False)
