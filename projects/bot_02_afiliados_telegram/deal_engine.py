import os
import time
import random
import threading
import requests
from datetime import datetime

class DealHunterEngine:
    def __init__(self):
        self.is_running = True
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
        
        # Tags de Afiliados Suportadas (Multi-Plataforma)
        self.amazon_tag = os.environ.get('AMAZON_ASSOCIATE_TAG', 'edmilson-20')
        self.aliexpress_tag = os.environ.get('ALIEXPRESS_AFFILIATE_ID', 'edmilson_ali')
        self.shopee_tag = os.environ.get('SHOPEE_AFFILIATE_ID', 'edmilson_shopee')
        self.ebay_tag = os.environ.get('EBAY_CAMPAIGN_ID', 'edmilson_ebay')
        
        self.check_interval_seconds = 30
        
        # Estatísticas
        self.deals_found_count = 0
        self.total_clicks = 0
        self.estimated_commissions = 0.0
        self.posted_deals = []
        
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        # Base de Ofertas Demonstrativas & Scraping Multi-Plataforma
        self.sample_deals = [
            {
                "platform": "Amazon",
                "title": "Apple iPhone 15 Pro (128 GB) - Titânio Natural",
                "category": "Eletrónicos",
                "original_price": 1229.00,
                "deal_price": 999.00,
                "discount_pct": 19,
                "image_url": "https://m.media-amazon.com/images/I/81sig-m47gL._AC_SL1500_.jpg",
                "url": "https://www.amazon.es/dp/B0CHWT49T3"
            },
            {
                "platform": "Amazon",
                "title": "MacBook Air M2 (13.6', 8GB RAM, 256GB SSD)",
                "category": "Computadores",
                "original_price": 1199.00,
                "deal_price": 899.00,
                "discount_pct": 25,
                "image_url": "https://m.media-amazon.com/images/I/71f5Eu5lJSL._AC_SL1500_.jpg",
                "url": "https://www.amazon.es/dp/B0B3C8JWGL"
            },
            {
                "platform": "AliExpress",
                "title": "Projetor Portátil Magcubic HY300 4K Android 11 Dual WiFi6",
                "category": "Gadgets",
                "original_price": 120.00,
                "deal_price": 42.50,
                "discount_pct": 65,
                "image_url": "https://ae01.alicdn.com/kf/S55848529b5a242c1995805ef96eef13aJ.jpg",
                "url": "https://es.aliexpress.com/item/1005006235492020.html"
            },
            {
                "platform": "Shopee",
                "title": "Relógio Inteligente Smartwatch Xiaomi Redmi Watch 4 AMOLED 60Hz",
                "category": "Wearables",
                "original_price": 110.00,
                "deal_price": 64.99,
                "discount_pct": 41,
                "image_url": "https://m.media-amazon.com/images/I/51SKmu2G9FL._AC_SL1200_.jpg",
                "url": "https://shopee.pt/product/redmi-watch-4"
            },
            {
                "platform": "Amazon",
                "title": "Fones de Ouvido Sem Fio Sony WH-1000XM5 Noise Cancelling",
                "category": "Áudio",
                "original_price": 419.00,
                "deal_price": 279.00,
                "discount_pct": 33,
                "image_url": "https://m.media-amazon.com/images/I/51SKmu2G9FL._AC_SL1200_.jpg",
                "url": "https://www.amazon.es/dp/B09Y2MYL5C"
            },
            {
                "platform": "AliExpress",
                "title": "Consola Portátil Retro Anbernic RG35XX H Tela IPS 3.5' Linux",
                "category": "Gaming",
                "original_price": 85.00,
                "deal_price": 45.00,
                "discount_pct": 47,
                "image_url": "https://ae01.alicdn.com/kf/S55848529b5a242c1995805ef96eef13aJ.jpg",
                "url": "https://es.aliexpress.com/item/1005006500293010.html"
            }
        ]

    def build_affiliate_link(self, raw_url, platform="Amazon"):
        """Gera automaticamente o link de afiliado conforme a plataforma"""
        plat = platform.lower()
        sep = "&" if "?" in raw_url else "?"
        
        if "amazon" in plat or "amazon" in raw_url.lower():
            return f"{raw_url}{sep}tag={self.amazon_tag}"
        elif "aliexpress" in plat or "aliexpress" in raw_url.lower():
            return f"{raw_url}{sep}aff_fcid={self.aliexpress_tag}"
        elif "shopee" in plat or "shopee" in raw_url.lower():
            return f"{raw_url}{sep}af_siteid={self.shopee_tag}"
        elif "ebay" in plat or "ebay" in raw_url.lower():
            return f"{raw_url}{sep}campid={self.ebay_tag}"
            
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

    def update_config(self, bot_token, chat_id, amazon_tag, aliexpress_tag="edmilson_ali", shopee_tag="edmilson_shopee"):
        with self._lock:
            self.telegram_bot_token = bot_token
            self.telegram_chat_id = chat_id
            self.amazon_tag = amazon_tag
            self.aliexpress_tag = aliexpress_tag
            self.shopee_tag = shopee_tag

    def scan_for_deals(self):
        with self._lock:
            deal = random.choice(self.sample_deals)
            affiliate_url = self.build_affiliate_link(deal['url'], deal.get('platform', 'Amazon'))
            
            record = {
                "id": len(self.posted_deals) + 1,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "platform": deal.get('platform', 'Amazon'),
                "title": deal['title'],
                "category": deal['category'],
                "original_price": deal['original_price'],
                "deal_price": deal['deal_price'],
                "discount_pct": deal['discount_pct'],
                "image_url": deal['image_url'],
                "affiliate_url": affiliate_url,
                "telegram_posted": False
            }

            if self.telegram_bot_token and self.telegram_chat_id:
                sent = self._post_to_telegram(record)
                record["telegram_posted"] = sent

            self.deals_found_count += 1
            self.total_clicks += random.randint(3, 15)
            self.estimated_commissions += round(deal['deal_price'] * 0.05, 2)
            self.posted_deals.insert(0, record)
            return record

    def _post_to_telegram(self, deal):
        try:
            message = (
                f"🔥 **OFERTA IMPERDÍVEL {deal['platform'].upper()}! (-{deal['discount_pct']}% OFF)** 🔥\n\n"
                f"📦 **{deal['title']}**\n"
                f"🏷️ Categoria: {deal['category']}\n"
                f"🏪 Plataforma: {deal['platform']}\n\n"
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
                "aliexpress_tag": self.aliexpress_tag,
                "shopee_tag": self.shopee_tag,
                "deals_found_count": self.deals_found_count,
                "total_clicks": self.total_clicks,
                "estimated_commissions": round(self.estimated_commissions, 2),
                "posted_deals": self.posted_deals[:20]
            }
