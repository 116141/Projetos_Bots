import os
import json
import time
import threading
import requests
import ccxt
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class TradingBotEngine:
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        self.is_running = True
        self.symbol = "BTC/USDT"
        self.strategy = "MA_CROSSOVER"
        self.trade_amount = 5.0    # $ per trade
        self.take_profit_pct = 0.5  # % (ajustado para scalping rapido 1m)
        self.stop_loss_pct = 0.4    # % (gestão de risco curta)
        self.interval = "1m"        # Usar velas de 1 minuto para mais entradas
        
        # CCXT Exchange Setup (Bybit Spot)
        self.api_key = os.getenv("BYBIT_API_KEY", "")
        self.api_secret = os.getenv("BYBIT_API_SECRET", "")
        self.exchange = None
        
        if self.api_key and self.api_secret:
            try:
                self.exchange = ccxt.bybit({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'enableRateLimit': True,
                    'options': {'defaultType': 'spot'}
                })
                self.trading_mode = "LIVE"
            except Exception as e:
                print(f"Erro ao ligar à Bybit: {e}")
                self.exchange = None
                self.trading_mode = "PAPER"
        else:
            self.trading_mode = "PAPER"
        
        # Portfolio State
        self.initial_balance = 10000.0
        self.usdt_balance = 10000.0
        self.crypto_balance = 0.0
        
        # Market Data Memory
        self.current_price = 64500.0
        self.price_history = []     # Histórico de velas (close prices)
        self.trades = []
        self.active_position = None
        
        # Taxas padrão Bybit Spot (Maker 0.1%, Taker 0.1%)
        self.trading_fee = 0.001
        
        self._lock = threading.Lock()
        self._load_config()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    self.symbol = cfg.get('symbol', 'BTC/USDT')
                    self.strategy = cfg.get('strategy', 'MA_CROSSOVER')
                    self.trade_amount = float(cfg.get('trade_amount', 5.0))
                    self.take_profit_pct = float(cfg.get('take_profit_pct', 1.0))
                    self.stop_loss_pct = float(cfg.get('stop_loss_pct', 1.0))
                    
                    if self.trading_mode == "PAPER":
                        self.usdt_balance = float(cfg.get('usdt_balance', 10000.0))
                        self.crypto_balance = float(cfg.get('crypto_balance', 0.0))
                        self.initial_balance = float(cfg.get('initial_balance', 10000.0))
                    self.active_position = cfg.get('active_position', None)
            except Exception:
                pass

    def _save_config(self):
        try:
            cfg = {
                'trading_mode': self.trading_mode,
                'symbol': self.symbol,
                'strategy': self.strategy,
                'trade_amount': self.trade_amount,
                'take_profit_pct': self.take_profit_pct,
                'stop_loss_pct': self.stop_loss_pct,
                'usdt_balance': round(self.usdt_balance, 4),
                'crypto_balance': round(self.crypto_balance, 6),
                'initial_balance': round(self.initial_balance, 4),
                'active_position': self.active_position
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def sync_real_balances(self):
        if self.exchange and self.trading_mode == "LIVE":
            try:
                balance = self.exchange.fetch_balance()
                self.usdt_balance = balance.get('USDT', {}).get('free', 0.0)
                
                base_coin = self.symbol.split('/')[0] # ex: 'BTC'
                self.crypto_balance = balance.get(base_coin, {}).get('free', 0.0)

                # AUTOCURA: Se active_position for None, mas tivermos cripto na carteira (> $1.00), recriar a posição para vender!
                if self.active_position is None and self.current_price > 0:
                    crypto_val = self.crypto_balance * self.current_price
                    if crypto_val >= 1.0:
                        self.active_position = {
                            "entry_price": self.current_price,
                            "highest_price": self.current_price,
                            "amount": self.crypto_balance,
                            "cost_basis": crypto_val,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        }
                        print(f"AUTOCURA: Posição ativa recuperada automaticamente ({self.crypto_balance} {base_coin} = ${crypto_val:.2f})")
                        self._save_config()
            except Exception as e:
                print(f"Erro ao sincronizar saldo: {e}")

    def fetch_klines(self):
        """Busca velas (candles) reais de 5 minutos via CCXT ou Binance API publica"""
        try:
            if self.exchange:
                # Usa CCXT se estiver live
                ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.interval, limit=35)
                closes = [float(candle[4]) for candle in ohlcv]
            else:
                # Usa Binance pública (fallback para paper trading)
                symbol_fmt = self.symbol.replace("/", "")
                url = f"https://api.binance.com/api/v3/klines?symbol={symbol_fmt}&interval={self.interval}&limit=35"
                res = requests.get(url, timeout=3)
                data = res.json()
                closes = [float(candle[4]) for candle in data]
                
            if closes:
                with self._lock:
                    self.current_price = closes[-1]
                    self.price_history = closes
            return self.current_price
        except Exception:
            pass
        return self.current_price

    def calculate_rsi(self, period=14):
        if len(self.price_history) < period + 1:
            return 50.0
        gains = []
        losses = []
        for i in range(1, len(self.price_history[-period-1:])):
            diff = self.price_history[-period-1:][i] - self.price_history[-period-1:][i-1]
            if diff >= 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)

    def calculate_sma(self, period):
        if len(self.price_history) < period:
            return self.current_price
        return sum(self.price_history[-period:]) / period

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

    def update_config(self, symbol, strategy, trade_amount, take_profit, stop_loss, trading_mode="PAPER"):
        with self._lock:
            if self.symbol != symbol:
                self.symbol = symbol
                self.price_history.clear()
            self.strategy = strategy
            self.trade_amount = float(trade_amount)
            self.take_profit_pct = float(take_profit)
            self.stop_loss_pct = float(stop_loss)
            self._save_config()

    def _run_loop(self):
        self.fetch_klines()
        self.sync_real_balances()
        
        while self.is_running:
            price = self.fetch_klines()
            self._evaluate_strategy(price)
            time.sleep(10)

    def _execute_sell_order(self, price, amount, close_reason, net_pnl_pct, net_pnl):
        order_success = False
        
        if self.trading_mode == "LIVE" and self.exchange:
            try:
                # Criar Ordem a Mercado na Bybit
                order = self.exchange.create_market_sell_order(self.symbol, amount)
                print(f"LIVETRADE: Venda Executada na Bybit: {order}")
                self.sync_real_balances()
                order_success = True
            except Exception as e:
                print(f"ERRO LIVETRADE VENDA: {e}")
                close_reason = f"Erro na Corretora: {e}"
        else:
            # Paper Trading
            sell_fee = (amount * price) * self.trading_fee
            net_value = (amount * price) - sell_fee
            self.usdt_balance += net_value
            self.crypto_balance = 0.0
            order_success = True

        if order_success:
            trade_record = {
                "id": len(self.trades) + 1,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "symbol": self.symbol,
                "type": "SELL",
                "price": price,
                "amount": amount,
                "pnl": net_pnl,
                "pnl_pct": net_pnl_pct,
                "reason": close_reason
            }
            self.trades.insert(0, trade_record)
            self.active_position = None
            self._save_config()

    def _execute_buy_order(self, price, amount_crypto, trade_cost, reason):
        order_success = False
        
        if self.trading_mode == "LIVE" and self.exchange:
            try:
                # Dimensionamento Dinâmico: se o saldo USDT for inferior a trade_cost (ex: $5), mas >= $2.0, usar 98% do saldo disponível!
                actual_cost = trade_cost
                if self.usdt_balance < (trade_cost * 1.002) and self.usdt_balance >= 2.0:
                    actual_cost = self.usdt_balance * 0.98
                    amount_crypto = actual_cost / price
                    print(f"LIVETRADE: Ajustando valor da ordem para o saldo livre disponível: ${actual_cost:.2f}")

                if self.usdt_balance >= (actual_cost * 1.002):
                    order = self.exchange.create_market_buy_order(self.symbol, amount_crypto)
                    print(f"LIVETRADE: Compra Executada na Bybit: {order}")
                    self.sync_real_balances()
                    order_success = True
                else:
                    print("LIVETRADE: Saldo insuficiente na Bybit para comprar (mínimo $2.0 USDT).")
            except Exception as e:
                print(f"ERRO LIVETRADE COMPRA: {e}")
        else:
            # Paper Trading
            if self.usdt_balance >= trade_cost:
                self.usdt_balance -= trade_cost
                self.crypto_balance = amount_crypto
                order_success = True

        if order_success:
            self.active_position = {
                "entry_price": price,
                "highest_price": price,
                "amount": amount_crypto,
                "cost_basis": trade_cost,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }

            trade_record = {
                "id": len(self.trades) + 1,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "symbol": self.symbol,
                "type": "BUY",
                "price": price,
                "amount": amount_crypto,
                "pnl": 0.0,
                "pnl_pct": 0.0,
                "reason": reason
            }
            self.trades.insert(0, trade_record)
            self._save_config()

    def _evaluate_strategy(self, price):
        with self._lock:
            if not self.price_history or len(self.price_history) < 26:
                return

            rsi = self.calculate_rsi()
            sma_fast = self.calculate_sma(7) 
            sma_slow = self.calculate_sma(25)

            # Manage active position
            if self.active_position is not None:
                entry_price = self.active_position['entry_price']
                amount_crypto = self.active_position['amount']
                
                gross_value = amount_crypto * price
                sell_fee = gross_value * self.trading_fee
                net_value = gross_value - sell_fee
                net_pnl = net_value - self.active_position['cost_basis']
                net_pnl_pct = (net_pnl / self.active_position['cost_basis']) * 100

                if price > self.active_position.get('highest_price', entry_price):
                    self.active_position['highest_price'] = price

                highest_price = self.active_position.get('highest_price', entry_price)
                drop_from_peak_pct = ((highest_price - price) / highest_price) * 100

                should_close = False
                close_reason = ""

                if net_pnl_pct >= self.take_profit_pct:
                    should_close = True
                    close_reason = f"Take Profit (+{net_pnl_pct:.2f}%)"
                elif net_pnl_pct <= -self.stop_loss_pct:
                    should_close = True
                    close_reason = f"Stop Loss ({net_pnl_pct:.2f}%)"
                elif drop_from_peak_pct >= 0.8 and net_pnl_pct >= 0.5:
                    should_close = True
                    close_reason = f"Trailing Stop Lock (+{net_pnl_pct:.2f}%)"
                elif self.strategy == "RSI_SCALPING" and rsi >= 70 and net_pnl_pct > 0.1:
                    should_close = True
                    close_reason = f"RSI Overbought ({rsi:.1f})"

                if should_close:
                    self._execute_sell_order(price, amount_crypto, close_reason, net_pnl_pct, net_pnl)
                return

            # Signal Generation for BUY
            signal_buy = False
            prev_sma_fast = sum(self.price_history[-8:-1]) / 7.0
            prev_sma_slow = sum(self.price_history[-26:-1]) / 25.0

            if self.strategy == "MA_CROSSOVER":
                if (prev_sma_fast <= prev_sma_slow) and (sma_fast > sma_slow) and (rsi < 65):
                    signal_buy = True
            elif self.strategy == "RSI_SCALPING":
                if rsi <= 30:
                    signal_buy = True
            elif self.strategy == "GRID_TRADING":
                if price < (sma_fast * 0.99) and rsi < 40:
                    signal_buy = True

            if signal_buy:
                buy_fee = self.trade_amount * self.trading_fee
                net_investment = self.trade_amount - buy_fee
                amount_crypto = net_investment / price
                self._execute_buy_order(price, amount_crypto, self.trade_amount, f"Smart Entry ({self.strategy})")

    def ensure_thread_running(self):
        with self._lock:
            if self.is_running and (self._thread is None or not self._thread.is_alive()):
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()

    def get_status(self):
        self.ensure_thread_running()
        with self._lock:
            curr_price = self.current_price if self.current_price > 0 else 64500.0
            
            current_crypto_value = self.crypto_balance * curr_price
            if self.active_position:
                current_crypto_value -= (current_crypto_value * self.trading_fee)
                
            total_equity = self.usdt_balance + current_crypto_value
            
            # Reset initial balance to real equity if switching to LIVE for the first time
            if self.trading_mode == "LIVE" and self.initial_balance == 10000.0 and total_equity > 0 and total_equity < 9900:
                self.initial_balance = total_equity
                self._save_config()
                
            net_pnl = total_equity - self.initial_balance
            net_pnl_pct = (net_pnl / self.initial_balance) * 100

            wins = [t for t in self.trades if t['type'] == 'SELL' and t['pnl'] > 0]
            losses = [t for t in self.trades if t['type'] == 'SELL' and t['pnl'] <= 0]
            total_closed = [t for t in self.trades if t['type'] == 'SELL']
            win_rate = (len(wins) / len(total_closed) * 100) if total_closed else 0.0

            safe_rsi = self.calculate_rsi() if len(self.price_history) >= 15 else 50.0
            safe_sma_fast = self.calculate_sma(7) if len(self.price_history) >= 7 else curr_price
            safe_sma_slow = self.calculate_sma(25) if len(self.price_history) >= 25 else curr_price
            
            display_mode = "🟢 LIVE TRADING (BYBIT)" if self.trading_mode == "LIVE" else "🟡 PAPER TRADING (SIMULADO)"

            return {
                "is_running": self.is_running,
                "symbol": self.symbol,
                "strategy": self.strategy,
                "current_price": curr_price,
                "rsi": safe_rsi,
                "sma_fast": round(safe_sma_fast, 2),
                "sma_slow": round(safe_sma_slow, 2),
                "usdt_balance": round(self.usdt_balance, 2),
                "crypto_balance": round(self.crypto_balance, 6),
                "total_equity": round(total_equity, 2),
                "net_pnl": round(net_pnl, 2),
                "net_pnl_pct": round(net_pnl_pct, 2),
                "win_rate": round(win_rate, 1),
                "winning_trades_count": len(wins),
                "losing_trades_count": len(losses),
                "total_closed_count": len(total_closed),
                "total_trades_count": len(self.trades),
                "active_position": self.active_position,
                "price_history": list(self.price_history[-30:]),
                "trades": self.trades[:20],
                "trading_mode": display_mode
            }
