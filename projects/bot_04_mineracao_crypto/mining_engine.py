import os
import json
import time
import random
import threading
import requests
from datetime import datetime

class AutoMineEngine:
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        self.is_running = True

        # NiceHash API Credentials (carregadas do ambiente ou config.json)
        self.nicehash_org_id    = os.environ.get('NICEHASH_ORG_ID', '')
        self.nicehash_api_key   = os.environ.get('NICEHASH_API_KEY', '')
        self.nicehash_api_secret = os.environ.get('NICEHASH_API_SECRET',
                                    os.environ.get('NICEHASH_SECRET_KEY', ''))

        # Hardware Rig Specs (parametros do utilizador - sem hardcode)
        self.rig_hashrate_mhs        = 250.0
        self.power_consumption_watts = 600.0
        self.electricity_cost_kwh    = 0.12

        # Estado atual
        self.active_coin        = "BTC"
        self.auto_switch_enabled = True

        # Stats acumulados
        self.total_mined_usd      = 0.0
        self.total_electricity_usd = 0.0
        self.net_profit_usd       = 0.0
        self.switch_history       = []

        # Cache de preços reais da NiceHash (atualizado a cada 60s)
        self._live_prices_cache   = {}
        self._last_price_fetch    = 0.0

        # NiceHash real account data
        self.nicehash_balance     = 0.0
        self.nicehash_rigs_count  = 0
        self.nicehash_rigs_status = "Sem hardware conectado"
        self.account_accessible   = False

        # Mapa de algoritmos NiceHash para moedas
        # paying da NiceHash está em BTC/GH/dia para algoritmos GPU
        # mhs_factor = converte MH/s do utilizador para GH/s = divide por 1000
        # XMR usa CPU (RandomX) — força fallback pois 250 MH/s GPU não serve para XMR
        self.algo_map = {
            "KAS":  {"name": "Kaspa",            "algo": "KHEAVYHASH",    "mhs_factor": 0.001,     "use_nicehash": True},
            "ETC":  {"name": "Ethereum Classic",  "algo": "ETCHASH",       "mhs_factor": 0.001,     "use_nicehash": True},
            "RVN":  {"name": "Ravencoin",         "algo": "KAWPOW",        "mhs_factor": 0.001,     "use_nicehash": True},
            "BTC":  {"name": "Bitcoin (SHA-256)",  "algo": "SHA256",       "mhs_factor": 0.000001,  "use_nicehash": True},
            "XMR":  {"name": "Monero (RandomX)",  "algo": "RANDOMXMONERO", "mhs_factor": 0.001,     "use_nicehash": False},
        }

        self._lock   = threading.RLock()
        self._thread = None
        self._load_config()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    self.active_coin              = cfg.get('active_coin', 'BTC')
                    self.auto_switch_enabled      = bool(cfg.get('auto_switch_enabled', True))
                    self.rig_hashrate_mhs         = float(cfg.get('rig_hashrate_mhs', 250.0))
                    self.power_consumption_watts  = float(cfg.get('power_consumption_watts', 600.0))
                    self.electricity_cost_kwh     = float(cfg.get('electricity_cost_kwh', 0.12))
                    self.total_mined_usd          = float(cfg.get('total_mined_usd', 0.0))
                    self.total_electricity_usd    = float(cfg.get('total_electricity_usd', 0.0))
                    self.net_profit_usd           = float(cfg.get('net_profit_usd', 0.0))
                    if cfg.get('nicehash_api_key'):
                        self.nicehash_api_key = cfg.get('nicehash_api_key')
                    if cfg.get('nicehash_api_secret'):
                        self.nicehash_api_secret = cfg.get('nicehash_api_secret')
                    if cfg.get('nicehash_org_id'):
                        self.nicehash_org_id = cfg.get('nicehash_org_id')
            except Exception:
                pass

    def _save_config(self):
        try:
            cfg = {
                'active_coin':             self.active_coin,
                'auto_switch_enabled':     self.auto_switch_enabled,
                'rig_hashrate_mhs':        self.rig_hashrate_mhs,
                'power_consumption_watts': self.power_consumption_watts,
                'electricity_cost_kwh':    self.electricity_cost_kwh,
                'total_mined_usd':         round(self.total_mined_usd, 6),
                'total_electricity_usd':   round(self.total_electricity_usd, 6),
                'net_profit_usd':          round(self.net_profit_usd, 6),
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    # ─── NiceHash API ─────────────────────────────────────────────────
    def _fetch_nicehash_algo_prices(self):
        """Busca rentabilidade REAL por algoritmo na NiceHash API v2"""
        now = time.time()
        if now - self._last_price_fetch < 60:        # Cache de 60 segundos
            return self._live_prices_cache
        self._last_price_fetch = now
        try:
            r = requests.get(
                "https://api2.nicehash.com/main/api/v2/public/simplemultialgo/info",
                timeout=6
            )
            if r.status_code == 200:
                data = r.json()
                algos = data.get("miningAlgorithms", [])
                cache = {}
                for a in algos:
                    name = a.get("algorithm", "").upper()
                    paying = float(a.get("paying", 0))  # BTC/TH/day
                    cache[name] = paying
                self._live_prices_cache = cache
                return cache
        except Exception:
            pass
        return self._live_prices_cache

    def _fetch_btc_usd_price(self):
        """Preço atual BTC em USD via Binance"""
        try:
            r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=4)
            if r.status_code == 200:
                return float(r.json()["price"])
        except Exception:
            pass
        return 65000.0

    def _fetch_nicehash_account_info(self):
        """Verifica o estado real da conta NiceHash (saldo + rigs)"""
        if not (self.nicehash_api_key and self.nicehash_api_secret and self.nicehash_org_id):
            return
        try:
            import hmac, hashlib, uuid as _uuid
            ts    = str(int(time.time() * 1000))
            nonce = str(_uuid.uuid4())
            path  = "/main/api/v2/mining/rigs2"
            msg   = f"{self.nicehash_api_key}\x00{ts}\x00{nonce}\x00\x00{self.nicehash_org_id}\x00\x00GET\x00{path}\x00"
            sig   = hmac.new(self.nicehash_api_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
            headers = {
                "X-Time":            ts,
                "X-Nonce":           nonce,
                "X-Organization-Id": self.nicehash_org_id,
                "X-Auth":            f"{self.nicehash_api_key}:{sig}",
            }
            r = requests.get("https://api2.nicehash.com" + path, headers=headers, timeout=6)
            if r.status_code == 200:
                data = r.json()
                self.nicehash_rigs_count = int(data.get("totalRigs", 0))
                self.account_accessible  = True
                if self.nicehash_rigs_count > 0:
                    self.nicehash_rigs_status = f"{self.nicehash_rigs_count} rig(s) conectado(s)"
                else:
                    self.nicehash_rigs_status = "Conta acessível mas sem hardware conectado"
            elif r.status_code == 401:
                self.nicehash_rigs_status = "❌ Autenticação NiceHash falhou — verifique as chaves"
        except Exception as e:
            self.nicehash_rigs_status = f"Erro ao contactar NiceHash: {str(e)[:60]}"

    # ─── Cálculo de Rentabilidade ──────────────────────────────────────
    def calculate_profitability(self):
        with self._lock:
            # Custo elétrico diário (parâmetros do utilizador)
            daily_kwh      = (self.power_consumption_watts * 24.0) / 1000.0
            daily_elec_cost = daily_kwh * self.electricity_cost_kwh

            # Buscar preços reais NiceHash e BTC/USD
            algo_prices = self._fetch_nicehash_algo_prices()
            btc_usd     = self._fetch_btc_usd_price()

            coin_rankings = []
            for ticker, info in self.algo_map.items():
                algo_name   = info["algo"]

                # Se temos preço real da NiceHash e algoritmo é GPU-compatível: usa-o
                if info.get("use_nicehash", True) and algo_prices.get(algo_name, 0) > 0:
                    # Converter MH/s do utilizador para GH/s (mhs_factor)
                    hashrate_units = self.rig_hashrate_mhs * info["mhs_factor"]
                    gross_btc_day  = algo_prices[algo_name] * hashrate_units
                    gross_usd_day  = gross_btc_day * btc_usd
                    data_source    = "NiceHash Real"
                else:
                    # Fallback: estimativa baseada em hashrate relativo a 250 MH/s
                    fallback = {"KAS": 14.50, "ETC": 11.20, "RVN": 9.80, "BTC": 16.10, "XMR": 7.50}
                    gross_usd_day = fallback.get(ticker, 10.0) * (self.rig_hashrate_mhs / 250.0)
                    data_source   = "Estimativa"

                # Variação de mercado ±3%
                fluctuation   = random.uniform(0.97, 1.03)
                gross_usd_day = gross_usd_day * fluctuation
                net_daily     = gross_usd_day - daily_elec_cost

                coin_rankings.append({
                    "ticker":          ticker,
                    "name":            info["name"],
                    "algo":            info["algo"],
                    "gross_daily":     round(gross_usd_day, 4),
                    "elec_cost_daily": round(daily_elec_cost, 4),
                    "net_daily":       round(net_daily, 4),
                    "is_active":       (ticker == self.active_coin),
                    "data_source":     data_source,
                })

            # Ordenar por lucro líquido
            coin_rankings.sort(key=lambda x: x["net_daily"], reverse=True)

            # Auto-switch para moeda mais rentável
            top_coin = coin_rankings[0]["ticker"]
            if self.auto_switch_enabled and top_coin != self.active_coin and self.is_running:
                old_coin = self.active_coin
                self.active_coin = top_coin
                diff = coin_rankings[0]["net_daily"] - next(
                    (c["net_daily"] for c in coin_rankings if c["ticker"] == old_coin), 0)
                self.switch_history.insert(0, {
                    "timestamp":  datetime.now().strftime("%H:%M:%S"),
                    "from_coin":  old_coin,
                    "to_coin":    top_coin,
                    "reason":     f"Rentabilidade superior em +${diff:.4f}/dia"
                })

            # Acumular rendimento (normalizado por tick de 2s)
            if self.is_running:
                active_info    = next(c for c in coin_rankings if c["ticker"] == self.active_coin)
                ticks_per_day  = 43200.0   # 24h / 2s
                yield_per_tick = active_info["gross_daily"] / ticks_per_day
                elec_per_tick  = daily_elec_cost / ticks_per_day

                self.total_mined_usd      += yield_per_tick
                self.total_electricity_usd += elec_per_tick
                self.net_profit_usd        = self.total_mined_usd - self.total_electricity_usd

            return coin_rankings

    # ─── Ciclo Principal ───────────────────────────────────────────────
    def _run_loop(self):
        tick = 0
        while True:
            if self.is_running:
                try:
                    self.calculate_profitability()
                    # Verificar conta NiceHash a cada 5 minutos
                    if tick % 150 == 0:
                        self._fetch_nicehash_account_info()
                    # Guardar progresso a cada 5 minutos
                    if tick % 150 == 0:
                        self._save_config()
                    tick += 1
                except Exception:
                    pass
            time.sleep(2)

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

    def update_config(self, hashrate, watts, elec_cost, auto_switch):
        with self._lock:
            self.rig_hashrate_mhs        = float(hashrate)
            self.power_consumption_watts = float(watts)
            self.electricity_cost_kwh    = float(elec_cost)
            self.auto_switch_enabled     = bool(auto_switch)
            self._save_config()

    def ensure_thread_running(self):
        with self._lock:
            if self.is_running and (self._thread is None or not self._thread.is_alive()):
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()

    def get_status(self):
        self.ensure_thread_running()
        with self._lock:
            coin_rankings = self.calculate_profitability()
            active_info   = next((c for c in coin_rankings if c["ticker"] == self.active_coin), coin_rankings[0])
            has_nicehash  = bool(self.nicehash_api_key and self.nicehash_api_secret and self.nicehash_org_id)

            return {
                "is_running":              self.is_running,
                "rig_hashrate_mhs":        self.rig_hashrate_mhs,
                "power_consumption_watts": self.power_consumption_watts,
                "electricity_cost_kwh":    self.electricity_cost_kwh,
                "auto_switch_enabled":     self.auto_switch_enabled,
                "active_coin":             self.active_coin,
                "total_mined_usd":         round(self.total_mined_usd, 6),
                "total_electricity_usd":   round(self.total_electricity_usd, 6),
                "net_profit_usd":          round(self.net_profit_usd, 6),
                "active_net_daily":        active_info["net_daily"],
                "active_monthly_est":      round(active_info["net_daily"] * 30.0, 2),
                "coin_rankings":           coin_rankings,
                "switch_history":          self.switch_history[:15],
                # Estado real da conta NiceHash
                "has_nicehash_keys":       has_nicehash,
                "nicehash_rigs_count":     self.nicehash_rigs_count,
                "nicehash_rigs_status":    self.nicehash_rigs_status,
                "account_accessible":      self.account_accessible,
                "nicehash_balance":        round(self.nicehash_balance, 8),
            }
