"""
Diagnóstico do Bot 01 - Trading Crypto
Analisa a frequência de trades e a lógica de MA/RSI
"""
import os, sys, time
BOT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'projects', 'bot_01_trading_crypto'))
sys.path.insert(0, BOT_DIR)
os.chdir(BOT_DIR)

from bot_engine import TradingBotEngine

bot = TradingBotEngine()
# Acelerar o teste, ignorando time.sleep interno no _run_loop para vermos 100 ticks
bot.stop()

print("==================================================")
print("📊 DIAGNÓSTICO BOT 01 - ANÁLISE DE TRADING")
print("==================================================")
print(f"Modo: {bot.trading_mode} | Par: {bot.symbol}")
print(f"Estratégia: {bot.strategy}")
print(f"TP: {bot.take_profit_pct}% | SL: {bot.stop_loss_pct}%")

# Simular 100 ticks da Binance
print("\n▶ Simulando 100 interações de mercado...")
for i in range(100):
    price = bot.fetch_klines()
    bot._evaluate_strategy(price)

status = bot.get_status()
print(f"\n▶ RESULTADOS APÓS 100 TICKS (aprox. 5 min de tempo real):")
print(f"Total Trades: {status['total_trades_count']}")
print(f"Win Rate:     {status['win_rate']}%")
print(f"Wins: {status['winning_trades_count']} | Losses: {status['losing_trades_count']}")
print(f"Net PnL:      ${status['net_pnl']} ({status['net_pnl_pct']}%)")
print(f"Últimos trades:")
for t in status['trades'][:5]:
    print(f"  [{t['type']}] {t['reason']} | PnL: ${t['pnl']:.2f} ({t['pnl_pct']:.2f}%)")

print("\n▶ ANÁLISE TÉCNICA (O PORQUÊ DAS PERDAS):")
print("1. O bot calcula SMA_7 e SMA_25 baseado em TICKS (a cada 3s) e não em velas (candles) de 1m ou 5m.")
print("   - Isto significa que a 'Tendência Longa' de 25 períodos tem apenas 75 SEGUNDOS.")
print("   - Ele está a fazer trading em cima de 'ruído' de mercado e não tendências reais.")
print("2. Não contabiliza as taxas de trading (0.1% na Binance), o que agrava as perdas.")
print("3. O 'Trailing Profit' dispara com apenas 0.4% de lucro, e um 'Drop' de 0.8%... A matemática das percentagens do trailing stop está desajustada para ruído de 3 segundos.")
