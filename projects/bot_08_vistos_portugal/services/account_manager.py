import asyncio
from typing import List, Optional
from models.account import Account

class AccountManager:
    """Gerenciador seguro para alocação e ciclo de bloqueio de contas de teste."""
    def __init__(self, accounts: List[Account]):
        self._accounts = accounts
        self._lock = asyncio.Lock()

    async def get_available_account(self) -> Optional[Account]:
        async with self._lock:
            for acc in self._accounts:
                if acc.check_availability():
                    return acc
            return None
