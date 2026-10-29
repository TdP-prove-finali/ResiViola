from dataclasses import dataclass


@dataclass
class Libro:
    isbn: str
    titolo: str
    disciplina: str
    editore: str
    prezzo: float

    def __post_init__(self):
        self.prezzo = float(self.prezzo)

    def __eq__(self, other):
        return isinstance(other, Libro) and self.isbn == other.isbn

    def __hash__(self):
        return hash(self.isbn)

    def __str__(self):
        return f"{self.titolo} ({self.editore}) — {self.prezzo:.2f} €"
