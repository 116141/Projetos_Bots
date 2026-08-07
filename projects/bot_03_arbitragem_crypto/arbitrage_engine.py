import os
import json
import time
import random
import threading
import requests
from datetime import datetime

class ArbitrageBotEngine:
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        self.is_running = True
        self.symbol = "BTC/USDT"
        self.min_spread_pct = 0.2  # Minimum net profit threshold (%)
        self.trade_amount = 5.0  # $ per arbitrage trade
        self.trading_mode = "LIVE"  # Default to LIVE mode
        
        # API Keys para Corretoras (Binance / Bybit / KuCoin)
        self.binance_api_key = os.environ.get('BINANCE_API_KEY', '') or os.environ.get('BINANCE_KEY', '')
        self.binance_secret_key = os.environ.get('BINANCE_SECRET_KEY', '') or os.environ.get('BINANCE_SECRET', '')
        self.bybit_api_key = os.environ.get('BYBIT_API_KEY', '') or os.environ.get('BYBIT_KEY', '') or os.environ.get('BYBIT_APIKEY', '')
        self.bybit_secret_key = os.environ.get('BYBIT_SECRET_KEY', '') or os.environ.get('BYBIT_SECRET', '') or os.environ.get('BYBIT_SECRETKEY', '')
        
        # Stats
        self.initial_balance = 10000.0
        self.total_profit = 0.0
        self.opportunities_found = 0
        self.last_execution_status = "Varredura ativa. A aguardar discrepância de preço..."
        
        # Dual Exchange Real Balances
        self.binance_balance = 0.0
        self.bybit_balance = 9.43
        self.bybit_usdt_balance = 0.0   # Saldo livre em USDT na Bybit
        self.bybit_btc_balance = 0.0    # Saldo em BTC na Bybit
        self.executed_trades = []
        
        # Exchange Price State
        self.exchanges = ["Binance", "Bybit", "KuCoin", "Kraken", "Gate.io"]
        self.latest_prices = {}
        
        self._lock = threading.Lock()
        self._load_config()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    self.trading_mode = cfg.get('trading_mode', 'LIVE')
                    self.symbol = cfg.get('symbol', 'BTC/USDT')
                    self.min_spread_pct = float(cfg.get('min_spread_pct', 0.1))
                    self.trade_amount = float(cfg.get('trade_amount', 9.0))
                    if cfg.get('bybit_api_key'):
                        self.bybit_api_key = cfg.get('bybit_api_key')
                    if cfg.get('bybit_secret_key'):
                        self.bybit_secret_key = cfg.get('bybit_secret_key')
                    self.total_profit = float(cfg.get('total_profit', 0.0))
                    self.opportunities_found = int(cfg.get('opportunities_found', 0))
                    self.executed_trades = cfg.get('executed_trades', [])
            except Exception:
                pass

    def _save_config(self):
        try:
            cfg = {
                'trading_mode': self.trading_mode,
                'symbol': self.symbol,
                'min_spread_pct': self.min_spread_pct,
                'trade_amount': self.trade_amount,
                'bybit_api_key': self.bybit_api_key,
                'bybit_secret_key': self.bybit_secret_key,
                'total_profit': round(self.total_profit, 2),
                'opportunities_found': self.opportunities_found,
                'executed_trades': self.executed_trades[:100]
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def fetch_live_exchange_prices(self):
        symbol_fmt = self.symbol.replace("/", "")       # e.g. BTCUSDT
        symbol_dash = self.symbol.replace("/", "-")     # e.g. BTC-USDT
        symbol_slash = self.symbol                      # e.g. BTC/USDT
        prices = {}

        # --- Binance ---
        try:
            res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_fmt}", timeout=3)
            if res.status_code == 200:
                prices["Binance"] = float(res.json()["price"])
        except Exception:
            pass

        # --- Bybit ---
        try:
            res = requests.get(f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol_fmt}", timeout=3)
            if res.status_code == 200:
                lst = res.json().get("result", {}).get("list", [])
                if lst:
                    prices["Bybit"] = float(lst[0]["lastPrice"])
        except Exception:
            pass

        # --- KuCoin ---
        try:
            res = requests.get(f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol_dash}", timeout=3)
            if res.status_code == 200:
                data = res.json().get("data", {})
                if data and data.get("price"):
                    prices["KuCoin"] = float(data["price"])
        except Exception:
            pass

        # --- Kraken ---
        try:
            kraken_sym = "XBTUSDT" if "BTC" in self.symbol else symbol_fmt
            res = requests.get(f"https://api.kraken.com/0/public/Ticker?pair={kraken_sym}", timeout=3)
            if res.status_code == 200:
                result = res.json().get("result", {})
                if result:
                    ticker = list(result.values())[0]
                    prices["Kraken"] = float(ticker["c"][0])
        except Exception:
            pass

        # --- Gate.io ---
        try:
            gate_sym = self.symbol.replace("/", "_")
            res = requests.get(f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={gate_sym}", timeout=3)
            if res.status_code == 200:
                lst = res.json()
                if lst:
                    prices["Gate.io"] = float(lst[0]["last"])
        except Exception:
            pass

        # Fallback: se nao conseguiu precos reais de suficientes corretoras, usa Binance como base
        if len(prices) < 2:
            try:
                res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_fmt}", timeout=3)
                base = float(res.json()["price"]) if res.status_code == 200 else 65000.0
            except Exception:
                base = 65000.0
            for ex in self.exchanges:
                if ex not in prices:
                    prices[ex] = round(base * (1 + random.uniform(-0.003, 0.003)), 2)

        with self._lock:
            self.latest_prices = prices
        return prices

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
        while True:
            if self.is_running:
                try:
                    self.scan_arbitrage_opportunities()
                except Exception as e:
                    self.last_execution_status = f"⚠️ Erro no loop: {str(e)}"
            time.sleep(2)

    def execute_real_bybit_order(self, symbol, side, qty_usd, current_price=65000.0):
        """Executa uma ordem REAL no mercado Spot da Bybit via API V5"""
        if not (self.bybit_api_key and self.bybit_secret_key):
            self.last_execution_status = "⚠️ Chaves API da Bybit ausentes nas variáveis do Render"
            return False, "Chaves API da Bybit ausentes"

        try:
            import hmac
            import hashlib
            import json

            symbol_fmt = symbol.replace("/", "")
            timestamp = str(int(time.time() * 1000))
            recv_window = "5000"
            
            # Para COMPRA (Buy), qty é o valor em USDT (ex: 5.0 USDT)
            # Para VENDA (Sell), qty é a quantidade exata em BTC (ex: 5.0 / 65000 = 0.00007692 BTC)
            if side == "Buy":
                qty_str = str(round(qty_usd, 2))
            else:
                btc_qty = qty_usd / float(current_price)
                qty_str = f"{btc_qty:.8f}"
            
            body_dict = {
                "category": "spot",
                "symbol": symbol_fmt,
                "side": side,
                "orderType": "Market",
                "qty": qty_str
            }
            body_json = json.dumps(body_dict)
            
            param_str = timestamp + self.bybit_api_key + recv_window + body_json
            signature = hmac.new(self.bybit_secret_key.encode('utf-8'), param_str.encode('utf-8'), hashlib.sha256).hexdigest()

            headers = {
                "Content-Type": "application/json",
                "X-BAPI-API-KEY": self.bybit_api_key,
                "X-BAPI-SIGN": signature,
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-RECV-WINDOW": recv_window
            }

            res = requests.post("https://api.bybit.com/v5/order/create", data=body_json, headers=headers, timeout=5)
            if res.status_code == 200:
                resp_json = res.json()
                if resp_json.get("retCode") == 0:
                    self.last_execution_status = f"✅ Ordem {side} de ${qty_usd} executada com sucesso na Bybit!"
                    return True, resp_json.get("result", {})
                else:
                    ret_msg = resp_json.get("retMsg", "Erro Bybit")
                    self.last_execution_status = f"⚠️ Bybit recusa: {ret_msg}"
                    return False, ret_msg
            self.last_execution_status = f"⚠️ Bybit Erro HTTP {res.status_code}"
            return False, f"HTTP {res.status_code}"
        except Exception as e:
            self.last_execution_status = f"⚠️ Exceção Bybit: {str(e)}"
            return False, str(e)

    def get_status(self):
        self.ensure_thread_running()
        self.fetch_real_exchange_balances()
        with self._lock:
            has_api_keys = bool(self.binance_api_key or self.bybit_api_key)
            if self.trading_mode == "LIVE":
                total_equity = self.binance_balance + self.bybit_balance
            else:
                total_equity = self.initial_balance + self.total_profit

            return {
                "is_running": self.is_running,
                "symbol": self.symbol,
                "min_spread_pct": self.min_spread_pct,
                "trade_amount": self.trade_amount,
                "trading_mode": self.trading_mode,
                "has_api_keys": has_api_keys,
                "binance_balance": round(self.binance_balance, 2),
                "bybit_balance": round(self.bybit_balance, 2),
                "initial_balance": self.initial_balance,
                "total_equity": round(total_equity, 2),
                "total_profit": round(self.total_profit, 2),
                "opportunities_found": self.opportunities_found,
                "last_execution_status": self.last_execution_status,
                "latest_prices": self.latest_prices,
                "executed_trades": self.executed_trades[:50]
            }

    def scan_arbitrage_opportunities(self):
        prices = self.fetch_live_exchange_prices()
        
        if not prices:
            return None

        # No modo CONTA REAL (LIVE):
        if self.trading_mode == "LIVE":
            live_balance = self.binance_balance + self.bybit_balance
            if live_balance <= 0:
                return None

            has_binance_funds = (self.binance_balance > 0)
            has_bybit_funds = (self.bybit_balance > 0)

            # CASO 1: Saldo em AMBAS as corretoras (Arbitragem Dual Perfeita Binance <-> Bybit)
            if has_binance_funds and has_bybit_funds:
                dual_prices = {k: v for k, v in prices.items() if k in ["Binance", "Bybit"]}
                if len(dual_prices) == 2:
                    buy_ex = min(dual_prices, key=dual_prices.get)
                    sell_ex = max(dual_prices, key=dual_prices.get)
                    buy_price = dual_prices[buy_ex]
                    sell_price = dual_prices[sell_ex]

                    raw_spread_pct = ((sell_price - buy_price) / buy_price) * 100
                    net_spread_pct = raw_spread_pct - 0.2

                    if net_spread_pct >= self.min_spread_pct:
                        side_bybit = "Buy" if buy_ex == "Bybit" else "Sell"
                        success, _ = self.execute_real_bybit_order(self.symbol, side_bybit, self.trade_amount, current_price=buy_price)

                        if success:
                            with self._lock:
                                self.opportunities_found += 1
                                net_profit_dollar = (self.trade_amount * (net_spread_pct / 100))
                                self.total_profit += net_profit_dollar

                                trade_record = {
                                    "id": len(self.executed_trades) + 1,
                                    "date": datetime.now().strftime("%Y-%m-%d"),
                                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                                    "symbol": self.symbol,
                                    "buy_exchange": buy_ex,
                                    "buy_price": buy_price,
                                    "sell_exchange": sell_ex,
                                    "sell_price": sell_price,
                                    "gross_spread_pct": round(raw_spread_pct, 2),
                                    "net_spread_pct": round(net_spread_pct, 2),
                                    "net_profit": round(net_profit_dollar, 2),
                                    "status": "REAL DUAL EXECUTADO"
                                }
                                self.executed_trades.insert(0, trade_record)
                                return trade_record
                return None

            # CASO 2: Saldo em apenas UMA corretora (Ex: Bybit) -> Compara a Bybit contra cada uma das outras 4 corretoras!
            bybit_price = prices.get("Bybit")
            if not (has_bybit_funds and bybit_price):
                return None

            for other_ex, other_price in prices.items():
                if other_ex == "Bybit":
                    continue

                # Sub-caso A: Bybit está MAIS BARATA do que a outra corretora -> COMPRA na Bybit!
                if bybit_price < other_price:
                    raw_spread_pct = ((other_price - bybit_price) / bybit_price) * 100
                    net_spread_pct = raw_spread_pct - 0.1  # Taxa Bybit Spot: 0.1%

                    # Calcular montante real disponivel em USDT
                    available_usdt = self.bybit_usdt_balance if self.bybit_usdt_balance > 0 else self.trade_amount
                    actual_amount = min(self.trade_amount, available_usdt)
                    bybit_min_order = 5.0

                    if net_spread_pct >= self.min_spread_pct:
                        if actual_amount < bybit_min_order:
                            self.last_execution_status = f"⚠️ Spread OK ({net_spread_pct:.3f}%) mas USDT insuficiente (${available_usdt:.2f}). Min: $5"
                        else:
                            success, details = self.execute_real_bybit_order(self.symbol, "Buy", actual_amount, current_price=bybit_price)
                            if success:
                                with self._lock:
                                    self.opportunities_found += 1
                                    net_profit_dollar = (actual_amount * (net_spread_pct / 100))
                                    self.total_profit += net_profit_dollar

                                    trade_record = {
                                        "id": len(self.executed_trades) + 1,
                                        "date": datetime.now().strftime("%Y-%m-%d"),
                                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                                        "symbol": self.symbol,
                                        "buy_exchange": "Bybit",
                                        "buy_price": round(bybit_price, 2),
                                        "sell_exchange": other_ex,
                                        "sell_price": round(other_price, 2),
                                        "gross_spread_pct": round(raw_spread_pct, 2),
                                        "net_spread_pct": round(net_spread_pct, 2),
                                        "net_profit": round(net_profit_dollar, 2),
                                        "status": "REAL EXECUTADO"
                                    }
                                    self.executed_trades.insert(0, trade_record)
                                    self._save_config()
                                    return trade_record
                    else:
                        self.last_execution_status = f"🔍 Bybit<{other_ex}: spread bruto={raw_spread_pct:.3f}% | liquido={net_spread_pct:.3f}% < {self.min_spread_pct}%"

                # Sub-caso B: Bybit está MAIS CARA do que a outra corretora -> VENDA na Bybit!
                elif bybit_price > other_price:
                    raw_spread_pct = ((bybit_price - other_price) / other_price) * 100
                    net_spread_pct = raw_spread_pct - 0.1  # Taxa Bybit Spot: 0.1%

                    # Para VENDA: usa o BTC disponivel na conta
                    available_btc = self.bybit_btc_balance
                    btc_needed = self.trade_amount / other_price

                    if net_spread_pct >= self.min_spread_pct:
                        if available_btc < btc_needed * 0.5:
                            self.last_execution_status = f"⚠️ Spread OK ({net_spread_pct:.3f}%) mas BTC insuficiente ({available_btc:.8f} BTC)"
                        else:
                            sell_amount = min(self.trade_amount, available_btc * other_price)
                            success, details = self.execute_real_bybit_order(self.symbol, "Sell", sell_amount, current_price=other_price)
                            if success:
                                with self._lock:
                                    self.opportunities_found += 1
                                    net_profit_dollar = (sell_amount * (net_spread_pct / 100))
                                    self.total_profit += net_profit_dollar

                                    trade_record = {
                                        "id": len(self.executed_trades) + 1,
                                        "date": datetime.now().strftime("%Y-%m-%d"),
                                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                                        "symbol": self.symbol,
                                        "buy_exchange": other_ex,
                                        "buy_price": round(other_price, 2),
                                        "sell_exchange": "Bybit",
                                        "sell_price": round(bybit_price, 2),
                                        "gross_spread_pct": round(raw_spread_pct, 2),
                                        "net_spread_pct": round(net_spread_pct, 2),
                                        "net_profit": round(net_profit_dollar, 2),
                                        "status": "REAL EXECUTADO"
                                    }
                                    self.executed_trades.insert(0, trade_record)
                                    self._save_config()
                                    return trade_record
                    else:
                        self.last_execution_status = f"🔍 Bybit>{other_ex}: spread bruto={raw_spread_pct:.3f}% | liquido={net_spread_pct:.3f}% < {self.min_spread_pct}%"
            return None

        # Modo SIMULAÇÃO (Paper Trading)
        buy_ex = min(prices, key=prices.get)
        sell_ex = max(prices, key=prices.get)
        
        buy_price = prices[buy_ex]
        sell_price = prices[sell_ex]

        raw_spread = sell_price - buy_price
        raw_spread_pct = (raw_spread / buy_price) * 100
        net_spread_pct = raw_spread_pct - 0.2

        with self._lock:
            if net_spread_pct >= self.min_spread_pct:
                self.opportunities_found += 1
                net_profit_dollar = (self.trade_amount * (net_spread_pct / 100))
                self.total_profit += net_profit_dollar

                trade_record = {
                    "id": len(self.executed_trades) + 1,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "symbol": self.symbol,
                    "buy_exchange": buy_ex,
                    "buy_price": buy_price,
                    "sell_exchange": sell_ex,
                    "sell_price": sell_price,
                    "gross_spread_pct": round(raw_spread_pct, 2),
                    "net_spread_pct": round(net_spread_pct, 2),
                    "net_profit": round(net_profit_dollar, 2),
                    "status": "SIMULADO"
                }
                self.executed_trades.insert(0, trade_record)
                return trade_record
        return None

    def reset_stats(self):
        with self._lock:
            self.total_profit = 0.0
            self.opportunities_found = 0
            self.executed_trades = []

    def update_config(self, symbol, min_spread, trade_amount, trading_mode="LIVE", reset_now=False, bybit_api_key=None, bybit_secret_key=None):
        with self._lock:
            self.trading_mode = str(trading_mode).upper()

            # APENAS reseta se o utilizador clicar explicitamente no botão "Limpar Painel" (reset_now=True)!
            if reset_now:
                self.total_profit = 0.0
                self.opportunities_found = 0
                self.executed_trades = []

            self.symbol = symbol
            self.min_spread_pct = float(min_spread)
            self.trade_amount = float(trade_amount)
            if bybit_api_key:
                self.bybit_api_key = str(bybit_api_key).strip()
            if bybit_secret_key:
                self.bybit_secret_key = str(bybit_secret_key).strip()
            self._save_config()

    def fetch_real_exchange_balances(self):
        """Busca o saldo real das contas via API Bybit V5 e Binance API"""
        now = time.time()
        if hasattr(self, '_last_balance_check') and (now - getattr(self, '_last_balance_check', 0) < 10):
            return
        self._last_balance_check = now

        if self.bybit_api_key and self.bybit_secret_key:
            try:
                import ccxt
                ex = ccxt.bybit({
                    'apiKey': self.bybit_api_key,
                    'secret': self.bybit_secret_key,
                    'enableRateLimit': True
                })
                bal = ex.fetch_balance()
                usdt = float(bal.get('USDT', {}).get('free', 0.0) or 0.0)
                btc = float(bal.get('BTC', {}).get('free', 0.0) or 0.0)
                curr_price = self.latest_prices.get('Bybit', 64700.0)
                total_val = usdt + (btc * curr_price)
                
                self.bybit_usdt_balance = usdt
                self.bybit_btc_balance = btc
                self.bybit_balance = round(total_val, 2) if total_val > 0 else 0.0
            except Exception as e:
                print(f"Erro ao buscar saldo Bybit no Bot 03: {e}")

    def ensure_thread_running(self):
        """Garante que a thread em segundo plano está viva dentro do processo Gunicorn"""
        with self._lock:
            if self.is_running and (self._thread is None or not self._thread.is_alive()):
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()

    def get_status(self):
        self.ensure_thread_running()
        self.fetch_real_exchange_balances()
        with self._lock:
            has_api_keys = bool(self.binance_api_key or self.bybit_api_key)
            if self.trading_mode == "LIVE":
                total_equity = self.binance_balance + self.bybit_balance
            else:
                total_equity = self.initial_balance + self.total_profit

            return {
                "is_running": self.is_running,
                "symbol": self.symbol,
                "min_spread_pct": self.min_spread_pct,
                "trade_amount": self.trade_amount,
                "trading_mode": self.trading_mode,
                "has_api_keys": has_api_keys,
                "binance_balance": round(self.binance_balance, 2),
                "bybit_balance": round(self.bybit_balance, 2),
                "initial_balance": self.initial_balance,
                "total_equity": round(total_equity, 2),
                "total_profit": round(self.total_profit, 2),
                "opportunities_found": self.opportunities_found,
                "last_execution_status": self.last_execution_status,
                "latest_prices": self.latest_prices,
                "executed_trades": self.executed_trades[:50]
            }
