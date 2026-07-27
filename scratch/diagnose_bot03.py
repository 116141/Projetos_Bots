"""
Diagnóstico LOCAL completo do Bot 03 ArbitragePro AI
Roda localmente para testar todos os componentes antes do deploy no Render.
"""
import os
import sys
import json
import time
import hmac
import hashlib
import requests

# Carregar credenciais do config.json local
CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'projects', 'bot_03_arbitragem_crypto', 'config.json')
config = {}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

BYBIT_API_KEY    = os.environ.get('BYBIT_API_KEY', config.get('bybit_api_key', ''))
BYBIT_SECRET_KEY = os.environ.get('BYBIT_SECRET_KEY', config.get('bybit_secret_key', ''))
SYMBOL = 'BTC/USDT'
SYMBOL_FMT = 'BTCUSDT'

print("=" * 60)
print("🔬 DIAGNÓSTICO LOCAL DO BOT 03 - ArbitragePro AI")
print("=" * 60)

# ─── TESTE 1: API Keys ──────────────────────────────────────────
print("\n[1/5] 🔑 Verificando Chaves API da Bybit...")
if BYBIT_API_KEY and BYBIT_SECRET_KEY:
    print(f"  ✅ BYBIT_API_KEY encontrada: {BYBIT_API_KEY[:8]}...")
    print(f"  ✅ BYBIT_SECRET_KEY encontrada: {BYBIT_SECRET_KEY[:6]}...")
else:
    print("  ❌ CHAVES NÃO ENCONTRADAS! Verifique as variáveis de ambiente ou config.json")
    sys.exit(1)

# ─── TESTE 2: Preços Reais de Cada Corretora ──────────────────────
print("\n[2/5] 📊 Buscando Preços Reais de Cada Corretora...")
prices = {}

# Binance
try:
    r = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL_FMT}", timeout=4)
    if r.status_code == 200:
        prices["Binance"] = float(r.json()["price"])
        print(f"  ✅ Binance:  ${prices['Binance']:,.2f}")
    else:
        print(f"  ❌ Binance: HTTP {r.status_code}")
except Exception as e:
    print(f"  ❌ Binance Erro: {e}")

# Bybit
try:
    r = requests.get(f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={SYMBOL_FMT}", timeout=4)
    if r.status_code == 200:
        lst = r.json().get("result", {}).get("list", [])
        if lst:
            prices["Bybit"] = float(lst[0]["lastPrice"])
            print(f"  ✅ Bybit:    ${prices['Bybit']:,.2f}")
    else:
        print(f"  ❌ Bybit: HTTP {r.status_code}")
except Exception as e:
    print(f"  ❌ Bybit Erro: {e}")

# KuCoin
try:
    r = requests.get("https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=BTC-USDT", timeout=4)
    if r.status_code == 200:
        data = r.json().get("data", {})
        if data and data.get("price"):
            prices["KuCoin"] = float(data["price"])
            print(f"  ✅ KuCoin:  ${prices['KuCoin']:,.2f}")
    else:
        print(f"  ❌ KuCoin: HTTP {r.status_code}")
except Exception as e:
    print(f"  ❌ KuCoin Erro: {e}")

# Kraken
try:
    r = requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSDT", timeout=4)
    if r.status_code == 200:
        result = r.json().get("result", {})
        if result:
            ticker = list(result.values())[0]
            prices["Kraken"] = float(ticker["c"][0])
            print(f"  ✅ Kraken:  ${prices['Kraken']:,.2f}")
    else:
        print(f"  ❌ Kraken: HTTP {r.status_code}")
except Exception as e:
    print(f"  ❌ Kraken Erro: {e}")

# Gate.io
try:
    r = requests.get("https://api.gateio.ws/api/v4/spot/tickers?currency_pair=BTC_USDT", timeout=4)
    if r.status_code == 200:
        lst = r.json()
        if lst:
            prices["Gate.io"] = float(lst[0]["last"])
            print(f"  ✅ Gate.io: ${prices['Gate.io']:,.2f}")
    else:
        print(f"  ❌ Gate.io: HTTP {r.status_code}")
except Exception as e:
    print(f"  ❌ Gate.io Erro: {e}")

# ─── TESTE 3: Análise de Spreads Reais ──────────────────────────
print("\n[3/5] 📈 Analisando Spreads Entre Corretoras...")
bybit_price = prices.get("Bybit")
if not bybit_price:
    print("  ❌ Preço da Bybit não disponível. Verificar conectividade.")
else:
    best_spread = 0
    best_pair = None
    for ex, price in prices.items():
        if ex == "Bybit":
            continue
        if bybit_price < price:
            raw = ((price - bybit_price) / bybit_price) * 100
            net = raw - 0.2
            direction = f"COMPRAR na Bybit, VENDER em {ex}"
        else:
            raw = ((bybit_price - price) / price) * 100
            net = raw - 0.2
            direction = f"COMPRAR em {ex}, VENDER na Bybit"
        status = "✅ DISPARA" if net >= 0.15 else ("⚠️ Perto" if net >= 0 else "❌ Negativo")
        print(f"  {status} | Bybit vs {ex}: Bruto={raw:.3f}% | Líquido={net:.3f}% | {direction}")
        if net > best_spread:
            best_spread = net
            best_pair = (ex, direction)
    if best_spread > 0:
        print(f"\n  🏆 MELHOR SPREAD: {best_spread:.3f}% líquido com {best_pair[1]}")

# ─── TESTE 4: Saldo Real na Bybit ───────────────────────────────
print("\n[4/5] 💰 Verificando Saldo Real na Bybit...")
try:
    recv_window = "5000"
    timestamp = str(int(time.time() * 1000))
    param_str = timestamp + BYBIT_API_KEY + recv_window + "accountType=UNIFIED"
    signature = hmac.new(BYBIT_SECRET_KEY.encode(), param_str.encode(), hashlib.sha256).hexdigest()
    headers = {
        "X-BAPI-API-KEY": BYBIT_API_KEY,
        "X-BAPI-SIGN": signature,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": recv_window
    }
    r = requests.get("https://api.bybit.com/v5/account/wallet-balance?accountType=UNIFIED", headers=headers, timeout=5)
    if r.status_code == 200:
        data = r.json()
        if data.get("retCode") == 0:
            list_data = data.get("result", {}).get("list", [])
            if list_data:
                total_eq = float(list_data[0].get("totalEquity", 0))
                print(f"  ✅ Saldo Bybit: ${total_eq:.2f} USD")
                if total_eq < 5:
                    print(f"  ⚠️  Saldo abaixo do mínimo da Bybit ($5 USDT). Bot pode não conseguir executar ordens!")
            for coin in list_data[0].get("coin", []) if list_data else []:
                if float(coin.get("walletBalance", 0)) > 0:
                    print(f"     - {coin['coin']}: {float(coin['walletBalance']):.6f}")
        else:
            print(f"  ❌ Bybit retCode: {data.get('retCode')} - {data.get('retMsg')}")
    else:
        print(f"  ❌ HTTP {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"  ❌ Erro: {e}")

# ─── TESTE 5: Simular Ordem de Compra (Dry Run) ─────────────────
print("\n[5/5] 🧪 Testando Execução de Ordem (Simulação sem enviar)...")
try:
    trade_amount = float(config.get('trade_amount', 9.0))
    bybit_price_now = prices.get("Bybit", 65000)
    body_buy = {
        "category": "spot",
        "symbol": SYMBOL_FMT,
        "side": "Buy",
        "orderType": "Market",
        "qty": str(round(trade_amount, 2))
    }
    body_sell = {
        "category": "spot",
        "symbol": SYMBOL_FMT,
        "side": "Sell",
        "orderType": "Market",
        "qty": f"{(trade_amount / bybit_price_now):.8f}"
    }
    print(f"  ✅ Payload BUY válido:  {json.dumps(body_buy)}")
    print(f"  ✅ Payload SELL válido: {json.dumps(body_sell)}")
    print(f"  ✅ Trade Amount: ${trade_amount} | Qty BTC Venda: {(trade_amount / bybit_price_now):.8f} BTC")
except Exception as e:
    print(f"  ❌ Erro no payload: {e}")

print("\n" + "=" * 60)
print("🏁 DIAGNÓSTICO CONCLUÍDO")
print("=" * 60)
