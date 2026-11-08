from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from ..nucleo.contador import Contador
from ..rs.datos import Datos
from ..rs.error import METRICAS
from ..rs.expresion import Expr
from ..solvers.fuerza_bruta import _mejora_de_verdad

Algoritmo = Callable[[int, Callable[[int], float]], int]       


@dataclass(frozen=True)
class Partida:
    consultas: int
    respuesta: int
    correcta: bool
    instancia: list[float] | None        


def jugar_contra_el_adversario(algoritmo: Algoritmo, n: int) -> Partida:
    if n < 2:
        raise ValueError("hacen falta al menos 2 candidatas")
    consultadas: list[int] = []

    def consultar(i: int) -> float:
        if not 0 <= i < n:
            raise IndexError(i)
        if i not in consultadas:
            consultadas.append(i)
        return 1.0                                        

    r = algoritmo(n, consultar)

    if len(consultadas) == n:
        return Partida(len(consultadas), r, True, None)   
       
    instancia = [1.0] * n
    sin_evaluar = [j for j in range(n) if j not in consultadas]
    otra = next((j for j in sin_evaluar if j != r), None)

    if otra is not None:
        instancia[otra] = 0.0                               
    else:
        instancia[r] = 2.0          

    return Partida(len(consultadas), r, False, instancia)



def verificar_instancia(algoritmo: Algoritmo, instancia: Sequence[float]) -> tuple[bool, int]:
    r = algoritmo(len(instancia), lambda i: instancia[i])
    return instancia[r] == min(instancia), r


def evaluar_todas(n: int, consultar: Callable[[int], float]) -> int:
    return min(range(n), key=consultar)


def saltar_la_ultima(n: int, consultar: Callable[[int], float]) -> int:
    return min(range(n - 1), key=consultar)


def saltar_la_primera(n: int, consultar: Callable[[int], float]) -> int:
    return min(range(1, n), key=consultar)


def mirar_solo_la_mitad(n: int, consultar: Callable[[int], float]) -> int:
    return min(range(n // 2), key=consultar)


def mejor_formula(candidatas: Sequence[Expr], datos: Datos, metrica: str = "ecm", contador: Contador | None = None, omitir_ultimas: int = 0,) -> tuple[int, float]:
    c = contador if contador is not None else Contador()
    medir = METRICAS[metrica]
    mejor, mejor_error = -1, float("inf")
    
    for i in range(len(candidatas) - omitir_ultimas):
        err = medir(candidatas[i], datos, c)
        if _mejora_de_verdad(err, mejor_error):
            mejor, mejor_error = i, err

    return mejor, mejor_error
