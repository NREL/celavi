from dataclasses import dataclass, field

from .unique_identifier import UniqueIdentifier


@dataclass
class Component:
    type: str
    xlong: float
    ylat: float
    year: float
    id: int = field(default_factory=UniqueIdentifier.unique_identifier)
