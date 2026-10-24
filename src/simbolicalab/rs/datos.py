from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterator

@dataclass(frozen=True)
class Datos:
    xs: tuple[float, ...]
    ys: tuple[float, ...]

    nombre_x : str = "x"
    nombre: str = "sin nombre"
    ley_oculta: str | None = None

    def __post_init__(self) -> None:
        if len(self.xs) != len(self.ys):
            raise ValueError("xs e ys deben tener la misma longitud")
        if len(self.xs) == 0:
            raise ValueError("el conjunto de datos no puede estar vacío")
        if not all(math.isfinite(v) for v in (*self.xs, *self.ys)):
            raise ValueError("los datos deben ser números finitos") 

    def __len__(self) -> int:
        return len(self.xs)

    def __iter__(self) -> Iterator[tuple[float, float]]:
        return zip(self.xs, self.ys)