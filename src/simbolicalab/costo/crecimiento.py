from __future__ import annotations

import math
from typing import Callable, Sequence

Costo = Callable[[int], float]

COSTOS_CLASICOS: dict[str, Costo] = {
    "n": lambda n: n,
    "n log n": lambda n: n * math.log2(n),
    "n^2": lambda n: n ** 2,
    "n^3": lambda n: n ** 3,
    "2^n": lambda n: 2 ** n,

}

def mayor_n(costo: Costo, presupuesto: float) ->int:
    if costo(1) > presupuesto:
        return 0

    alto = 2
    while costo(alto) <= presupuesto:
        alto *= 2

    bajo = alto // 2

    while bajo + 1 < alto:
        medio = (bajo + alto) // 2

        if costo(medio) <= presupuesto:
            bajo = medio
        else:
            alto = medio

    return bajo

def tabla_hardware(costos: dict[str, Costo] = COSTOS_CLASICOS,ops_por_segundo: float = 1e9,
    segundos: float = 3600, factores: Sequence[int] = (1, 10, 1000)) -> dict[str, list[int]]:

    base = ops_por_segundo * segundos
    return {nombre : [mayor_n(f, base * k) for  k in factores] for nombre, f in costos.items()}

def pendientes(puntos: Sequence[tuple[float, float]]) -> list[float]:
    return [ (math.log(c2) - math.log(c1)) / (math.log(n2) - math.log(n1)) for (n1, c1), (n2, c2) in zip(puntos, puntos[1:])]

def razones(costos: Sequence[float]) -> list[float]:
    return [b / a for a, b in zip(costos, costos[1:])]

def razon_media(costos: Sequence[float]) -> float:
    if len(costos) < 2:
        raise ValueError("hacen falta al menos dos costos")
    return (costos[-1] / costos[0]) ** (1 / (len(costos) - 1))