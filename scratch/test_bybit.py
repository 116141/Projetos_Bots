import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("BYBIT_API_KEY", "")
api_secret = os.getenv("BYBIT_API_SECRET", "")

if not api_key or not api_secret:
    print("ERRO: As chaves BYBIT_API_KEY e BYBIT_API_SECRET não foram encontradas.")
    print("Por favor, cria um ficheiro .env na pasta raiz do teu projeto com estas variáveis.")
    exit(1)

try:
    print("A ligar à Bybit...")
    exchange = ccxt.bybit({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    
    # Testar ligação pedindo o saldo
    balance = exchange.fetch_balance()
    
    usdt = balance.get('USDT', {}).get('free', 0.0)
    btc = balance.get('BTC', {}).get('free', 0.0)
    
    print("\n✅ LIGAÇÃO BEM SUCEDIDA À TUA CONTA BYBIT!")
    print("-" * 40)
    print(f"💰 Saldo Disponível (USDT): ${usdt:.2f}")
    print(f"💰 Saldo Disponível (BTC) : ₿{btc:.6f}")
    print("-" * 40)
    print("O Bot 01 está pronto para arrancar e usar estes fundos reais.")
    
except Exception as e:
    print(f"\n❌ FALHA NA LIGAÇÃO: {e}")
    print("Verifica se as tuas chaves estão corretas e se tens permissões de 'Leitura e Negociação' na API.")
