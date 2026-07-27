"""
Teste rápido do novo motor do Bot 04
"""
import os, sys, time

NICEHASH_API_KEY    = os.environ.get('NICEHASH_API_KEY', 'dd5a7aac-6583-4bbe-b259-96eac067ba36')
NICEHASH_SECRET     = os.environ.get('NICEHASH_API_SECRET', 'ad346d78-fece-470d-8019-dd61f9065ebb171cfdc1-8cf6-4cbb-832f-1ec927e8c4d3')
NICEHASH_ORG_ID     = os.environ.get('NICEHASH_ORG_ID', 'f7152d6f-290d-4132-81aa-1ae60b512ac9')

BOT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'projects', 'bot_04_mineracao_crypto'))
sys.path.insert(0, BOT_DIR)
os.chdir(BOT_DIR)

# Injetar credenciais via env
os.environ['NICEHASH_API_KEY']    = NICEHASH_API_KEY
os.environ['NICEHASH_API_SECRET'] = NICEHASH_SECRET
os.environ['NICEHASH_ORG_ID']     = NICEHASH_ORG_ID

from mining_engine import AutoMineEngine

print("=" * 55)
print("🧪 TESTE DO NOVO MOTOR BOT 04")
print("=" * 55)

print("\n▶ Iniciando motor...")
bot = AutoMineEngine()
time.sleep(3)

print(f"  is_running:    {bot.is_running}")
print(f"  NiceHash Key:  {bot.nicehash_api_key[:12]}...")
print(f"  NiceHash Org:  {bot.nicehash_org_id}")

print("\n▶ Buscando preços reais NiceHash...")
prices = bot._fetch_nicehash_algo_prices()
if prices:
    print(f"  ✅ {len(prices)} algoritmos encontrados na NiceHash")
    for k, v in list(prices.items())[:6]:
        print(f"     {k}: {v:.8f} BTC/TH/dia")
else:
    print("  ⚠️  Nenhum preço obtido (usando fallback)")

print("\n▶ Buscando preço BTC/USD...")
btc = bot._fetch_btc_usd_price()
print(f"  BTC/USD: ${btc:,.2f}")

print("\n▶ Calculando rentabilidade...")
rankings = bot.calculate_profitability()
print(f"  Rankings calculados: {len(rankings)} moedas")
for r in rankings:
    src = r.get('data_source', '?')
    print(f"  {'⭐' if r['is_active'] else '  '} {r['ticker']}: Bruto=${r['gross_daily']:.4f} | Líquido=${r['net_daily']:.4f}/dia [{src}]")

print("\n▶ Verificando conta NiceHash...")
bot._fetch_nicehash_account_info()
print(f"  Rigs:   {bot.nicehash_rigs_count}")
print(f"  Status: {bot.nicehash_rigs_status}")
print(f"  Conta acessível: {bot.account_accessible}")

print("\n▶ Aguardando 4s de acumulação...")
time.sleep(4)
print(f"  Total Minerado:  ${bot.total_mined_usd:.6f}")
print(f"  Custo Elétrico:  ${bot.total_electricity_usd:.6f}")
print(f"  Lucro Líquido:   ${bot.net_profit_usd:.6f}")

print("\n▶ Testando get_status()...")
status = bot.get_status()
keys_ok = all(k in status for k in ['is_running', 'coin_rankings', 'net_profit_usd', 'nicehash_rigs_count'])
print(f"  Chaves obrigatórias: {'✅ OK' if keys_ok else '❌ FALTAM CAMPOS'}")
print(f"  Moeda ativa: {status['active_coin']}")
print(f"  Lucro diário estimado: ${status['active_net_daily']:.4f}")
print(f"  NiceHash rigs: {status['nicehash_rigs_count']}")
print(f"  NiceHash status: {status['nicehash_rigs_status']}")

print("\n▶ Verificando sintaxe de app.py...")
import py_compile
try:
    py_compile.compile(os.path.join(BOT_DIR, 'mining_engine.py'), doraise=True)
    py_compile.compile(os.path.join(BOT_DIR, 'app.py'), doraise=True)
    print("  ✅ SYNTAX OK: mining_engine.py e app.py")
except py_compile.PyCompileError as e:
    print(f"  ❌ SYNTAX ERROR: {e}")

print("\n" + "=" * 55)
print("🏁 TESTE CONCLUÍDO!")
print("=" * 55)
