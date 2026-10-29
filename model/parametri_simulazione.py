from dataclasses import dataclass, field

from model.parametri_piano import ParametriPiano


@dataclass
class ParametriSimulazione:
    piano: ParametriPiano = field(default_factory=ParametriPiano)
    anni: int = 5
    budget_annuo: float = 5000.0
    p_danno: float = 0.10
    p_perdita: float = 0.03
    p_cambio: float = 0.134
