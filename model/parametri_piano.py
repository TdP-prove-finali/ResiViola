from dataclasses import dataclass


@dataclass
class ParametriPiano:
    budget: float = 20000.0
    quota_richiedenti: float = 0.6
    soglia_isee: float = 15748.78
    prezzo_usato: float = 0.5
    usato_disponibile: float = 0.3
    seme: int = 42
