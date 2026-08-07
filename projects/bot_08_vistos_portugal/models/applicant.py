class Applicant:
    """Modelo representando os dados de um requerente no ambiente de teste."""
    def __init__(self, name: str, passport: str, birth_date: str, email: str, phone: str):
        self.name = name
        self.passport = passport
        self.birth_date = birth_date
        self.email = email
        self.phone = phone
        self.is_scheduled = False

    def mark_as_scheduled(self):
        self.is_scheduled = True
