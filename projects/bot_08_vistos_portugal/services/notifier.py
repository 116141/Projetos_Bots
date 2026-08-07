from abc import ABC, abstractmethod

class INotifier(ABC):
    @abstractmethod
    async def send(self, title: str, message: str, attachment_path: str = None):
        pass

class ConsoleNotifier(INotifier):
    """Notificador para impressão de logs no console de testes."""
    async def send(self, title: str, message: str, attachment_path: str = None):
        print(f"[{title}] {message} | Anexo: {attachment_path or 'Nenhum'}")
