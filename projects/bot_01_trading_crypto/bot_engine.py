import time
import threading
import random
import requests
from datetime import datetime

class TradingBotEngine:
    def __init__(self):
        self.is_running = True
        self.symbol = "BTC/USDT"
        self.strategy = "MA_CROSSOVER"
        self.trade_amount = 500.0  # $ per trade
        self.take_profit_pct = 2.0  # %
        self.stop_loss_pct = 1.0    # %
        
        # Paper Trading Portfolio State
        self.initial_balance = 10000.0
        self.usdt_balance = 10000.0
        self.crypto_balance = 0.0
        
        # Market Data Memory
        self.price_history = []
        self.current_price = 64500.0
        self.trades = []
        self.active_position = None  # Dict if long position open
        
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def get_binance_symbol(self):
        return self.symbol.replace("/", "")

    def fetch_live_price(self):
        try:
            symbol_fmt = self.get_binance_symbol()
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_fmt}"
            res = requests.get(url, timeout=3)
            if res.status_code == 200:
                data = res.json()
                price = float(data['price'])
                with self._lock:
                    self.current_price = price
                    self.price_history.append(price)
                    if len(self.price_history) > 100:
                        self.price_history.pop(0)
                return price
        except Exception:
            # Fallback simulated movement if offline or API limit
            with self._lock:
                change = random.uniform(-0.003, 0.003)
                self.current_price = round(self.current_price * (1 + change), 2)
                self.price_history.append(self.current_price)
                if len(self.price_history) > 100:
                    self.price_history.pop(0)
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

    def calculate_sma(self, period=7):
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

    def update_config(self, symbol, strategy, trade_amount, take_profit, stop_loss):
        with self._lock:
            if self.symbol != symbol:
                self.symbol = symbol
                self.price_history.clear()
            self.strategy = strategy
            self.trade_amount = float(trade_amount)
            self.take_profit_pct = float(take_profit)
            self.stop_loss_pct = float(stop_loss)

    def _run_loop(self):
        while self.is_running:
            price = self.fetch_live_price()
            self._evaluate_strategy(price)
            time.sleep(3)

    def _evaluate_strategy(self, price):
        with self._lock:
            rsi = self.calculate_rsi()
            sma_fast = self.calculate_sma(7)
            sma_slow = self.calculate_sma(25)

            # Manage active position (Check Take Profit / Stop Loss / Trailing Stop)
            if self.active_position is not None:
                entry_price = self.active_position['entry_price']
                pnl_pct = ((price - entry_price) / entry_price) * 100

                # Update peak price for trailing stop
                if price > self.active_position.get('highest_price', entry_price):
                    self.active_position['highest_price'] = price

                highest_price = self.active_position.get('highest_price', entry_price)
                drop_from_peak_pct = ((highest_price - price) / highest_price) * 100

                should_close = False
                close_reason = ""

                if pnl_pct >= self.take_profit_pct:
                    should_close = True
                    close_reason = f"Take Profit (+{pnl_pct:.2f}%)"
                elif pnl_pct <= -self.stop_loss_pct:
                    should_close = True
                    close_reason = f"Stop Loss ({pnl_pct:.2f}%)"
                elif drop_from_peak_pct >= 0.8 and pnl_pct >= 0.4:
                    should_close = True
                    close_reason = f"Trailing Profit Lock (+{pnl_pct:.2f}%)"
                elif self.strategy == "RSI_SCALPING" and rsi >= 65:
                    should_close = True
                    close_reason = f"RSI Exit ({rsi:.1f})"

                if should_close:
                    total_pnl = (price - entry_price) * self.active_position['amount']
                    self.usdt_balance += (self.active_position['amount'] * price)
                    self.crypto_balance = 0.0

                    trade_record = {
                        "id": len(self.trades) + 1,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "symbol": self.symbol,
                        "type": "SELL",
                        "price": price,
                        "amount": self.active_position['amount'],
                        "pnl": total_pnl,
                        "pnl_pct": pnl_pct,
                        "reason": close_reason
                    }
                    self.trades.insert(0, trade_record)
                    self.active_position = None
                return

            # Signal Generation for BUY (with Smart Entry Filters)
            signal_buy = False
            if len(self.price_history) >= 26:
                prev_sma_fast = sum(self.price_history[-8:-1]) / 7.0
                prev_sma_slow = sum(self.price_history[-26:-1]) / 25.0

                # 1. MA Crossover: ONLY buy on true bullish crossover AND when RSI < 60 (Not Overbought)
                if self.strategy == "MA_CROSSOVER":
                    if (prev_sma_fast <= prev_sma_slow) and (sma_fast > sma_slow) and (rsi < 60):
                        signal_buy = True

                # 2. RSI Scalping: Buy when deeply oversold (RSI <= 30)
                elif self.strategy == "RSI_SCALPING":
                    if rsi <= 30:
                        signal_buy = True

                # 3. Grid Trading: Buy when price dips 0.8% below Fast SMA AND RSI < 45
                elif self.strategy == "GRID_TRADING":
                    if price < (sma_fast * 0.992) and rsi < 45:
                        signal_buy = True

            if signal_buy and self.usdt_balance >= self.trade_amount:
                amount_crypto = self.trade_amount / price
                self.usdt_balance -= self.trade_amount
                self.crypto_balance = amount_crypto

                self.active_position = {
                    "entry_price": price,
                    "highest_price": price,
                    "amount": amount_crypto,
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
                    "reason": f"Smart Entry ({self.strategy})"
                }
                self.trades.insert(0, trade_record)

    def get_status(self):
        with self._lock:
            curr_price = self.current_price if self.current_price > 0 else 64500.0
            total_equity = self.usdt_balance + (self.crypto_balance * curr_price)
            net_pnl = total_equity - self.initial_balance
            net_pnl_pct = (net_pnl / self.initial_balance) * 100

            wins = [t for t in self.trades if t['type'] == 'SELL' and t['pnl'] > 0]
            losses = [t for t in self.trades if t['type'] == 'SELL' and t['pnl'] <= 0]
            total_closed = [t for t in self.trades if t['type'] == 'SELL']
            win_rate = (len(wins) / len(total_closed) * 100) if total_closed else 0.0

            return {
                "is_running": self.is_running,
                "symbol": self.symbol,
                "strategy": self.strategy,
                "current_price": curr_price,
                "rsi": self.calculate_rsi(),
                "sma_fast": round(self.calculate_sma(7), 2),
                "sma_slow": round(self.calculate_sma(25), 2),
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
                "trades": self.trades[:20]
            }
