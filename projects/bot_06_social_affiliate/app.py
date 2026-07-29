import os
from flask import Flask, render_template, jsonify, request

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        "online": True,
        "is_running": False, # Não há processo 24/7 neste bot, apenas gerador sob demanda
        "status_message": "A aguardar chaves API (Gemini & Pexels)"
    })

@app.route('/api/generate', methods=['POST'])
def generate_content():
    data = request.json
    niche = data.get('niche', '')
    
    if not niche:
        return jsonify({"status": "error", "message": "Niche/Product required"}), 400
        
    # TODO: Implement AI Video Generation Engine
    # For now, return mock data
    mock_script = f"Hook: Did you know this {niche} trick?\nBody: It solves your biggest problem...\nCTA: Click the link in my bio to get yours!"
    
    return jsonify({
        "status": "success",
        "script": mock_script,
        "video_url": "#", # Future MP4 download URL
        "message": "Fábrica em construção. Módulo IA será ativado brevemente."
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5005))
    print("==========================================================")
    print(f"🎬 SOCIAL AFFILIATE AI - CONTENT FACTORY (PORTA {port})")
    print("==========================================================")
    app.run(host='0.0.0.0', port=port, debug=False)
