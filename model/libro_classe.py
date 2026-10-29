from dataclasses import dataclass


@dataclass
class LibroClasse:
    codice_scuola: str
    anno_corso: int
    sezione: str
    isbn: str
    prezzo: float

    def __post_init__(self):
        self.prezzo = float(self.prezzo)

    @property
    def chiave_classe(self):
        return self.codice_scuola, self.anno_corso, self.sezione

    def __eq__(self, other):
        return (isinstance(other, LibroClasse)
                and (self.chiave_classe, self.isbn) == (other.chiave_classe, other.isbn))

    def __hash__(self):
        return hash((self.chiave_classe, self.isbn))
