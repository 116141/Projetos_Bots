from flask import Flask, render_template, jsonify, request
from deal_engine import DealHunterEngine

app = Flask(__name__, static_folder='static', template_folder='templates')
bot = DealHunterEngine()

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
    deal = bot.scan_for_deals()
    return jsonify({"status": "success", "deal": deal})

@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.json or {}
    bot_token = data.get('telegram_bot_token', '')
    chat_id = data.get('telegram_chat_id', '')
    amazon_tag = data.get('amazon_tag', 'edmilson-20')
    
    bot.update_config(bot_token, chat_id, amazon_tag)
    return jsonify({"status": "updated", "config": data})

if __name__ == '__main__':
    print("==========================================================")
    print("🚀 DEALHUNTER AI BOT - AFILIADOS TELEGRAM SERVIDOR WEB")
    print("Acesse no navegador: http://localhost:5001")
    print("==========================================================")
    app.run(host='0.0.0.0', port=5001, debug=True)
