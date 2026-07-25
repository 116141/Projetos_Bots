import os
import sys

# Adicionar a pasta do hub portal ao sys.path para importação de assets e módulos
hub_dir = os.path.join(os.path.dirname(__file__), 'projects', 'bot_00_hub_portal')
if hub_dir not in sys.path:
    sys.path.insert(0, hub_dir)

# Importar a aplicação Flask principal do Hub Portal
from projects.bot_00_hub_portal.app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4999))
    app.run(host='0.0.0.0', port=port)
