from __future__ import annotations

from typing import Callable

Funcion = Callable[[int], float]

def primer_contraejemplo_cota_superior(f: Funcion, g: Funcion, c:float, n0: int, hasta: int) -> int | None:
    return next((n for n in range(n0, hasta + 1) if f(n) > c * g(n)), None)

def primer_contraejemplo_cota_inferior(f: Funcion, g: Funcion, c:float, n0: int, hasta: int) -> int | None:
    return next((n for n in range(n0, hasta + 1) if f(n) < c * g(n)), None)

def razones_en_potencias_de_2(f: Funcion, g: Funcion, hasta_exponente: int = 30) -> list[tuple[int, float]]:
    return [(2 ** k, f(2 ** k) / g(2**k)) for k in range(1, hasta_exponente + 1)]
