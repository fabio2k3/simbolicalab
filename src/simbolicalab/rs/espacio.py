from __future__ import annotations

from .gramatica import Gramatica

def contar_por_size(g: Gramatica, max_tam: int) -> list[int]:
    t = g.n_terminales
    u = len(g.unarios), 
    b = len(g.binarios) 

    n = [0]* (max_tam + 1)

    for s in range(1, max_tam + 1):
        if s == 1:
            n[1] = t
        else:
            n[s] = u * n[s - 1] + b * sum(n[k] * n[s - 1 - k] for k  in  range(1, s - 1))
    return n

def costo_fuerza_bruta(g: Gramatica, max_tam: int,  n_puntos: int) -> int:
    n = contar_por_size(g, max_tam)
    return sum(n[s] * (1 + s * n_puntos) for s in range(1, max_tam + 1))

def mayor_size_alcanzable(g: Gramatica, operaciones: int, n_puntos: int, tope: int = 60) -> int:
    gastado = 0
    mejor = 0

    for s in range(1, tope + 1):
        gastado = costo_fuerza_bruta(g, s, n_puntos)
        if gastado > operaciones:
            break
        mejor = s
    return mejor