from dataclasses import dataclass


@dataclass
class Scuola:
    codice_scuola: str
    denominazione: str
    tipologia: str

    def __eq__(self, other):
        return isinstance(other, Scuola) and self.codice_scuola == other.codice_scuola

    def __hash__(self):
        return hash(self.codice_scuola)

    def __str__(self):
        return f"{self.denominazione} ({self.codice_scuola})"
