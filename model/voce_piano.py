from dataclasses import dataclass, field

from model.libro import Libro


@dataclass
class VocePiano:
    libro: Libro
    copie_usate: int = 0
    copie_nuove: int = 0
    costo: float = 0.0
    classi: set[str] = field(default_factory=set)

    @property
    def copie(self):
        return self.copie_usate + self.copie_nuove

    def __eq__(self, other):
        return isinstance(other, VocePiano) and self.libro == other.libro

    def __hash__(self):
        return hash(self.libro)
