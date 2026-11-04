from __future__ import annotations

from typing import Iterator, Sequence

from ..nucleo.contador import Contador
from ..rs.expresion import Expr, Op
from ..rs.operadores import OPERADORES
from .union_find import UnionFind


def intercambios(e: Expr) -> Iterator[Expr]:
    if not isinstance(e, Op):
        return
    if OPERADORES[e.nombre].conmutativo and len(e.hijos) == 2:
        yield Op(e.nombre, (e.hijos[1], e.hijos[0]))

    for i, h in enumerate(e.hijos):
        for h2 in intercambios(h):
            yield Op(e.nombre, e.hijos[:i] + (h2,) + e.hijos[i + 1:])


def clases_por_conmutatividad(formulas: Sequence[Expr], contador: Contador | None = None) -> UnionFind:
    indice = {e: i for i, e in enumerate(formulas)}
    if len(indice) != len(formulas):
        raise ValueError("la lista contiene fórmulas repetidas")
    uf = UnionFind(len(formulas), contador=contador)

    for i, e in enumerate(formulas):
        for e2 in intercambios(e):
            j = indice.get(e2)
            if j is not None:
                uf.union(i, j)
                
    return uf


def reduccion_por_simetria(formulas: Sequence[Expr]) -> tuple[int, int]:
    return len(formulas), clases_por_conmutatividad(formulas).conjuntos
