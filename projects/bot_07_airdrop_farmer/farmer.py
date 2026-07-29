import os
import json
import time
import threading
from web3 import Web3
from eth_account import Account

# Ativa as funcionalidades experimentais para criar carteiras locais
Account.enable_unaudited_hdwallet_features()

class AirdropFarmerEngine:
    def __init__(self):
        self.base_dir = os.path.dirname(__file__)
        self.wallets_file = os.path.join(self.base_dir, 'wallets', 'keys.json')
        self.config_file = os.path.join(self.base_dir, 'config.json')
        
        # Testnet RPCs (Sepolia é a mais usada para farmar airdrops iniciais)
        self.rpc_urls = {
            "sepolia": "https://ethereum-sepolia-rpc.publicnode.com",
            "base_sepolia": "https://sepolia.base.org"
        }
        
        self.active_network = "sepolia"
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_urls[self.active_network]))
        
        self.wallets = []
        self.is_farming = False
        self.logs = []
        
        self._lock = threading.Lock()
        self._load_wallets()
        
        # O Thread principal que vai farmar (simular transações)
        self._farmer_thread = None

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        with self._lock:
            self.logs.insert(0, formatted)
            if len(self.logs) > 50:
                self.logs.pop()
        print(formatted)

    def _load_wallets(self):
        if os.path.exists(self.wallets_file):
            try:
                with open(self.wallets_file, 'r', encoding='utf-8') as f:
                    self.wallets = json.load(f)
            except Exception as e:
                self.log(f"Erro ao carregar carteiras: {e}")
        else:
            self.wallets = []

    def _save_wallets(self):
        os.makedirs(os.path.dirname(self.wallets_file), exist_ok=True)
        with open(self.wallets_file, 'w', encoding='utf-8') as f:
            json.dump(self.wallets, f, indent=2)

    def generate_wallets(self, count=3):
        """Gera novas carteiras Ethereum e guarda as chaves privadas com segurança"""
        new_wallets = []
        for _ in range(count):
            account = Account.create()
            wallet_data = {
                "address": account.address,
                "private_key": account.key.hex(),
                "total_txs": 0
            }
            new_wallets.append(wallet_data)
            
        with self._lock:
            self.wallets.extend(new_wallets)
            self._save_wallets()
            
        self.log(f"Geradas {count} novas carteiras (Burner Wallets).")
        return new_wallets

    def get_balances(self):
        """Lê o saldo de todas as carteiras na rede ativa"""
        results = []
        for w in self.wallets:
            try:
                # Verifica saldo
                balance_wei = self.web3.eth.get_balance(w["address"])
                balance_eth = self.web3.from_wei(balance_wei, 'ether')
                results.append({
                    "address": w["address"],
                    "balance": round(float(balance_eth), 4),
                    "txs": w.get("total_txs", 0)
                })
            except Exception as e:
                results.append({
                    "address": w["address"],
                    "balance": 0.0,
                    "txs": w.get("total_txs", 0)
                })
        return results

    def _farm_loop(self):
        self.log("🚀 Motor de Airdrop Farming iniciado.")
        
        while self.is_farming:
            with self._lock:
                wallets_to_farm = list(self.wallets)
            
            if not wallets_to_farm:
                self.log("Nenhuma carteira encontrada. Gera carteiras primeiro!")
                self.stop_farming()
                break

            for w in wallets_to_farm:
                if not self.is_farming:
                    break
                    
                address = w["address"]
                pk = w["private_key"]
                
                try:
                    balance_wei = self.web3.eth.get_balance(address)
                    balance_eth = float(self.web3.from_wei(balance_wei, 'ether'))
                    
                    if balance_eth < 0.001:
                        self.log(f"[{address[:6]}...] Saldo insuficiente ({balance_eth} ETH). Precisa de ir ao Faucet.")
                        time.sleep(2)
                        continue
                        
                    # Simular Volume On-Chain: Enviar uma fração de volta para si mesmo (Self-Transfer)
                    # Isto gasta gás (na testnet) mas gera 1 transação no histórico
                    self.log(f"[{address[:6]}...] A preparar transação para gerar volume on-chain...")
                    
                    nonce = self.web3.eth.get_transaction_count(address)
                    tx = {
                        'nonce': nonce,
                        'to': address, # Envia para ele próprio
                        'value': self.web3.to_wei(0.0001, 'ether'),
                        'gas': 21000,
                        'gasPrice': self.web3.eth.gas_price,
                        'chainId': self.web3.eth.chain_id
                    }
                    
                    signed_tx = self.web3.eth.account.sign_transaction(tx, pk)
                    tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    
                    self.log(f"✅ Transação executada! Hash: {self.web3.to_hex(tx_hash)[:10]}...")
                    
                    # Atualizar contador local
                    w["total_txs"] = w.get("total_txs", 0) + 1
                    self._save_wallets()
                    
                    # Espera aleatória entre transações para não parecer um bot tão óbvio
                    time.sleep(15)
                    
                except Exception as e:
                    self.log(f"[{address[:6]}...] Erro na transação: {str(e)[:50]}")
                    time.sleep(5)
            
            # Depois de correr todas as carteiras, espera 1 minuto antes do próximo ciclo
            if self.is_farming:
                self.log("Ciclo completo. A aguardar 60 segundos...")
                time.sleep(60)
                
        self.log("🛑 Motor de Airdrop Farming parado.")

    def start_farming(self):
        if not self.is_farming:
            self.is_farming = True
            self._farmer_thread = threading.Thread(target=self._farm_loop, daemon=True)
            self._farmer_thread.start()

    def stop_farming(self):
        self.is_farming = False

    def get_status(self):
        with self._lock:
            return {
                "is_farming": self.is_farming,
                "network": self.active_network,
                "wallets": self.get_balances(),
                "logs": self.logs
            }

if __name__ == "__main__":
    farmer = AirdropFarmerEngine()
    if len(farmer.wallets) == 0:
        farmer.generate_wallets(2)
    print(farmer.get_balances())
