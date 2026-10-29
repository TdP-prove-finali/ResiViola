from dataclasses import dataclass, field


@dataclass
class StatisticaAnno:
    anno: int
    valori: dict[str, float] = field(default_factory=dict)
