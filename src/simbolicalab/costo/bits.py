from __future__ import annotations

from ..nucleo.contador import Contador

SEGUNDOS_POR_ANIO = 3600 * 24 * 365

def tamaño_en_bits(n: int) -> int:
    if n < 0:
        raise ValueError("n debe ser no negativo")
    return max(1, n.bit_length())

def es_primo_contador(n: int, contador: Contador) -> bool:
    if n < 2:
        return False
    d = 2

    while d * d <= n:
        contador.tick(1, "division")
        if n % d == 0:
            return False
        d += 1

    return True

def tiempo_division_de_prueba(bits: int, ops_x_segundo: float = 1e9) -> float:
    divisiones = 2 ** (bits // 2)
    return divisiones / ops_x_segundo

def mochila_contada(pesos: list[int], valores: list[int], capacidad: int, contador: Contador) -> int:
    if len(pesos) != len(valores):
        raise ValueError("pesos y valores deben tener la misma longitud")
    mejor = [0] * (capacidad + 1)
    for peso, valor in zip(pesos, valores):
        contador.tick(capacidad + 1, "celda")
        for w in range(capacidad, peso - 1, -1):
            candidato = mejor[w - peso] + valor
            if candidato > mejor[w]:
                mejor[w] = candidato
    return mejor[capacidad]