import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, jsonify, request
from bot_engine import TradingBotEngine

app = Flask(__name__, static_folder='static', template_folder='templates')
bot = TradingBotEngine()

@app.route('/ping', methods=['GET'])
def ping():
    bot.ensure_thread_running()
    return "PONG", 200

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
    symbol = data.get('symbol', 'BTC/USDT')
    strategy = data.get('strategy', 'MA_CROSSOVER')
    trade_amount = float(data.get('trade_amount', 500))
    take_profit = float(data.get('take_profit', 2.0))
    stop_loss = float(data.get('stop_loss', 1.0))
    trading_mode = data.get('trading_mode', None)
    
    bot.update_config(symbol, strategy, trade_amount, take_profit, stop_loss, trading_mode)
    return jsonify({"status": "updated", "config": data})

@app.route('/api/buy', methods=['POST'])
def manual_buy():
    success, msg = bot.manual_buy()
    return jsonify({"success": success, "message": msg})

@app.route('/api/sell', methods=['POST'])
def manual_sell():
    success, msg = bot.manual_sell()
    return jsonify({"success": success, "message": msg})

@app.route('/api/reset', methods=['POST'])
def reset_history():
    success, msg = bot.reset_history()
    return jsonify({"success": success, "message": msg})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("==========================================================")
    print(f"🚀 QUANTTRADER BOT DASHBOARD - INICIANDO SERVIDOR WEB (PORTA {port})...")
    print("==========================================================")
    app.run(host='0.0.0.0', port=port, debug=False)
