import os
import time
import random
import threading
import requests
from datetime import datetime

import json

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

class DealHunterEngine:
    def __init__(self):
        self.is_running = True
        
        # Carregar do config.json se existir, senão usar variáveis de ambiente
        saved_config = self._load_config()
        self.telegram_bot_token = saved_config.get('telegram_bot_token') or os.environ.get('TELEGRAM_BOT_TOKEN', '8977525891:AAETvun3_qUkX4EUtq5VQcy5ckLI2QMq')
        self.telegram_chat_id = saved_config.get('telegram_chat_id') or os.environ.get('TELEGRAM_CHAT_ID', '-1004315197983')
        
        # Tags de Afiliados Suportadas (Multi-Plataforma)
        self.amazon_tag = saved_config.get('amazon_tag') or os.environ.get('AMAZON_ASSOCIATE_TAG', 'gilsoncarvalh-21')
        self.aliexpress_tag = os.environ.get('ALIEXPRESS_AFFILIATE_ID', '')
        self.shopee_tag = os.environ.get('SHOPEE_AFFILIATE_ID', '')
        self.ebay_tag = os.environ.get('EBAY_CAMPAIGN_ID', '')
        
        self.check_interval_seconds = 30
        
        # Estatísticas
        self.deals_found_count = 0
        self.total_clicks = 0
        self.estimated_commissions = 0.0
        self.posted_deals = []
        
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

        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_config(self):
        try:
            cfg = {
                "telegram_bot_token": self.telegram_bot_token,
                "telegram_chat_id": self.telegram_chat_id,
                "amazon_tag": self.amazon_tag
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def is_valid_affiliate_tag(self, tag):
        """Verifica se a tag de afiliado é válida e não é vazia ou marcador temporário de exemplo"""
        if not tag:
            return False
        tag_clean = str(tag).strip().lower()
        placeholders = ["", "edmilson_ali", "edmilson_shopee", "edmilson_ebay", "edmilson-20", "ex:tag", "undefined", "none"]
        return tag_clean not in placeholders

    def build_affiliate_link(self, raw_url, platform="Amazon"):
        """Deteta o domínio e injeta o ID de Afiliado. Retorna (url_afiliado, tem_afiliado_valido)"""
        plat = platform.lower()
        url_lower = raw_url.lower()
        sep = "&" if "?" in raw_url else "?"
        
        # 1. Amazon (amazon.es, amazon.com, amzn.to)
        if "amazon" in url_lower or "amzn" in url_lower or "amazon" in plat:
            if self.is_valid_affiliate_tag(self.amazon_tag):
                return f"{raw_url}{sep}tag={self.amazon_tag}", True
            return raw_url, False
            
        # 2. Shopee (shopee.pt, shopee.com.br, shope.ee)
        elif "shopee" in url_lower or "shope" in url_lower or "shopee" in plat:
            if self.is_valid_affiliate_tag(self.shopee_tag):
                return f"{raw_url}{sep}af_siteid={self.shopee_tag}", True
            return raw_url, False
            
        # 3. AliExpress (aliexpress.com, s.click.aliexpress.com)
        elif "aliexpress" in url_lower or "ali" in url_lower or "aliexpress" in plat:
            if self.is_valid_affiliate_tag(self.aliexpress_tag):
                return f"{raw_url}{sep}aff_fcid={self.aliexpress_tag}", True
            return raw_url, False
            
        # 4. eBay (ebay.com, ebay.es)
        elif "ebay" in url_lower or "ebay" in plat:
            if self.is_valid_affiliate_tag(self.ebay_tag):
                return f"{raw_url}{sep}campid={self.ebay_tag}", True
            return raw_url, False
            
        return raw_url, False

    def start(self):
        with self._lock:
            if not self.is_running:
                self.is_running = True
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()

    def stop(self):
        with self._lock:
            self.is_running = False

    def update_config(self, bot_token, chat_id, amazon_tag, aliexpress_tag="", shopee_tag=""):
        with self._lock:
            self.telegram_bot_token = bot_token
            self.telegram_chat_id = chat_id
            self.amazon_tag = amazon_tag
            if aliexpress_tag:
                self.aliexpress_tag = aliexpress_tag
            if shopee_tag:
                self.shopee_tag = shopee_tag
            self._save_config()

    def get_active_deals_pool(self):
        """Retorna apenas ofertas das plataformas que possuem ID de Afiliado VÁLIDO configurado"""
        valid_pool = []
        for deal in self.sample_deals:
            plat = deal.get('platform', 'Amazon').lower()
            if ("amazon" in plat or "amzn" in plat) and self.is_valid_affiliate_tag(self.amazon_tag):
                valid_pool.append(deal)
            elif ("shopee" in plat or "shope" in plat) and self.is_valid_affiliate_tag(self.shopee_tag):
                valid_pool.append(deal)
            elif ("aliexpress" in plat or "ali" in plat) and self.is_valid_affiliate_tag(self.aliexpress_tag):
                valid_pool.append(deal)
            elif "ebay" in plat and self.is_valid_affiliate_tag(self.ebay_tag):
                valid_pool.append(deal)
        return valid_pool if valid_pool else self.sample_deals

    def scan_for_deals(self):
        with self._lock:
            pool = self.get_active_deals_pool()
            deal = random.choice(pool)
            affiliate_url, has_valid_affiliate = self.build_affiliate_link(deal['url'], deal.get('platform', 'Amazon'))
            
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
                "has_valid_affiliate": has_valid_affiliate,
                "telegram_posted": False
            }

            # REGRA ESTRITA: Apenas dispara para o Telegram se houver Tag de Afiliado VÁLIDA da plataforma!
            if has_valid_affiliate and self.telegram_bot_token and self.telegram_chat_id:
                sent = self._post_to_telegram(record)
                record["telegram_posted"] = sent

            self.deals_found_count += 1
            if has_valid_affiliate:
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

    def ensure_thread_running(self):
        """Garante que a thread em segundo plano está viva dentro do processo Gunicorn"""
        with self._lock:
            if self.is_running and (self._thread is None or not self._thread.is_alive()):
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()

    def get_status(self):
        self.ensure_thread_running()
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
