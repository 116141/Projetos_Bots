import sys, os, time

BOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'projects', 'bot_03_arbitragem_crypto')
BOT_DIR = os.path.normpath(BOT_DIR)
sys.path.insert(0, BOT_DIR)
os.chdir(BOT_DIR)

from arbitrage_engine import ArbitrageBotEngine

print("Importando e iniciando motor...")
bot = ArbitrageBotEngine()
time.sleep(3)

prices = bot.fetch_live_exchange_prices()
print("Precos reais obtidos:")
for ex, p in prices.items():
    print(f"  {ex}: {p:.2f}")

bot.fetch_real_exchange_balances()
time.sleep(1)

print(f"\nSaldo Bybit Total: {bot.bybit_balance:.2f} USD")
print(f"Saldo USDT livre: {bot.bybit_usdt_balance:.2f} USD")
print(f"Saldo BTC: {bot.bybit_btc_balance:.8f} BTC")
print(f"\nAPI Key Bybit OK: {bool(bot.bybit_api_key)}")
print(f"Modo de Operacao: {bot.trading_mode}")
print(f"Spread Minimo: {bot.min_spread_pct}%")
print(f"Trade Amount: {bot.trade_amount} USD")
print(f"Status Motor: {bot.last_execution_status}")

# Simular scan
print("\nA simular um scan de oportunidades...")
result = bot.scan_arbitrage_opportunities()
print(f"Resultado do Scan: {result}")
print(f"Status pos-scan: {bot.last_execution_status}")
print("\nTudo OK!")
