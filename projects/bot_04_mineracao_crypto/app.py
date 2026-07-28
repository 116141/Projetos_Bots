import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, jsonify, request
from staking_engine import YieldEngine

app = Flask(__name__, static_folder='static', template_folder='templates')
bot = YieldEngine()

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
    active_coin = data.get('active_coin', 'USDT')
    user_balance = float(data.get('user_balance', 8.75))
    min_apy_alert = float(data.get('min_apy_alert', 10.0))
    
    bot.update_config(active_coin, user_balance, min_apy_alert)
    return jsonify({"status": "updated", "config": data})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    print("==========================================================")
    print(f"🚀 YIELD PRO AI - STAKING & DEFI MONITOR (PORTA {port})")
    print("==========================================================")
    app.run(host='0.0.0.0', port=port, debug=False)
