import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, jsonify, request
from farmer import AirdropFarmerEngine

app = Flask(__name__, static_folder='static', template_folder='templates')
bot = AirdropFarmerEngine()
bot.start_farming() # Iniciar automaticamente assim que o servidor acorda

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(bot.get_status())

@app.route('/api/start', methods=['POST'])
def start_bot():
    bot.start_farming()
    return jsonify({"status": "started", "is_farming": bot.is_farming})

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    bot.stop_farming()
    return jsonify({"status": "stopped", "is_farming": bot.is_farming})

@app.route('/api/generate', methods=['POST'])
def generate_wallets():
    if not bot.is_farming:
        bot.generate_wallets(3)
        return jsonify({"status": "generated", "count": len(bot.wallets)})
    return jsonify({"status": "error", "message": "Stop the bot first"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5006))
    print("==========================================================")
    print(f"🪂 AIRDROP FARMER - GHOST WALLETS (PORTA {port})")
    print("==========================================================")
    # Ensure there's at least 1 wallet on boot
    if len(bot.wallets) == 0:
        bot.generate_wallets(3)
    app.run(host='0.0.0.0', port=port, debug=False)
