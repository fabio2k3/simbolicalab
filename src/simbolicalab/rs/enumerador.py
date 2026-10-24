from __future__ import annotations
from typing import Iterator

from ..nucleo.contador import Contador
from .expresion import Expr, Op
from .gramatica import Gramatica

def enumerar( g: Gramatica, max_tam: int, contador: Contador | None = None) -> Iterator[Expr]:
    c  = contador if contador is not None else Contador()
    por_size = list[list[Expr]] = []

    for s in range(1, max_tam + 1):
        nivel: list[Expr] = []

        if s == 1:
            for t in g.terminales:
                c.tick(1, "construccion")
                nivel.append(t)
                yield t
        else:
            for nombre in g.unarios:
                for h in por_size[s - 1]:
                    c.tick(1, "construccion")
                    e = Op(nombre, (h,))
                    nivel.append(e)
                    yield e

            for k in range(1, s - 1):
                for left in por_size[k]:
                    for right in por_size[s - 1 - k]:
                        for nombre in g.binarios:
                            c.tick(1, "construccion")
                            e = Op(nombre, (left, right))
                            nivel.append(e)
                            yield e
        por_size.append(nivel)

        