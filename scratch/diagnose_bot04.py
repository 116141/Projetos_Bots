"""
Diagnóstico LOCAL completo do Bot 04 - AutoMine Profitability AI
Analisa todos os problemas de forma profunda.
"""
import os, sys, time, hmac, hashlib, json, uuid, requests
from datetime import datetime

NICEHASH_API_KEY    = "dd5a7aac-6583-4bbe-b259-96eac067ba36"
NICEHASH_SECRET     = "ad346d78-fece-470d-8019-dd61f9065ebb171cfdc1-8cf6-4cbb-832f-1ec927e8c4d3"
NICEHASH_ORG_ID     = "f7152d6f-290d-4132-81aa-1ae60b512ac9"
NICEHASH_HOST       = "https://api2.nicehash.com"

print("=" * 65)
print("🔬 DIAGNÓSTICO PROFUNDO BOT 04 - AutoMine Profitability AI")
print("=" * 65)

# ────────────────────────────────────────────────────────────────
# TESTE 1: Estrutura do motor (sem API externa)
# ────────────────────────────────────────────────────────────────
print("\n[1/6] 🧠 Análise da Lógica do Motor (mining_engine.py)...")

BOT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'projects', 'bot_04_mineracao_crypto'))
sys.path.insert(0, BOT_DIR)
os.chdir(BOT_DIR)

from mining_engine import AutoMineEngine
bot = AutoMineEngine()
time.sleep(1)

print(f"  ✅ Motor iniciado. is_running={bot.is_running}")
print(f"  ℹ️  Hashrate configurado: {bot.rig_hashrate_mhs} MH/s")
print(f"  ℹ️  Consumo:              {bot.power_consumption_watts} W")
print(f"  ℹ️  Custo eletricidade:   ${bot.electricity_cost_kwh}/kWh")
print(f"  ℹ️  Auto-switch:          {bot.auto_switch_enabled}")

# Calcular custo elétrico diário
daily_kwh = (bot.power_consumption_watts * 24.0) / 1000.0
daily_elec_cost = daily_kwh * bot.electricity_cost_kwh
print(f"\n  📊 CUSTO ELÉTRICO DIÁRIO: ${daily_elec_cost:.2f}")
print(f"  📊 Isso é: {bot.power_consumption_watts}W × 24h / 1000 × ${bot.electricity_cost_kwh}/kWh")

# Analisar rentabilidade de cada moeda
print("\n  📈 RENTABILIDADE SIMULADA POR MOEDA:")
for ticker, info in bot.coins_db.items():
    gross = info["base_reward_day"] * (bot.rig_hashrate_mhs / 250.0)
    net   = gross - daily_elec_cost
    status = "✅ LUCRATIVO" if net > 0 else "❌ PREJUÍZO"
    print(f"    {status} | {ticker}: Bruto=${gross:.2f}/dia | Elec=${daily_elec_cost:.2f}/dia | Líquido=${net:.2f}/dia")

time.sleep(2)
print(f"\n  📊 Total Minerado (2s): ${bot.total_mined_usd:.6f}")
print(f"  📊 Custo Elétrico (2s): ${bot.total_electricity_usd:.6f}")
print(f"  📊 Lucro Líquido (2s):  ${bot.net_profit_usd:.6f}")

# ────────────────────────────────────────────────────────────────
# TESTE 2: Verificar se NiceHash API está configurada
# ────────────────────────────────────────────────────────────────
print("\n[2/6] 🔑 Verificando Credenciais NiceHash...")
if NICEHASH_API_KEY and NICEHASH_SECRET and NICEHASH_ORG_ID:
    print(f"  ✅ NICEHASH_API_KEY:  {NICEHASH_API_KEY[:12]}...")
    print(f"  ✅ NICEHASH_SECRET:   {NICEHASH_SECRET[:12]}...")
    print(f"  ✅ NICEHASH_ORG_ID:   {NICEHASH_ORG_ID}")
else:
    print("  ❌ Credenciais NiceHash ausentes ou incompletas!")

# ────────────────────────────────────────────────────────────────
# TESTE 3: Testar conectividade com NiceHash API
# ────────────────────────────────────────────────────────────────
print("\n[3/6] 🌐 Testando Conexão com NiceHash API...")
def nicehash_request(method, path, body=None):
    ts = str(int(time.time() * 1000))
    nonce = str(uuid.uuid4())
    body_str = json.dumps(body) if body else ""
    msg = f"{NICEHASH_API_KEY}\x00{ts}\x00{nonce}\x00\x00{NICEHASH_ORG_ID}\x00\x00{method}\x00{path}\x00{body_str}"
    sig = hmac.new(NICEHASH_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
    headers = {
        "X-Time":      ts,
        "X-Nonce":     nonce,
        "X-Organization-Id": NICEHASH_ORG_ID,
        "X-Auth":      f"{NICEHASH_API_KEY}:{sig}",
        "Content-Type": "application/json"
    }
    url = NICEHASH_HOST + path
    if method == "GET":
        return requests.get(url, headers=headers, timeout=8)
    return requests.post(url, headers=headers, data=body_str, timeout=8)

# Testar time sync
try:
    r = requests.get(f"{NICEHASH_HOST}/api/v2/time", timeout=5)
    if r.status_code == 200:
        server_ts = r.json().get("serverTime", 0)
        local_ts  = int(time.time() * 1000)
        drift_ms  = abs(int(server_ts) - local_ts)
        print(f"  ✅ Servidor NiceHash online. Drift de relógio: {drift_ms}ms")
        if drift_ms > 5000:
            print(f"  ⚠️  DRIFT ALTO! Pode causar falhas de autenticação (max 5000ms)")
    else:
        print(f"  ❌ NiceHash time endpoint: HTTP {r.status_code}")
except Exception as e:
    print(f"  ❌ Erro de conexão NiceHash: {e}")

# ────────────────────────────────────────────────────────────────
# TESTE 4: Verificar saldo NiceHash (Wallet)
# ────────────────────────────────────────────────────────────────
print("\n[4/6] 💰 Verificando Saldo na Conta NiceHash...")
try:
    r = nicehash_request("GET", "/main/api/v2/accounting/accounts2")
    if r.status_code == 200:
        data = r.json()
        currencies = data.get("currencies", [])
        if currencies:
            print(f"  ✅ Conta NiceHash acessível! Moedas encontradas:")
            for c in currencies:
                total = float(c.get("totalBalance", 0))
                avail = float(c.get("available", 0))
                if total > 0 or avail > 0:
                    print(f"     - {c['currency']}: Total={total:.8f} | Disponível={avail:.8f}")
            if not any(float(c.get("totalBalance",0)) > 0 for c in currencies):
                print("  ⚠️  Todas as moedas com saldo ZERO!")
        else:
            print(f"  ⚠️  Resposta sem moedas: {data}")
    elif r.status_code == 401:
        print(f"  ❌ AUTENTICAÇÃO FALHOU! Verifique as chaves API NiceHash.")
        print(f"     Resposta: {r.text[:300]}")
    else:
        print(f"  ❌ HTTP {r.status_code}: {r.text[:300]}")
except Exception as e:
    print(f"  ❌ Erro: {e}")

# ────────────────────────────────────────────────────────────────
# TESTE 5: Verificar rigs de mineração ativos
# ────────────────────────────────────────────────────────────────
print("\n[5/6] ⚙️  Verificando Rigs de Mineração na NiceHash...")
try:
    r = nicehash_request("GET", f"/main/api/v2/mining/rigs2")
    if r.status_code == 200:
        data = r.json()
        rigs = data.get("miningRigs", [])
        total_rigs = data.get("totalRigs", 0)
        print(f"  ℹ️  Total de Rigs: {total_rigs}")
        if rigs:
            for rig in rigs:
                name   = rig.get("rigId", "?")
                status = rig.get("minerStatus", "UNKNOWN")
                nh_alg = rig.get("profitability", 0)
                print(f"     Rig: {name} | Status: {status} | Rentabilidade: ${nh_alg:.6f}/dia")
        else:
            print("  ⚠️  NENHUM RIG encontrado na conta NiceHash!")
            print("  ℹ️  Isso significa que não há hardware físico de mineração conectado.")
    elif r.status_code == 401:
        print(f"  ❌ AUTENTICAÇÃO FALHOU para rigs! Resposta: {r.text[:200]}")
    else:
        print(f"  ❌ HTTP {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"  ❌ Erro: {e}")

# ────────────────────────────────────────────────────────────────
# TESTE 6: Verificar rentabilidade atual NiceHash por algoritmo
# ────────────────────────────────────────────────────────────────
print("\n[6/6] 📊 Rentabilidade Real por Algoritmo na NiceHash...")
try:
    r = requests.get(f"{NICEHASH_HOST}/api/v2/mining/algorithms", timeout=5)
    if r.status_code == 200:
        algos = r.json().get("miningAlgorithms", [])
        target_algos = {"KHEAVYHASH", "ETCHASH", "KAWPOW", "SHA256", "RANDOMXMONERO"}
        for a in algos:
            if a.get("algorithm","").upper() in target_algos:
                pay = float(a.get("paying", 0))
                print(f"  📈 {a['algorithm']}: ${pay:.6f} BTC/TH/dia")
    else:
        print(f"  ❌ HTTP {r.status_code}")
except Exception as e:
    print(f"  ❌ Erro: {e}")

print("\n" + "=" * 65)
print("🏁 DIAGNÓSTICO COMPLETO!")
print("=" * 65)
