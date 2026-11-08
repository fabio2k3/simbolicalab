from __future__ import annotations

import itertools
from typing import Callable, Sequence

from ..nucleo.contador import Contador
from .informacion import Elemento


def insercion(lista: list[Elemento], menor: Callable[[Elemento, Elemento], bool]) -> list[Elemento]:
    A = list(lista)

    for i in range(1, len(A)):
        j = i
        while j > 0 and menor(A[j], A[j - 1]):
            A[j], A[j - 1] = A[j - 1], A[j]
            j -= 1

    return A


def mergesort(lista: list[Elemento], menor: Callable[[Elemento, Elemento], bool]) -> list[Elemento]:
    if len(lista) <= 1:
        return list(lista)
    
    m = len(lista) // 2
    izq, der = mergesort(lista[:m], menor), mergesort(lista[m:], menor)
    salida, i, j = [], 0, 0
    while i < len(izq) and j < len(der):
        if menor(der[j], izq[i]):                   
            salida.append(der[j])
            j += 1
        else:
            salida.append(izq[i])
            i += 1

    return salida + izq[i:] + der[j:]


def peor_caso_exacto(algoritmo: Callable, n: int) -> int:
    peor = 0
    for permutacion in itertools.permutations(range(n)):
        cuenta = [0]

        def menor(a: Elemento, b: Elemento) -> bool:
            cuenta[0] += 1
            return a.valor < b.valor

        algoritmo([Elemento(v, i) for i, v in enumerate(permutacion)], menor)
        peor = max(peor, cuenta[0])
    return peor


def ordenar_por_error(errores: Sequence[float], contador: Contador | None = None) -> list[int]:
    c = contador if contador is not None else Contador()
    elementos = [Elemento(0, i) for i in range(len(errores))]       

    def menor(a: Elemento, b: Elemento) -> bool:
        c.tick(1, "comparacion")
        return errores[a.posicion] < errores[b.posicion]

    return [e.posicion for e in mergesort(elementos, menor)]


def ordenar_por_conteo(claves: Sequence[int], maximo: int, contador: Contador | None = None) -> list[int]:
    c = contador if contador is not None else Contador()
    if any(not (0 <= k <= maximo) for k in claves):
        raise ValueError("las claves deben ser enteros en [0, maximo]")
    
    cuenta = [0] * (maximo + 2)
    for k in claves:
        c.tick(1, "acceso")
        cuenta[k + 1] += 1

    for k in range(maximo + 1):
        c.tick(1, "acumular")
        cuenta[k + 1] += cuenta[k]

    salida = [0] * len(claves)
    for i, k in enumerate(claves):
        c.tick(1, "acceso")
        salida[cuenta[k]] = i
        cuenta[k] += 1

    return salida


def frente_de_pareto_cuadratico(tamanos: Sequence[int], errores: Sequence[float]) -> list[int]:
    frente = []
    for i in range(len(tamanos)):
        dominado = any(
            (tamanos[j] <= tamanos[i] and errores[j] <= errores[i]) and (tamanos[j] < tamanos[i] or errores[j] < errores[i])
            for j in range(len(tamanos)))
        
        repetido = any(tamanos[j] == tamanos[i] and errores[j] == errores[i] for j in range(i))

        if not dominado and not repetido:
            frente.append(i)
    return sorted(frente, key=lambda i: (tamanos[i], i))


def frente_de_pareto(tamanos: Sequence[int], errores: Sequence[float], contador: Contador | None = None) -> list[int]:
    c = contador if contador is not None else Contador()
    if not tamanos:
        return []
    
    if min(tamanos) < 1:
        raise ValueError("los tamaños deben ser enteros >= 1")
    
    S = max(tamanos)
    mejor_por_tamano: list[int | None] = [None] * (S + 1)             
    for i, s in enumerate(tamanos):
        c.tick(1, "acceso")
        actual = mejor_por_tamano[s]
        if actual is None or errores[i] < errores[actual]:
            mejor_por_tamano[s] = i

    frente: list[int] = []
    mejor_error = float("inf")
    for s in range(1, S + 1):
        c.tick(1, "recorrido")
        i = mejor_por_tamano[s]
        if i is not None and errores[i] < mejor_error:
            frente.append(i)
            mejor_error = errores[i]
            
    return frente
