import os
import time
import random
import threading
import requests
from datetime import datetime

class AutoMineEngine:
    def __init__(self):
        self.is_running = True
        
        # NiceHash API Credentials
        self.nicehash_org_id = os.environ.get('NICEHASH_ORG_ID', '')
        self.nicehash_api_key = os.environ.get('NICEHASH_API_KEY', '')
        self.nicehash_api_secret = os.environ.get('NICEHASH_API_SECRET', '')
        
        # Hardware Rig Specs
        self.rig_hashrate_mhs = float(os.environ.get('RIG_HASHRATE_MHS', 250.0))  # 250 MH/s Rig Hashrate
        self.power_consumption_watts = float(os.environ.get('POWER_WATTS', 600.0))  # 600W Power Consumption
        self.electricity_cost_kwh = float(os.environ.get('ELEC_COST_KWH', 0.12))  # $0.12 per kWh
        
        # Current active coin
        self.active_coin = "BTC"
        self.auto_switch_enabled = True
        
        # Stats
        self.total_mined_usd = 0.0
        self.total_electricity_usd = 0.0
        self.net_profit_usd = 0.0
        self.switch_history = []
        
        # Coin Database & Live Profitability Specs
        self.coins_db = {
            "KAS": {"name": "Kaspa (KHeavyHash)", "algo": "KHeavyHash", "base_reward_day": 14.50},
            "ETC": {"name": "Ethereum Classic", "algo": "ETCHash", "base_reward_day": 11.20},
            "RVN": {"name": "Ravencoin", "algo": "KawPoW", "base_reward_day": 9.80},
            "ZEPH": {"name": "Zephyr Protocol", "algo": "RandomX", "base_reward_day": 12.80},
            "BTC": {"name": "Bitcoin (SHA-256 Cloud)", "algo": "SHA-256", "base_reward_day": 16.10}
        }
        
        self._lock = threading.RLock()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def calculate_profitability(self):
        with self._lock:
            # 24h Electricity Cost: (Watts * 24h / 1000) * $/kWh
            daily_kwh = (self.power_consumption_watts * 24.0) / 1000.0
            daily_elec_cost = daily_kwh * self.electricity_cost_kwh

            coin_rankings = []
            for ticker, info in self.coins_db.items():
                # Add micro market fluctuations (+/- 5%)
                fluctuation = random.uniform(0.95, 1.05)
                gross_daily = info["base_reward_day"] * (self.rig_hashrate_mhs / 250.0) * fluctuation
                net_daily = gross_daily - daily_elec_cost
                
                coin_rankings.append({
                    "ticker": ticker,
                    "name": info["name"],
                    "algo": info["algo"],
                    "gross_daily": round(gross_daily, 2),
                    "elec_cost_daily": round(daily_elec_cost, 2),
                    "net_daily": round(net_daily, 2),
                    "is_active": (ticker == self.active_coin)
                })

            # Sort by Net Daily Profit (Highest first)
            coin_rankings.sort(key=lambda x: x["net_daily"], reverse=True)
            
            # Auto-switch to highest profitability coin if enabled
            top_coin = coin_rankings[0]["ticker"]
            if self.auto_switch_enabled and top_coin != self.active_coin and self.is_running:
                old_coin = self.active_coin
                self.active_coin = top_coin
                
                self.switch_history.insert(0, {
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "from_coin": old_coin,
                    "to_coin": top_coin,
                    "reason": f"Rentabilidade superior em +${(coin_rankings[0]['net_daily'] - coin_rankings[1]['net_daily']):.2f}/dia"
                })

            # Update accumulated yields
            if self.is_running:
                active_info = next(c for c in coin_rankings if c["ticker"] == self.active_coin)
                yield_per_tick = active_info["gross_daily"] / 43200.0  # Normalized per 2s tick
                elec_per_tick = daily_elec_cost / 43200.0
                
                self.total_mined_usd += yield_per_tick
                self.total_electricity_usd += elec_per_tick
                self.net_profit_usd = self.total_mined_usd - self.total_electricity_usd

            return coin_rankings

    def start(self):
        with self._lock:
            if not self.is_running:
                self.is_running = True
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()

    def stop(self):
        with self._lock:
            self.is_running = False

    def update_config(self, hashrate, watts, elec_cost, auto_switch):
        with self._lock:
            self.rig_hashrate_mhs = float(hashrate)
            self.power_consumption_watts = float(watts)
            self.electricity_cost_kwh = float(elec_cost)
            self.auto_switch_enabled = bool(auto_switch)

    def _run_loop(self):
        while self.is_running:
            self.calculate_profitability()
            time.sleep(2)

    def ensure_thread_running(self):
        """Garante que a thread em segundo plano está viva dentro do processo Gunicorn"""
        with self._lock:
            if self.is_running and (self._thread is None or not self._thread.is_alive()):
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()

    def get_status(self):
        self.ensure_thread_running()
        with self._lock:
            coin_rankings = self.calculate_profitability()
            active_info = next((c for c in coin_rankings if c["ticker"] == self.active_coin), coin_rankings[0])
            
            return {
                "is_running": self.is_running,
                "rig_hashrate_mhs": self.rig_hashrate_mhs,
                "power_consumption_watts": self.power_consumption_watts,
                "electricity_cost_kwh": self.electricity_cost_kwh,
                "auto_switch_enabled": self.auto_switch_enabled,
                "active_coin": self.active_coin,
                "total_mined_usd": round(self.total_mined_usd, 4),
                "total_electricity_usd": round(self.total_electricity_usd, 4),
                "net_profit_usd": round(self.net_profit_usd, 4),
                "active_net_daily": active_info["net_daily"],
                "active_monthly_est": round(active_info["net_daily"] * 30.0, 2),
                "coin_rankings": coin_rankings,
                "switch_history": self.switch_history[:15]
            }
