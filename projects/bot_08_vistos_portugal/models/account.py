from datetime import datetime
from enum import Enum

class AccountStatus(Enum):
    AVAILABLE = "available"
    LOCKED = "locked"
    COOLDOWN = "cooldown"

class Account:
    """Modelo de dados para representar uma conta de teste e seu estado."""
    def __init__(self, email: str, secret: str):
        self.email = email
        self.secret = secret
        self.status = AccountStatus.AVAILABLE
        self.locked_until: datetime | None = None

    def lock_until(self, unlock_date: datetime):
        """Define o bloqueio da conta até uma data específica."""
        self.status = AccountStatus.LOCKED
        self.locked_until = unlock_date

    def check_availability(self) -> bool:
        """Verifica e atualiza o estado de disponibilidade da conta."""
        if self.status == AccountStatus.LOCKED and self.locked_until:
            if datetime.now() >= self.locked_until:
                self.status = AccountStatus.AVAILABLE
                self.locked_until = None
        return self.status == AccountStatus.AVAILABLE
