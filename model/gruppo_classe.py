from dataclasses import dataclass


@dataclass
class GruppoClasse:
    codice_scuola: str
    anno_corso: int
    sezione: str
    studenti: int
    costo: float
    isbn: list[str]

    @property
    def nome_classe(self):
        return f"{self.anno_corso}{self.sezione}"

    def __eq__(self, other):
        return (isinstance(other, GruppoClasse)
                and (self.codice_scuola, self.anno_corso, self.sezione)
                == (other.codice_scuola, other.anno_corso, other.sezione))

    def __hash__(self):
        return hash((self.codice_scuola, self.anno_corso, self.sezione))
