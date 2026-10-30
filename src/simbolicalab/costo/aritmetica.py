from __future__ import annotations

from ..nucleo.contador import Contador
from .bits import tamaño_en_bits

def costo_suma_bits(a: int, b: int) -> int:
    return max(tamaño_en_bits(a), tamaño_en_bits(b))

def costo_multiplicacion_bits(a:int, b:int) -> int:
    return tamaño_en_bits(a) * tamaño_en_bits(b)

def cuadrados_repetidos(k: int, contador: Contador) ->int:
    x = 2
    for _ in range(k):
        contador.tick(1, "mult_unitaria")
        contador.tick(costo_multiplicacion_bits(x,x), "bits")
        x = x * x
    return x


def fibonacci_contado(n: int, contador: Contador) -> int:
    a = 0
    b = 1

    for _ in range(n):
        contador.tick(1, "suma")
        contador.tick(costo_suma_bits(a, b), "bits")
        a, b = b, a + b

    return a