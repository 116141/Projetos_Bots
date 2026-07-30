import os
import requests
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        pass

    def get_credentials(self):
        token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
        chat_id = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
        return token, chat_id

    def is_configured(self):
        token, chat_id = self.get_credentials()
        return bool(token and chat_id)

    def send_message(self, text):
        token, chat_id = self.get_credentials()
        if not token or not chat_id:
            logger.warning("Telegram Bot Token ou Chat ID não estão configurados nas Variáveis de Ambiente.")
            return False, "Credenciais do Telegram em falta."
            
        api_url = f"https://api.telegram.org/bot{token}/sendMessage"
            
        try:
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            response = requests.post(api_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return True, "Mensagem enviada com sucesso."
            else:
                logger.error(f"Erro ao enviar Telegram: {response.text}")
                return False, f"Erro na API do Telegram: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Erro de excepção no Telegram: {str(e)}")
            return False, str(e)

    def generate_daily_report(self, hub_status_data):
        """
        Recebe os dados agregados do Hub e gera um relatório bonito.
        """
        lines = []
        lines.append("📊 *Relatório Diário de Lucros*")
        lines.append("--------------------------------")
        
        total_profit = 0.0
        
        # Bot 01 (Trading)
        if 'bot1' in hub_status_data:
            bot1 = hub_status_data['bot1']
            if bot1.get('status') == 'online':
                pnl = float(bot1.get('data', {}).get('net_pnl', 0.0))
                total_profit += pnl
                lines.append(f"📈 *Bot 01 (QuantTrader):* `${pnl:.2f}`")
            else:
                lines.append("📈 *Bot 01 (QuantTrader):* 🔴 Offline")
                
        # Bot 03 (Arbitragem)
        if 'bot3' in hub_status_data:
            bot3 = hub_status_data['bot3']
            if bot3.get('status') == 'online':
                profit = float(bot3.get('data', {}).get('total_profit', 0.0))
                total_profit += profit
                lines.append(f"⚖️ *Bot 03 (Arbitragem):* `${profit:.2f}`")
            else:
                lines.append("⚖️ *Bot 03 (Arbitragem):* 🔴 Offline")
                
        # Bot 04 (YieldPro)
        if 'bot4' in hub_status_data:
            bot4 = hub_status_data['bot4']
            if bot4.get('status') == 'online':
                yield_earned = float(bot4.get('data', {}).get('total_yield_earned', 0.0))
                total_profit += yield_earned
                lines.append(f"🚜 *Bot 04 (YieldPro):* `${yield_earned:.4f}`")
            else:
                lines.append("🚜 *Bot 04 (YieldPro):* 🔴 Offline")
                
        lines.append("--------------------------------")
        if total_profit >= 0:
            lines.append(f"💰 *Lucro Total do Dia:* `+${total_profit:.2f}`")
        else:
            lines.append(f"🔴 *Prejuízo do Dia:* `-${abs(total_profit):.2f}`")
            
        return "\n".join(lines)
