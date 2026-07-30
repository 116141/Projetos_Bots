import sys
import os

# Adicionar os diretórios ao PATH para permitir imports locais
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_dir, "projects"))

print("=== INICIANDO TESTE DOS MOTORES ===")

# Teste Bot 01
try:
    from bot_01_trading_crypto.bot_engine import TradingBotEngine as Bot01
    bot1 = Bot01()
    print(f"✅ Bot 01 (QuantTrader): Instanciado com sucesso. Take Profit está a {bot1.take_profit_pct}%")
except Exception as e:
    print(f"❌ Erro no Bot 01: {e}")

# Teste Bot 03
try:
    from bot_03_arbitragem_crypto.arbitrage_engine import ArbitrageBotEngine as Bot03
    bot3 = Bot03()
    # Simular atualização de preços
    bot3.update_prices()
    print(f"✅ Bot 03 (ArbitragePro): Oportunidades detetadas com nova volatilidade: {len(bot3.opportunities)}")
except Exception as e:
    print(f"❌ Erro no Bot 03: {e}")

# Teste Bot 04
try:
    from bot_04_mineracao_crypto.staking_engine import YieldEngine as Bot04
    bot4 = Bot04()
    # Atualizar oportunidades de USDT (onde adicionámos a Raydium a 142%)
    bot4.active_coin = "USDT"
    bot4.update_opportunities()
    best_apy = bot4.opportunities[0]['apy'] if bot4.opportunities else 0
    print(f"✅ Bot 04 (YieldPro): Melhor APY encontrado para USDT é {best_apy}%")
except Exception as e:
    print(f"❌ Erro no Bot 04: {e}")

# Teste Bot 05
try:
    from bot_05_sentimento_ia.sentinel_engine import CryptoSentinelEngine as Bot05
    bot5 = Bot05()
    print(f"✅ Bot 05 (Sentinel AI): Threshold de impacto mínimo está a {bot5.min_impact_threshold * 100}%")
except Exception as e:
    print(f"❌ Erro no Bot 05: {e}")

print("=== FIM DOS TESTES ===")
