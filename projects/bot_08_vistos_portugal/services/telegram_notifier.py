import asyncio
import logging
from typing import Optional
import requests
from services.notifier import INotifier

logger = logging.getLogger(__name__)


class TelegramNotifier(INotifier):
    """Notificador que envia mensagens e PDFs gerados pelo bot para o Telegram."""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        if not bot_token or not chat_id:
            logger.warning("TelegramNotifier configurado sem token ou chat_id. Notificações desativadas.")

    async def send(self, title: str, message: str, attachment_path: Optional[str] = None):
        """Envia mensagem (e anexo, se fornecido) para o Telegram."""
        if not self.bot_token or not self.chat_id:
            logger.warning("[Telegram desativado] %s - %s", title, message)
            return

        text = f"🔔 *{title}*\n\n{message}"

        try:
            # Enviar mensagem de texto
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown",
            }
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code != 200:
                logger.error("Falha ao enviar mensagem Telegram: %s - %s", resp.status_code, resp.text)
                return

            # Enviar anexo (PDF) se fornecido
            if attachment_path:
                await asyncio.to_thread(self._send_attachment, attachment_path)

        except Exception as e:
            logger.error("Erro ao enviar notificação Telegram: %s", e)

    def _send_attachment(self, attachment_path: str):
        """Envia um documento (PDF) para o Telegram."""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"
            with open(attachment_path, "rb") as f:
                files = {"document": (attachment_path.split("/")[-1], f, "application/pdf")}
                data = {"chat_id": self.chat_id, "caption": "📄 Comprovativo de agendamento"}
                resp = requests.post(url, data=data, files=files, timeout=60)
                if resp.status_code != 200:
                    logger.error("Falha ao enviar PDF: %s - %s", resp.status_code, resp.text)
        except Exception as e:
            logger.error("Erro ao enviar anexo Telegram: %s", e)
