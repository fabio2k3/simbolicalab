from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field
from typing import Any, Callable


def cota_de_informacion(salidas: int, respuestas: int = 2) -> int:
    if salidas < 1 or respuestas < 2:
        raise ValueError("salidas >= 1 y respuestas >= 2")
    
    h, capacidad = 0, 1
    while capacidad < salidas:
        capacidad *= respuestas
        h += 1
        
    return h


def cota_de_ordenar(n: int) -> int:
    return cota_de_informacion(math.factorial(n))


@dataclass(frozen=True)
class Elemento:
    valor: int
    posicion: int


@dataclass(frozen=True)
class ArbolDeDecision:
    n: int
    altura: int                                  
    hojas: int                                 
    caminos: dict[tuple[tuple[int, int, bool], ...], tuple[int, ...]] = field(repr=False)

    def como_dict(self) -> dict[str, Any]:
        def construir(prefijo: tuple) -> dict[str, Any]:
            if prefijo in self.caminos:
                return {"salida": list(self.caminos[prefijo])}
            
            siguientes = [c for c in self.caminos if c[: len(prefijo)] == prefijo]
            i, j, _ = siguientes[0][len(prefijo)]

            return {
                "pregunta": [i, j],
                "si": construir(prefijo + ((i, j, True),)),
                "no": construir(prefijo + ((i, j, False),)),
            }
        
        return construir(())


def arbol_de_decision(algoritmo: Callable[[list[Elemento], Callable[[Elemento, Elemento], bool]], list[Elemento]], n: int) -> ArbolDeDecision:
    caminos: dict[tuple, tuple[int, ...]] = {}

    for permutacion in itertools.permutations(range(n)):
        camino: list[tuple[int, int, bool]] = []

        def menor(a: Elemento, b: Elemento) -> bool:
            respuesta = a.valor < b.valor
            camino.append((a.posicion, b.posicion, respuesta))
            return respuesta

        salida = algoritmo([Elemento(v, i) for i, v in enumerate(permutacion)], menor)
        clave, orden = tuple(camino), tuple(e.posicion for e in salida)
        if caminos.setdefault(clave, orden) != orden:
            raise AssertionError("el algoritmo no depende solo de las respuestas: dos entradas con el mismo camino dan salidas distintas")
        
    return ArbolDeDecision(n, max((len(c) for c in caminos), default=0), len(caminos), caminos)
