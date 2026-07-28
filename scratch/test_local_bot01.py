import os
import sys
import time

BOT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'projects', 'bot_01_trading_crypto'))
sys.path.insert(0, BOT_DIR)
os.chdir(BOT_DIR)

from bot_engine import TradingBotEngine

def main():
    print("==================================================")
    print("🤖 TESTE LOCAL - BOT 01 (TRADING PROFISSIONAL)")
    print("==================================================")
    
    bot = TradingBotEngine()
    
    print(f"[*] A carregar Klines (Velas 5m) para {bot.symbol} da Binance...")
    # Aguardar que o bot faça a primeira busca na thread em background
    time.sleep(3)
    
    status = bot.get_status()
    
    if len(status['price_history']) > 0:
        print("[+] Dados de mercado carregados com sucesso!")
        print(f"    - Preço Atual: ${status['current_price']:,.2f}")
        print(f"    - Velas Analisadas: {len(status['price_history'])}")
        print(f"    - SMA Fast (7): ${status['sma_fast']:,.2f}")
        print(f"    - SMA Slow (25): ${status['sma_slow']:,.2f}")
        print(f"    - RSI: {status['rsi']:.2f}")
        
        print("\n[*] Lógica de Taxas (Simulação):")
        if status['sma_fast'] > status['sma_slow']:
            print("    -> Tendência de Curto Prazo é de ALTA (BULLISH).")
        else:
            print("    -> Tendência de Curto Prazo é de QUEDA (BEARISH). O bot aguarda cruzamento dourado.")
            
        print("\n[+] Status Financeiro:")
        print(f"    - Saldo USDT: ${status['usdt_balance']:,.2f}")
        print(f"    - PnL Líquido: ${status['net_pnl']:,.2f} ({status['net_pnl_pct']:.2f}%)")
        print("==================================================")
        print("✅ Bot 01 Teste Concluído - Motor saudável!")
    else:
        print("[-] Erro: Falha ao carregar Klines da Binance. (Sem internet?)")
        
    bot.stop()

if __name__ == "__main__":
    main()
