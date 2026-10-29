from dataclasses import dataclass


@dataclass
class ClasseIsee:
    id: int
    descrizione: str
    limite_inf: float
    limite_sup: float | None
    nuclei_con_minori: int
    nuclei_senza_minori: int

    def __post_init__(self):
        self.limite_inf = float(self.limite_inf)
        self.limite_sup = float(self.limite_sup) if self.limite_sup is not None else None

    def __eq__(self, other):
        return isinstance(other, ClasseIsee) and self.id == other.id

    def __hash__(self):
        return hash(self.id)
