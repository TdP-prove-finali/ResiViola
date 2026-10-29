from dataclasses import dataclass, field

from model.libro import Libro


@dataclass
class Trasferimento:
    da: str
    a: str
    libro: Libro
    copie: int
    km: float


@dataclass
class PianoTrasferimenti:
    trasferimenti: list[Trasferimento] = field(default_factory=list)
    eccedenze: int = 0
    carenze: int = 0
    copie_ricevute: int = 0
    risparmio: float = 0.0
    tempo_s: float = 0.0

    @property
    def copie_km(self):
        return sum(t.copie * t.km for t in self.trasferimenti)

    @property
    def viaggi(self):
        return {(t.da, t.a) for t in self.trasferimenti}
