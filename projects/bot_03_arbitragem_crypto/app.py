import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, jsonify, request
from arbitrage_engine import ArbitrageBotEngine

app = Flask(__name__, static_folder='static', template_folder='templates')
bot = ArbitrageBotEngine()

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

@app.route('/api/scan', methods=['POST'])
def force_scan():
    trade = bot.scan_arbitrage_opportunities()
    return jsonify({"status": "success", "trade": trade})

@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.json or {}
    symbol = data.get('symbol', 'BTC/USDT')
    min_spread = float(data.get('min_spread', 0.4))
    trade_amount = float(data.get('trade_amount', 1000.0))
    trading_mode = data.get('trading_mode', 'SIMULATION')
    reset_now = bool(data.get('reset_now', False))
    
    bot.update_config(symbol, min_spread, trade_amount, trading_mode, reset_now=reset_now)
    return jsonify({"status": "updated", "config": data})

@app.route('/api/reset', methods=['POST'])
def reset_stats():
    bot.reset_stats()
    return jsonify({"status": "reset", "is_running": bot.is_running})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    print("==========================================================")
    print(f"🚀 ARBITRAGE PRO AI BOT - SERVIDOR WEB (PORTA {port})")
    print("==========================================================")
    app.run(host='0.0.0.0', port=port, debug=False)
