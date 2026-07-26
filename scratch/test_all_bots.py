import os
import sys
import time

# Add project root to PYTHONPATH
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from projects.bot_01_trading_crypto.bot_engine import TradingBotEngine
from projects.bot_02_afiliados_telegram.deal_engine import DealHunterEngine
from projects.bot_03_arbitragem_crypto.arbitrage_engine import ArbitrageBotEngine
from projects.bot_04_mineracao_crypto.mining_engine import AutoMineEngine
from projects.bot_05_sentimento_ia.sentinel_engine import CryptoSentinelEngine

print("==================================================")
print("🧪 TESTE AUTOMÁTICO DE VERIFICAÇÃO DOS 5 BOTS")
print("==================================================")

# Test 1: Bot 01
print("\n--- [BOT 01: QuantTrader AI] ---")
b1 = TradingBotEngine()
time.sleep(4)
st1 = b1.get_status()
print(f"Status: is_running={st1['is_running']}")
print(f"Preço BTC Atual: ${st1['current_price']}")
print(f"Pontos de Preço no Gráfico: {len(st1['price_history'])}")
print(f"Resultado Bot 01: {'✅ OK' if st1['is_running'] and len(st1['price_history']) > 0 else '❌ ERRO'}")

# Test 2: Bot 02
print("\n--- [BOT 02: DealHunter AI - Telegram] ---")
b2 = DealHunterEngine()
time.sleep(4)
st2 = b2.get_status()
print(f"Status: is_running={st2['is_running']}")
print(f"Ofertas Capturadas: {st2['deals_found_count']}")
print(f"Amazon Tag Oficial: {st2['amazon_tag']}")
print(f"Telegram Bot Token: {st2['telegram_bot_token'][:15]}...")
print(f"Telegram Chat ID: {st2['telegram_chat_id']}")

# Force 1 real scan and post
deal_record = b2.scan_for_deals()
print(f"Oferta Sorteada: [{deal_record['platform']}] {deal_record['title']}")
print(f"Link Afiliado Injetado: {deal_record['affiliate_url']}")
print(f"Postado no Telegram: {deal_record['telegram_posted']}")
print(f"Resultado Bot 02: {'✅ OK' if st2['is_running'] else '❌ ERRO'}")

# Test 3: Bot 03
print("\n--- [BOT 03: ArbitragePro AI] ---")
b3 = ArbitrageBotEngine()
time.sleep(4)
st3 = b3.get_status()
print(f"Status: is_running={st3['is_running']}")
print(f"Preços de Corretoras Capturados: {len(st3['latest_prices'])}")
print(f"Resultado Bot 03: {'✅ OK' if st3['is_running'] else '❌ ERRO'}")

# Test 4: Bot 04
print("\n--- [BOT 04: AutoMine AI] ---")
b4 = AutoMineEngine()
time.sleep(4)
st4 = b4.get_status()
print(f"Status: is_running={st4['is_running']}")
print(f"Moeda Ativa: {st4['active_coin']}")
print(f"Lucro Mensal Estimado: €{st4['active_monthly_est']}")
print(f"Resultado Bot 04: {'✅ OK' if st4['is_running'] else '❌ ERRO'}")

# Test 5: Bot 05
print("\n--- [BOT 05: Sentinel AI] ---")
b5 = CryptoSentinelEngine()
time.sleep(4)
st5 = b5.get_status()
print(f"Status: is_running={st5['is_running']}")
print(f"Fear & Greed Index: {st5['fear_greed_index']} ({st5['fear_greed_text']})")
print(f"Artigos Analisados: {st5['articles_analyzed_count']}")
print(f"Resultado Bot 05: {'✅ OK' if st5['is_running'] else '❌ ERRO'}")

print("\n==================================================")
print("🏆 VERIFICAÇÃO AUTOMÁTICA CONCLUÍDA")
print("==================================================")
