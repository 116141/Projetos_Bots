# 🚀 Guia Completo de Deploy: Render & Vercel

Este guia descreve o passo a passo para colocar o **Central Hub Portal** e os **5 Bots de Automação & Trading** online utilizando **Render** (recomendado para os bots 24/7) e **Vercel** (opcional para a interface Hub).

---

## 🟢 Opção 1: Deploy Automático no Render (Recomendado)

O Render permite colocar todos os serviços no ar através do ficheiro Blueprint `render.yaml` existente na raiz do projeto.

### Passo a Passo no Render:
1. Acesse [render.com](https://render.com) e faça Login (ou crie conta com a sua conta GitHub).
2. Clique no botão **New +** e selecione **Blueprint**.
3. Conecte o repositório GitHub: `116141/Projetos_Bots`.
4. O Render detectará automaticamente o ficheiro [`render.yaml`](file:///c:/Users/Uni-CvFCT-EdmilsonGi/Documents/Projetos_Bots/render.yaml) e listará os 6 serviços:
   - `bot-00-hub-portal`
   - `bot-01-trading-crypto`
   - `bot-02-afiliados-telegram`
   - `bot-03-arbitragem-crypto`
   - `bot-04-mineracao-crypto`
   - `bot-05-sentimento-ia`
5. Clique em **Apply**. O Render fará a compilação (*build*) e deploy dos 6 serviços em segundo plano.

---

## ⚡ Conectar o Hub Portal aos Bots no Render

Depois de criar os serviços no Render, cada bot terá um URL único (ex: `https://bot-01-trading-crypto.onrender.com`).

No serviço `bot-00-hub-portal` no Render:
1. Vá às **Environment Variables** (Variáveis de Ambiente).
2. Adicione as seguintes chaves com os URLs fornecidos pelo Render:
   - `BOT_01_URL` = `https://bot-01-trading-crypto.onrender.com`
   - `BOT_02_URL` = `https://bot-02-afiliados-telegram.onrender.com`
   - `BOT_03_URL` = `https://bot-03-arbitragem-crypto.onrender.com`
   - `BOT_04_URL` = `https://bot-04-mineracao-crypto.onrender.com`
   - `BOT_05_URL` = `https://bot-05-sentimento-ia.onrender.com`

---

## 📐 Opção 2: Deploy no Vercel (Hub Portal ou Dashboards)

Se desejar publicar o **Hub Portal** ou qualquer Dashboard individual no **Vercel**:

1. Acesse [vercel.com](https://vercel.com) e clique em **Add New... -> Project**.
2. Importe o repositório `116141/Projetos_Bots`.
3. Na opção **Root Directory**, selecione a pasta do bot que quer publicar (ex: `projects/bot_00_hub_portal`).
4. Em **Environment Variables**, adicione as URLs públicas dos bots (como `BOT_01_URL`, etc.).
5. Clique em **Deploy**.

---

## 🛡️ Variáveis de Ambiente Recomendadas

| Bot | Variável | Descrição |
|---|---|---|
| **Bot 01 (Trading)** | `API_KEY` & `SECRET_KEY` | Chaves da corretora (Binance/Bybit) sem permissão de levantamento |
| **Bot 02 (Telegram)** | `TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHAT_ID` | Token do Bot Telegram e ID do canal |
| **Bot 00 (Hub)** | `BOT_01_URL` até `BOT_05_URL` | Endereços dos bots para monitoramento remoto |
