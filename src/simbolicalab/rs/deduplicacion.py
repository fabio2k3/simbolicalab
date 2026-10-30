from __future__ import annotations

import math
from itertools import product
from typing import Sequence

from ..nucleo.contador import Contador
from .expresion import Expr, evaluar

Firma = tuple[float, ...]
LIMITE_COCIENTE = 2.0 ** 50            


def firma(e: Expr, nombre_x: str, puntos: Sequence[float], contador: Contador | None = None) -> Firma | None:
    """Valores de la fórmula en los puntos dados, o None si alguno es NaN o infinito."""
    valores = tuple(evaluar(e, {nombre_x: x}, contador) for x in puntos)
    return valores if all(math.isfinite(v) for v in valores) else None


def _distancia2(f: Firma, g: Firma) -> float:
    return sum((a - b) * (a - b) for a, b in zip(f, g))


def _validar(firmas: Sequence[Firma | None], eps: float) -> None:
    if eps < 0 or not math.isfinite(eps):
        raise ValueError("eps debe ser finito y >= 0")
    ks = {len(f) for f in firmas if f is not None}
    if len(ks) > 1:
        raise ValueError("todas las firmas deben tener la misma dimensión")


def deduplicar_cuadratico(firmas: Sequence[Firma | None], eps: float, contador: Contador | None = None) -> list[int]:
    _validar(firmas, eps)
    c = contador if contador is not None else Contador()
    conservados: list[int] = []
    for i, f in enumerate(firmas):
        if f is None:
            continue
        for j in conservados:
            c.tick(1, "comparacion_firma")
            if _distancia2(f, firmas[j]) <= eps * eps:      
                break
        else:
            conservados.append(i)
    return conservados


def deduplicar_exacta(firmas: Sequence[Firma | None], contador: Contador | None = None) -> list[int]:
    _validar(firmas, 0.0)
    c = contador if contador is not None else Contador()
    vistas: set[Firma] = set()
    conservados: list[int] = []
    for i, f in enumerate(firmas):
        if f is None:
            continue
        c.tick(1, "acceso_hash")
        if f not in vistas:
            vistas.add(f)
            conservados.append(i)
    return conservados


def deduplicar_rejilla(firmas: Sequence[Firma | None], eps: float, contador: Contador | None = None, radio: int = 1,) -> list[int]:

    _validar(firmas, eps)
    if eps == 0:
        return deduplicar_exacta(firmas, contador)
    c = contador if contador is not None else Contador()

    rejilla: dict[tuple[int, ...], list[int]] = {}
    fuera: list[int] = []                     
    conservados: list[int] = []

    def en_rango(f: Firma) -> bool:
        return all(abs(v) / eps < LIMITE_COCIENTE for v in f)

    def cercano(f: Firma, j: int) -> bool:
        c.tick(1, "comparacion_firma")
        return _distancia2(f, firmas[j]) <= eps * eps       

    for i, f in enumerate(firmas):
        if f is None:
            continue
        if not en_rango(f):
            repetida = any(cercano(f, j) for j in conservados)
        else:
            celda = tuple(int(v // eps) for v in f)
            repetida = any(cercano(f, j) for j in fuera)      
            if not repetida:
                for desplazamiento in product(range(-radio, radio + 1), repeat=len(f)):
                    c.tick(1, "acceso_hash")
                    vecina = rejilla.get(tuple(a + b for a, b in zip(celda, desplazamiento)))
                    if vecina and any(cercano(f, j) for j in vecina):
                        repetida = True
                        break
        if repetida:
            continue
        conservados.append(i)
        if en_rango(f):
            rejilla.setdefault(tuple(int(v // eps) for v in f), []).append(i)
        else:
            fuera.append(i)
    return conservados


def todas_distintas(xs: Sequence[float], contador: Contador | None = None) -> bool:
    return len(deduplicar_exacta([(x,) for x in xs], contador)) == len(xs)
