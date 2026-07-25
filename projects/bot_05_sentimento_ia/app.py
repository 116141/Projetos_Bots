from flask import Flask, render_template, jsonify, request
from sentinel_engine import CryptoSentinelEngine

app = Flask(__name__, static_folder='static', template_folder='templates')
bot = CryptoSentinelEngine()

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
    headline = bot.analyze_news_sentiment()
    return jsonify({"status": "success", "headline": headline})

if __name__ == '__main__':
    print("==========================================================")
    print("🚀 CRYPTO SENTINEL AI BOT - SERVIDOR WEB (PORTA 5004)")
    print("Acesse no navegador: http://localhost:5004")
    print("==========================================================")
    app.run(host='0.0.0.0', port=5004, debug=True)
