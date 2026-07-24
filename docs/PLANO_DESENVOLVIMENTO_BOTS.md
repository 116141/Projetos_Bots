# Plano de Desenvolvimento de Bots de Automação & Trading

Este documento centraliza as ideias, arquitetura, ferramentas e o roadmap de desenvolvimento de **Bots de Automação Financeira e Web** a partir de Cabo Verde.

---

## 1. Visão Geral das Estratégias

### A. Bot de Trading Algorítmico (Cripto / Forex / Índices)
* **Objetivo**: Executar estratégias automáticas de negociação (ex: *Grid Trading*, *Média Móvel Crossover*, *RSI Breakout*) 24/7 sem intervenção manual.
* **Tecnologias**: Python 3.11+, `CCXT` (API unificada de corretoras), `pandas` e `TA-Lib`.
* **Corretoras Suportadas**: Binance, Bybit, KuCoin, Deriv (para Índices Sintéticos).
* **Gestão de Risco**: Stop-loss automático, tamanho de posição fixo (1% a 2% do saldo por trade).

### B. Bot de Automação Web & Afiliados (Renda Passiva sem Risco de Capital)
* **Objetivo**: Capturar ofertas e promoções em tempo real na Amazon/AliExpress, gerar links de afiliados e publicar em grupos de Telegram / WhatsApp / X.
* **Tecnologias**: Python com `Playwright` / `Requests` / `BeautifulSoup4` + Telegram Bot API (`python-telegram-bot`).

### C. Bot de Automação de Mineração (Auto-Switching)
* **Objetivo**: Consultar APIs de rentabilidade em tempo real (NiceHash / HiveOS) e comutar automaticamente a mineração para o algoritmo mais lucrativo.

---

## 2. Operação a partir de Cabo Verde (Movimentação de Capital & P2P)

1. **Infraestrutura Cloud**: Servidor **VPS** (Hetzner, DigitalOcean ou Linode na Europa) custando entre 4€ a 6€/mês para manter o bot operando 24 horas por dia sem dependência da energia/internet residencial.
2. **Conta Payoneer Verificada (Trunfo Estratégico)**:
   * Possui contas bancárias virtuais em USD, EUR e GBP.
   * Permite receber ganhos de plataformas de afiliados (Amazon, eBay), serviços e brokers internacionais.
   * Possibilita transferência direta para banco local em Cabo Verde ou utilização do Cartão Mastercard Payoneer.
3. **Recebimento de Lucros em Cabo Verde (CVE)**:
   * **Mercado P2P (Binance / Bybit)**: Os lucros acumulados em USDT/BTC são convertidos via P2P diretamente para a conta bancária local em Cabo Verde (Caixa Económica, BCI, BAI, etc.) ou vinti4 em minutos.
   * **Cartão Payoneer / Cartões Globais**: Para depósitos, compras e levantamentos diretos.
3. **Segurança de API**:
   * As chaves de API da corretora devem ter a opção de **Levantamento/Withdraw DESATIVADA**.
   * Apenas permissões de **Leitura (Read)** e **Negociação (Spot Trade)** ativas.

---

## 3. Exemplo Prático Inicial (Python + CCXT)

Abaixo um script base demonstrativo de como o bot consulta saldos e preços em tempo real usando a biblioteca `CCXT`:

```python
import ccxt
import time

def inicializar_bot():
    # Conexão com a corretora (Ex: Binance Testnet / Demo)
    exchange = ccxt.binance({
        'apiKey': 'SUA_API_KEY_AQUI',
        'secret': 'SUA_SECRET_KEY_AQUI',
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    
    # Ativar modo Testnet/Sandbox se disponível
    exchange.set_sandbox_mode(True)
    return exchange

def monitorar_mercado(exchange, par="BTC/USDT"):
    try:
        ticker = exchange.fetch_ticker(par)
        preco_atual = ticker['last']
        print(f"[{time.strftime('%H:%M:%S')}] Preço atual de {par}: ${preco_atual:.2f}")
        return preco_atual
    except Exception as e:
        print(f"Erro ao obter preço: {e}")
        return None

if __name__ == "__main__":
    print("Iniciando Bot de Monitoramento...")
    bot = inicializar_bot()
    
    # Loop de monitoramento (exemplo: a cada 10 segundos)
    for _ in range(5):
        monitorar_mercado(bot, "BTC/USDT")
        time.sleep(10)
```

---

## 4. Estrutura do Diretório de Projetos

```text
Documents/Projetos_Bots/
├── docs/
│   └── PLANO_DESENVOLVIMENTO_BOTS.md   (Este documento)
└── projects/
    ├── bot_trading_crypto/              (Projeto de Trading Algorítmico)
    ├── bot_afiliados_telegram/          (Projeto de Automação de Ofertas)
    └── bot_mining_monitor/              (Projeto de Automação de Mineração)
```

---

## 5. Próximos Passos
1. Definir o primeiro projeto a implementar (ex: Bot de Trading Simulado em Python ou Bot de Ofertas Telegram).
2. Criar ambiente virtual Python (`venv`) e instalar dependências (`pip install ccxt pandas python-telegram-bot`).
3. Testar a estratégia em modo **Paper Trading / Demo** (dinheiro fictício).
