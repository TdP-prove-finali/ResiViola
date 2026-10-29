from dataclasses import dataclass


@dataclass
class Richiesta:
    id: int
    codice_scuola: str
    anno_corso: int
    sezione: str
    isee: float

    @property
    def chiave_classe(self):
        return self.codice_scuola, self.anno_corso, self.sezione

    def __eq__(self, other):
        return isinstance(other, Richiesta) and self.id == other.id

    def __hash__(self):
        return hash(self.id)
