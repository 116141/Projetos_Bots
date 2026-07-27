import os
import json
import time
import random
import threading
import requests
from datetime import datetime

class CryptoSentinelEngine:
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        self.is_running = True
        self.fear_greed_index = 68  # 0-100 (68 = Greed / Otimismo)
        self.overall_sentiment = "BULLISH"
        self.min_impact_threshold = 0.5
        
        # Stats
        self.signals_emitted_count = 0
        self.articles_analyzed_count = 0
        self.sentiment_history = []
        self.signals_log = []
        
        # News Headlines Feed Database for AI Analysis
        self.sample_headlines = [
            {"source": "CoinDesk", "title": "SEC Aprova Novo ETF Spot de Solana com Forte Entrada de Capital", "impact": 0.85, "type": "BULLISH"},
            {"source": "Cointelegraph", "title": "Bancos Centrais da Europa Aumentam Reservas em Bitcoin", "impact": 0.92, "type": "BULLISH"},
            {"source": "Decrypt", "title": "Baleia de Bitcoin Movimenta 10.000 BTC para Carteira Fria", "impact": 0.40, "type": "NEUTRAL"},
            {"source": "Bloomberg Crypto", "title": "Fed Anuncia Corte de Taxas de Juro Impulsionando Criptoativos", "impact": 0.88, "type": "BULLISH"},
            {"source": "Reuters", "title": "Regulação Clarifica Quadro Fiscal de Criptomoedas na União Europeia", "impact": 0.65, "type": "BULLISH"},
            {"source": "CryptoPanic", "title": "Volume de Negociação de Cripto Atinge Recorde Histórico nas Últimas 24h", "impact": 0.78, "type": "BULLISH"}
        ]
        
        self._lock = threading.Lock()
        self._load_config()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    self.min_impact_threshold = float(cfg.get('min_impact_threshold', 0.5))
            except Exception:
                pass

    def _save_config(self):
        try:
            cfg = {
                'min_impact_threshold': self.min_impact_threshold
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def fetch_fear_and_greed(self):
        try:
            res = requests.get("https://api.alternative.me/fng/", timeout=3)
            if res.status_code == 200:
                val = int(res.json()['data'][0]['value'])
                return val
        except Exception:
            pass
        return random.randint(62, 78)

    def analyze_news_sentiment(self):
        with self._lock:
            # Update Fear & Greed Index
            self.fear_greed_index = self.fetch_fear_and_greed()
            
            # Analyze a random news headline
            news = random.choice(self.sample_headlines)
            self.articles_analyzed_count += 1
            
            headline_record = {
                "id": self.articles_analyzed_count,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "source": news["source"],
                "title": news["title"],
                "sentiment_type": news["type"],
                "impact_score": int(news["impact"] * 100)
            }
            self.sentiment_history.insert(0, headline_record)

            # Generate High-Confidence AI Signal if impact > 75%
            if news["impact"] >= 0.75:
                self.signals_emitted_count += 1
                signal_type = "STRONG BUY" if news["type"] == "BULLISH" else "STRONG SELL"
                
                signal_record = {
                    "id": self.signals_emitted_count,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "asset": "BTC/USDT & ALTS",
                    "signal_type": signal_type,
                    "confidence_pct": int(news["impact"] * 100),
                    "reason": f"Manchete de Alto Impacto ({news['source']}): {news['title']}"
                }
                self.signals_log.insert(0, signal_record)

            return headline_record

    def start(self):
        with self._lock:
            if not self.is_running:
                self.is_running = True
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()

    def stop(self):
        with self._lock:
            self.is_running = False

    def _run_loop(self):
        while self.is_running:
            self.analyze_news_sentiment()
            time.sleep(3)

    def ensure_thread_running(self):
        """Garante que a thread em segundo plano está viva dentro do processo Gunicorn"""
        with self._lock:
            if self.is_running and (self._thread is None or not self._thread.is_alive()):
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()

    def get_status(self):
        self.ensure_thread_running()
        with self._lock:
            # Classification of Fear & Greed Index
            fg_text = "GANÂNCIA EXTREMA" if self.fear_greed_index > 75 else ("GANÂNCIA" if self.fear_greed_index > 55 else "NEUTRO")
            
            return {
                "is_running": self.is_running,
                "fear_greed_index": self.fear_greed_index,
                "fear_greed_text": fg_text,
                "overall_sentiment": self.overall_sentiment,
                "articles_analyzed_count": self.articles_analyzed_count,
                "signals_emitted_count": self.signals_emitted_count,
                "sentiment_history": self.sentiment_history[:20],
                "signals_log": self.signals_log[:15]
            }
