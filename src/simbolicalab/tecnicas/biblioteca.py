"""Biblioteca de términos candidatos: los representantes por firma del PD, como columnas para el ajuste lineal."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from ..nucleo.contador import Contador
from ..rs.datos import Datos
from ..rs.expresion import Expr, tamano
from ..rs.gramatica import Gramatica
from .matroides import MatroideLineal, clases_paralelas, goloso_base_lineal
from .pd_tamano import TablaPD, tabla_pd

REDUCCIONES = ("ninguna", "paralelas", "base")


@dataclass(frozen=True)
class Termino:
    expr: Expr
    columna: tuple[float, ...]
    costo: int                      # tamaño del árbol: la complejidad del término


def biblioteca_de_terminos(datos: Datos, g: Gramatica, max_tam: int, cifras: int | None = None, contador: Contador | None = None) -> tuple[list[Termino], TablaPD]:
    t = tabla_pd(datos, g, max_tam, "ecm", contador, cifras=cifras)
    terminos = [Termino(e, f, tamano(e)) for nivel in t.representantes for e, f, _ in nivel
                if all(math.isfinite(v) for v in f)]
    
    return terminos, t



def reducir_biblioteca(terminos: Sequence[Termino], modo: str = "paralelas", tol: float = 1e-9, contador: Contador | None = None) -> list[int]:
    if modo not in REDUCCIONES:
        raise ValueError(f"reducción desconocida: {modo!r}; opciones: {REDUCCIONES}")
    
    cols = [t.columna for t in terminos]
    if modo == "ninguna":
        return list(range(len(terminos)))
    if modo == "paralelas":
        return sorted(min(c, key=lambda i: (terminos[i].costo, i)) for c in clases_paralelas(cols))
    
    r = goloso_base_lineal(MatroideLineal(cols, tol, contador), [float(t.costo) for t in terminos])
    return sorted(r.elegidos)