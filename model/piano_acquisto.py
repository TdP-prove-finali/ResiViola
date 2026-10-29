from dataclasses import dataclass, field

from model.gruppo_classe import GruppoClasse
from model.voce_piano import VocePiano


@dataclass
class PianoAcquisto:
    metodo: str
    budget: float
    richiedenti: int = 0
    aventi_diritto: int = 0
    gruppi_serviti: list[GruppoClasse] = field(default_factory=list)
    voci: list[VocePiano] = field(default_factory=list)
    nodi_visitati: int = 0
    tempo_s: float = 0.0

    @property
    def studenti_serviti(self):
        return sum(g.studenti for g in self.gruppi_serviti)

    @property
    def pct_soddisfatte(self):
        return 100 * self.studenti_serviti / self.aventi_diritto if self.aventi_diritto else 0.0

    @property
    def costo_totale(self):
        return sum(g.costo for g in self.gruppi_serviti)

    @property
    def copie_usate(self):
        return sum(v.copie_usate for v in self.voci)

    @property
    def copie_nuove(self):
        return sum(v.copie_nuove for v in self.voci)
