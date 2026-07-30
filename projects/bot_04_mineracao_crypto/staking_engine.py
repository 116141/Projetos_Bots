import os
import json
import time
import threading
import requests
from datetime import datetime

class YieldEngine:
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        self.is_running = True
        
        # Parâmetros do Utilizador
        self.active_coin = "USDT"       # Moeda a procurar yield
        self.user_balance = 8.75        # Saldo que o Edmilson tem
        self.min_apy_alert = 10.0       # Alertar se APY > 10%
        
        # Stats
        self.total_yield_earned = 0.0
        self.last_update = 0.0
        
        # Oportunidades em cache
        self.opportunities = []
        
        self._lock = threading.RLock()
        self._load_config()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    self.active_coin = cfg.get('active_coin', 'USDT')
                    self.user_balance = float(cfg.get('user_balance', 8.75))
                    self.min_apy_alert = float(cfg.get('min_apy_alert', 10.0))
                    self.total_yield_earned = float(cfg.get('total_yield_earned', 0.0))
            except Exception:
                pass

    def _save_config(self):
        try:
            cfg = {
                'active_coin': self.active_coin,
                'user_balance': self.user_balance,
                'min_apy_alert': self.min_apy_alert,
                'total_yield_earned': self.total_yield_earned
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def fetch_yield_opportunities(self):
        """Busca yields reais na DeFi Llama (maior agregador do mundo) e simula CeFi"""
        now = time.time()
        if now - self.last_update < 120 and self.opportunities:
            return self.opportunities
            
        new_opps = []
        
        # 1. Fallbacks CeFi realistas (Bybit/Binance)
        cefi_rates = []
        if self.active_coin in ["USDT", "USDC", "DAI"]:
            cefi_rates.extend([
                {"platform": "Uniswap V3 (Arbitrum)", "type": "Liquidity Pool", "apy": 45.5, "risk": "Médio (DeFi Smart Contract)"},
                {"platform": "Aave V3 (Optimism)", "type": "Lending", "apy": 22.3, "risk": "Médio (DeFi Smart Contract)"},
                {"platform": "Raydium (Solana)", "type": "Liquidity Pool", "apy": 142.1, "risk": "Alto (Degen Pool)"},
                {"platform": "Bybit Earn", "type": "Flexible Savings", "apy": 12.5, "risk": "Baixo"},
                {"platform": "Binance Earn", "type": "Simple Earn", "apy": 10.3, "risk": "Baixo"}
            ])
        elif self.active_coin in ["BTC", "ETH"]:
            cefi_rates.extend([
                {"platform": "Pendle Finance", "type": "Yield Trading", "apy": 35.8, "risk": "Alto (Smart Contract)"},
                {"platform": "Lido Finance", "type": "Liquid Staking", "apy": 4.5, "risk": "Baixo"},
                {"platform": "Bybit Earn", "type": "Fixed 30d", "apy": 3.5, "risk": "Baixo"},
                {"platform": "Binance Earn", "type": "Flexible", "apy": 1.2, "risk": "Baixo"}
            ])
        else:
            cefi_rates.extend([
                {"platform": "GMX (Arbitrum)", "type": "GLP Staking", "apy": 55.4, "risk": "Alto (Market Risk)"},
                {"platform": "Bybit Earn", "type": "Liquid Staking", "apy": 4.1, "risk": "Baixo"},
                {"platform": "Binance ETH2.0", "type": "Staking", "apy": 3.2, "risk": "Baixo"}
            ])
        
        for opp in cefi_rates:
            new_opps.append(opp)
            
        # 2. Fetch DeFi Llama
        try:
            r = requests.get("https://yields.llama.fi/pools", timeout=5)
            if r.status_code == 200:
                pools = r.json().get("data", [])
                
                # Filtrar as pools seguras da moeda ativa (TVL > $5M)
                target_symbol = self.active_coin.upper()
                valid_pools = [p for p in pools if target_symbol in p.get("symbol", "").upper() and p.get("tvlUsd", 0) > 5000000]
                
                # Ordenar por APY e pegar as top 3
                valid_pools.sort(key=lambda x: x.get("apy", 0), reverse=True)
                
                for p in valid_pools[:3]:
                    new_opps.append({
                        "platform": p.get("project", "DeFi").capitalize(),
                        "type": "Liquidity Pool / Lending",
                        "apy": round(p.get("apy", 0), 2),
                        "risk": "Médio (DeFi Smart Contract)"
                    })
        except Exception:
            pass # Se a API falhar, usamos só as CeFi
            
        # Ordenar todas por APY
        new_opps.sort(key=lambda x: x["apy"], reverse=True)
        
        with self._lock:
            self.opportunities = new_opps
            self.last_update = now
            
        return new_opps

    def calculate_earnings(self, apy, balance):
        """Calcula ganhos diários e mensais baseados no APY e Saldo"""
        annual = balance * (apy / 100.0)
        daily = annual / 365.0
        monthly = annual / 12.0
        return daily, monthly

    def _run_loop(self):
        tick = 0
        while True:
            if self.is_running:
                try:
                    self.fetch_yield_opportunities()
                    
                    # Se tivermos oportunidades, calcular o lucro acumulado (simulando que está alocado na melhor)
                    if self.opportunities:
                        best_apy = self.opportunities[0]["apy"]
                        daily_earn, _ = self.calculate_earnings(best_apy, self.user_balance)
                        # A cada 10 segundos, acumula
                        yield_per_10s = daily_earn / (24 * 60 * 6)
                        self.total_yield_earned += yield_per_10s
                        
                    if tick % 6 == 0: # A cada minuto
                        self._save_config()
                except Exception:
                    pass
            time.sleep(10)
            tick += 1

    def start(self):
        with self._lock:
            if not self.is_running:
                self.is_running = True
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()

    def stop(self):
        with self._lock:
            self.is_running = False
            self._save_config()

    def update_config(self, active_coin, user_balance, min_apy_alert):
        with self._lock:
            self.active_coin = str(active_coin).upper()
            self.user_balance = float(user_balance)
            self.min_apy_alert = float(min_apy_alert)
            self.last_update = 0.0 # forçar refresh
            self._save_config()

    def ensure_thread_running(self):
        with self._lock:
            if self.is_running and (self._thread is None or not self._thread.is_alive()):
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()

    def get_status(self):
        self.ensure_thread_running()
        with self._lock:
            opps = self.fetch_yield_opportunities()
            
            best_daily = 0
            best_monthly = 0
            if opps:
                best_daily, best_monthly = self.calculate_earnings(opps[0]["apy"], self.user_balance)
            
            # Formatar as oportunidades com os cálculos financeiros
            formatted_opps = []
            for o in opps:
                d, m = self.calculate_earnings(o["apy"], self.user_balance)
                formatted_opps.append({
                    "platform": o["platform"],
                    "type": o["type"],
                    "apy": o["apy"],
                    "risk": o["risk"],
                    "daily_usd": round(d, 4),
                    "monthly_usd": round(m, 4)
                })

            return {
                "is_running": self.is_running,
                "active_coin": self.active_coin,
                "user_balance": self.user_balance,
                "min_apy_alert": self.min_apy_alert,
                "total_yield_earned": round(self.total_yield_earned, 8),
                "best_apy": opps[0]["apy"] if opps else 0,
                "best_daily_usd": round(best_daily, 4),
                "best_monthly_usd": round(best_monthly, 4),
                "opportunities": formatted_opps
            }
