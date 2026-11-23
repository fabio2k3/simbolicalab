from __future__ import annotations
import math
from typing import Callable
from dataclasses import dataclass

@dataclass(frozen=True)
class CasoMaestro:
    caso: str                 
    razon: float            
    exponente: float       
    con_log: bool            
    notacion: str


def _validar(a: float, b: float, d: float) -> None:
    if a < 1:
        raise ValueError("a debe ser al menos 1")
    if b <= 1:
        raise ValueError("b debe ser mayor que 1")
    if d < 0:
        raise ValueError("d no puede ser negativo")


def maestro(a: float, b: float, d: float) -> CasoMaestro:
    _validar(a, b, d)
    r = a / b ** d

    if math.isclose(r, 1.0, rel_tol=1e-12):
        return CasoMaestro("empate", 1.0, d, True, f"Θ(n^{d:g} log n)" if d else "Θ(log n)")
    if r < 1:
        return CasoMaestro("raiz", r, d, False, f"Θ(n^{d:g})" if d else "Θ(1)")
    
    e = math.log(a, b)
    return CasoMaestro("hojas", r, e, False, f"Θ(n^{e:.4g})")


def trabajo_por_nivel(a: float, b: float, d: float, n: int) -> list[float]:
    _validar(a, b, d)
    niveles, tam, nodos = [], float(n), 1.0
    while tam >= 1:
        niveles.append(nodos * tam ** d)
        tam, nodos = tam / b, nodos * a
    return niveles


def resolver(a: int, b: int, f: Callable[[int], float], n: int, base: float = 1.0) -> float:
    if a < 1 or b < 2:
        raise ValueError("hace falta a >= 1 y b entero >= 2")
    
    size = [n]
    while size[-1] > 1:
        if size[-1] % b:
            raise ValueError(f"{n} no es una potencia de {b}")
        size.append(size[-1] // b)
    t = base

    for m in reversed(size[:-1]):
        t = a * t + f(m)
    return t


def verificar_maestro(a: int, b: int, d: float, exponente_max: int = 12, ultimos: int = 5, tolerancia: float = 0.3) -> dict:
    caso = maestro(a, b, d)
    razones = []

    for L in range(1, exponente_max + 1):
        n = b ** L
        t = resolver(a, b, lambda m: m ** d, n)
        g = n ** caso.exponente * (math.log(n) if caso.con_log else 1.0)
        razones.append(t / g)

    queue = razones[-ultimos:]
    media = sum(queue) / len(queue)
    return {"caso": caso, "razones": razones, "acotado": all(abs(x / media - 1) <= tolerancia for x in queue)}