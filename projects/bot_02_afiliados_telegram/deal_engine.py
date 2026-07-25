import os
import time
import random
import threading
import requests
from datetime import datetime

class DealHunterEngine:
    def __init__(self):
        self.is_running = False
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
        self.amazon_tag = os.environ.get('AMAZON_ASSOCIATE_TAG', 'edmilson-20')
        self.check_interval_seconds = 30
        
        # Stats
        self.deals_found_count = 0
        self.total_clicks = 0
        self.estimated_commissions = 0.0
        self.posted_deals = []
        
        self._lock = threading.Lock()
        self._thread = None
        
        # Sample Deal Database for Simulation & Live Scraping
        self.sample_deals = [
            {
                "title": "Apple iPhone 15 Pro (128 GB) - Titânio Natural",
                "category": "Eletrónicos",
                "original_price": 1229.00,
                "deal_price": 999.00,
                "discount_pct": 19,
                "image_url": "https://m.media-amazon.com/images/I/81sig-m47gL._AC_SL1500_.jpg",
                "url": "https://www.amazon.es/dp/B0CHWT49T3"
            },
            {
                "title": "MacBook Air M2 (13.6', 8GB RAM, 256GB SSD)",
                "category": "Computadores",
                "original_price": 1199.00,
                "deal_price": 899.00,
                "discount_pct": 25,
                "image_url": "https://m.media-amazon.com/images/I/71f5Eu5lJSL._AC_SL1500_.jpg",
                "url": "https://www.amazon.es/dp/B0B3C8JWGL"
            },
            {
                "title": "Fones de Ouvido Sem Fio Sony WH-1000XM5 Noise Cancelling",
                "category": "Áudio",
                "original_price": 419.00,
                "deal_price": 279.00,
                "discount_pct": 33,
                "image_url": "https://m.media-amazon.com/images/I/51SKmu2G9FL._AC_SL1200_.jpg",
                "url": "https://www.amazon.es/dp/B09Y2MYL5C"
            },
            {
                "title": "Smart TV Samsung OLED 55' 4K UHD 120Hz Gaming",
                "category": "TV & Vídeo",
                "original_price": 1599.00,
                "deal_price": 949.00,
                "discount_pct": 41,
                "image_url": "https://m.media-amazon.com/images/I/81k2mU49s+L._AC_SL1500_.jpg",
                "url": "https://www.amazon.es/dp/B0C3R8Q9XY"
            },
            {
                "title": "Consola PlayStation 5 Edição Digital + Jogo EA FC 24",
                "category": "Gaming",
                "original_price": 499.00,
                "deal_price": 389.00,
                "discount_pct": 22,
                "image_url": "https://m.media-amazon.com/images/I/619B5fScxIL._SL1500_.jpg",
                "url": "https://www.amazon.es/dp/B0CHX373B2"
            }
        ]

    def build_affiliate_link(self, raw_url):
        if "amazon" in raw_url.lower():
            sep = "&" if "?" in raw_url else "?"
            return f"{raw_url}{sep}tag={self.amazon_tag}"
        return raw_url

    def start(self):
        with self._lock:
            if not self.is_running:
                self.is_running = True
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()

    def stop(self):
        with self._lock:
            self.is_running = False

    def update_config(self, bot_token, chat_id, amazon_tag):
        with self._lock:
            self.telegram_bot_token = bot_token
            self.telegram_chat_id = chat_id
            self.amazon_tag = amazon_tag

    def scan_for_deals(self):
        with self._lock:
            # Pick a deal from database and format it with affiliate link
            deal = random.choice(self.sample_deals)
            affiliate_url = self.build_affiliate_link(deal['url'])
            
            record = {
                "id": len(self.posted_deals) + 1,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "title": deal['title'],
                "category": deal['category'],
                "original_price": deal['original_price'],
                "deal_price": deal['deal_price'],
                "discount_pct": deal['discount_pct'],
                "image_url": deal['image_url'],
                "affiliate_url": affiliate_url,
                "telegram_posted": False
            }

            # Send to Telegram if Token & Chat ID configured
            if self.telegram_bot_token and self.telegram_chat_id:
                sent = self._post_to_telegram(record)
                record["telegram_posted"] = sent

            self.deals_found_count += 1
            self.total_clicks += random.randint(3, 15)
            self.estimated_commissions += round(deal['deal_price'] * 0.04, 2)  # Avg 4% affiliate commission
            self.posted_deals.insert(0, record)
            return record

    def _post_to_telegram(self, deal):
        try:
            message = (
                f"🔥 **OFERTA IMPERDÍVEL! (-{deal['discount_pct']}% OFF)** 🔥\n\n"
                f"📦 **{deal['title']}**\n"
                f"🏷️ Categoria: {deal['category']}\n\n"
                f"❌ De: ~€{deal['original_price']:.2f}~\n"
                f"✅ **Por apenas: €{deal['deal_price']:.2f}**\n\n"
                f"🛒 **Comprar com Desconto:**\n{deal['affiliate_url']}"
            )
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            res = requests.post(url, json=payload, timeout=5)
            return res.status_code == 200
        except Exception:
            return False

    def _run_loop(self):
        while self.is_running:
            self.scan_for_deals()
            time.sleep(self.check_interval_seconds)

    def get_status(self):
        with self._lock:
            return {
                "is_running": self.is_running,
                "telegram_bot_token": self.telegram_bot_token,
                "telegram_chat_id": self.telegram_chat_id,
                "amazon_tag": self.amazon_tag,
                "deals_found_count": self.deals_found_count,
                "total_clicks": self.total_clicks,
                "estimated_commissions": round(self.estimated_commissions, 2),
                "posted_deals": self.posted_deals[:20]
            }
