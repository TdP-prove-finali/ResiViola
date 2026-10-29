from dataclasses import dataclass
from datetime import datetime


@dataclass
class Scenario:
    id: int
    nome: str
    codice_scuola: str
    creato: datetime
    budget: float
    budget_annuo: float
    quota_richiedenti: float
    soglia_isee: float
    prezzo_usato: float
    usato_disponibile: float
    p_danno: float
    p_perdita: float
    p_cambio: float
    anni: int

    def __eq__(self, other):
        return isinstance(other, Scenario) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return f"{self.nome} ({self.creato:%d/%m %H:%M})"
