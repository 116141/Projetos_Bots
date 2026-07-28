import os
import sys
import time

BOT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'projects', 'bot_04_mineracao_crypto'))
sys.path.insert(0, BOT_DIR)
os.chdir(BOT_DIR)

from staking_engine import YieldEngine

def main():
    print("==================================================")
    print("🌾 TESTE LOCAL - BOT 04 (YIELD PRO AI)")
    print("==================================================")
    
    bot = YieldEngine()
    print("[*] A conectar aos oráculos DeFi e Plataformas (Bybit/Binance)...")
    
    # Aguardar que a thread de background atualize a API
    time.sleep(4)
    
    status = bot.get_status()
    
    if len(status['opportunities']) > 0:
        print("[+] Oportunidades de Yield carregadas com sucesso!")
        print(f"\n    💰 Saldo Simulado: ${status['user_balance']:,.2f} {status['active_coin']}")
        print(f"    🚀 Melhor APY Encontrado: {status['best_apy']}%")
        print(f"    💵 Estimativa Mensal Máxima: ${status['best_monthly_usd']:.4f}")
        
        print("\n    TOP 3 OPÇÕES NO MERCADO AGORA:")
        for i, opp in enumerate(status['opportunities'][:3]):
            print(f"      {i+1}. {opp['platform']} ({opp['type']}) -> {opp['apy']}% APY | Risco: {opp['risk']}")
            
        print("==================================================")
        print("✅ Bot 04 Teste Concluído - Motor saudável!")
    else:
        print("[-] Erro: Falha ao carregar APYs. (Sem internet ou API offline)")
        
    bot.stop()

if __name__ == "__main__":
    main()
