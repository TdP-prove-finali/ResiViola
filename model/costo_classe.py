from dataclasses import dataclass


@dataclass
class CostoClasse:
    codice_scuola: str
    anno_corso: int
    sezione: str
    num_libri: int
    costo_studente: float
    num_studenti: int = 0
    stima_cittadina: bool = False

    def __post_init__(self):
        self.costo_studente = float(self.costo_studente or 0)

    @property
    def costo_classe(self):
        return self.costo_studente * self.num_studenti

    def __eq__(self, other):
        return (isinstance(other, CostoClasse)
                and (self.codice_scuola, self.anno_corso, self.sezione)
                == (other.codice_scuola, other.anno_corso, other.sezione))

    def __hash__(self):
        return hash((self.codice_scuola, self.anno_corso, self.sezione))

    def __str__(self):
        nota = " (stima media cittadina)" if self.stima_cittadina else ""
        return (f"Classe {self.anno_corso}{self.sezione}: {self.num_libri} libri, "
                f"{self.costo_studente:.2f} € per studente × {self.num_studenti} studenti{nota} "
                f"= {self.costo_classe:.2f} €")
