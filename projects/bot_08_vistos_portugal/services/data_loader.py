import csv
import json
import logging
from typing import List

from models.account import Account
from models.applicant import Applicant

logger = logging.getLogger(__name__)


def load_applicants(filepath: str) -> List[Applicant]:
    """Carrega a lista de requerentes a partir de um CSV.

    Colunas esperadas: nome, passaporte, data_nascimento, email, telefone
    """
    applicants = []
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = (row.get("nome") or row.get("name") or "").strip()
                if not name:
                    continue
                applicants.append(Applicant(
                    name=name,
                    passport=(row.get("passaporte") or row.get("passport") or "").strip(),
                    birth_date=(row.get("data_nascimento") or row.get("birth_date") or "").strip(),
                    email=(row.get("email") or "").strip(),
                    phone=(row.get("telefone") or row.get("phone") or "").strip(),
                ))
        logger.info("Carregados %d requerentes de %s", len(applicants), filepath)
    except FileNotFoundError:
        logger.warning("Arquivo de requerentes não encontrado: %s", filepath)
    except Exception as e:
        logger.error("Erro ao carregar requerentes: %s", e)
    return applicants


def load_accounts(filepath: str) -> List[Account]:
    """Carrega a lista de contas a partir de um arquivo JSON.

    Formato esperado:
    [
        {"email": "...", "senha": "...", "usada": false, "data_agendamento": null},
        ...
    ]
    """
    accounts = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            email = (item.get("email") or "").strip()
            secret = (item.get("senha") or item.get("password") or item.get("secret") or "").strip()
            if not email or not secret:
                continue
            acc = Account(email=email, secret=secret)
            # Restaurar estado de bloqueio persistido
            used = item.get("usada", False)
            scheduled_date = item.get("data_agendamento")
            if used and scheduled_date:
                from datetime import datetime
                try:
                    acc.lock_until(datetime.fromisoformat(scheduled_date))
                except ValueError:
