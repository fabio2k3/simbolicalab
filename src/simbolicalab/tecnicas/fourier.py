
from __future__ import annotations

import math
import random
import cmath
from typing import Sequence

from ..nucleo.contador import Contador


def es_potencia_de_dos(n: int) -> bool:
    return n >= 1 and n & (n - 1) == 0


def siguiente_potencia_de_dos(m: int) -> int:
    n = 1
    while n < m:
        n *= 2
    return n


def raiz(n: int, k: int, signo: int = 1) -> complex:
    return cmath.exp(signo * 2j * math.pi * k / n)


def dft(a: Sequence[complex], signo: int = 1, contador: Contador | None = None) -> list[complex]:
    n = len(a)
    if contador is not None:
        contador.tick(n * n, "mult")
        contador.tick(n * (n - 1), "suma")

    return [sum(a[j] * raiz(n, signo * j * k) for j in range(n)) for k in range(n)]



def _exigir_potencia_de_dos(n: int) -> None:
    if not es_potencia_de_dos(n):
        raise ValueError(f"la FFT de base 2 necesita un largo potencia de dos, no {n}")


def fft(a: Sequence[complex], signo: int = 1, contador: Contador | None = None) -> list[complex]:
    n = len(a)
    _exigir_potencia_de_dos(n)
    if n == 1:
        return [complex(a[0])]
    
    pares, impares = fft(a[0::2], signo, contador), fft(a[1::2], signo, contador)
    y = [0j] * n

    for k in range(n // 2):
        t = raiz(n, signo * k) * impares[k]
        y[k], y[k + n // 2] = pares[k] + t, pares[k] - t

    if contador is not None:
        contador.tick(n // 2, "mult")
        contador.tick(n, "suma")

    return y


def _invertir_bits(i: int, bits: int) -> int:
    r = 0
    for _ in range(bits):
        r, i = (r << 1) | (i & 1), i >> 1
    return r


def fft_iterativa(a: Sequence[complex], signo: int = 1, contador: Contador | None = None) -> list[complex]:
    n = len(a)
    _exigir_potencia_de_dos(n)
    bits = n.bit_length() - 1
    y = [complex(a[_invertir_bits(i, bits)]) for i in range(n)]
    raices = [raiz(n, signo * k) for k in range(n // 2)]
    m = 2

    while m <= n:
        paso, medio = n // m, m // 2
        for s in range(0, n, m):
            for k in range(medio):
                t = raices[k * paso] * y[s + k + medio]
                u = y[s + k]
                y[s + k], y[s + k + medio] = u + t, u - t
        if contador is not None:
            contador.tick(n // 2, "mult")
            contador.tick(n, "suma")
        m *= 2
    return y


def ifft(y: Sequence[complex], contador: Contador | None = None) -> list[complex]:
    n = len(y)
    if contador is not None:
        contador.tick(n, "mult")
    return [v / n for v in fft_iterativa(y, -1, contador)]


def multiplicar_escolar(a: Sequence[float], b: Sequence[float], contador: Contador | None = None) -> list:
    if not a or not b:
        return []
    if contador is not None:
        contador.tick(len(a) * len(b), "mult")
        contador.tick(len(a) * len(b), "suma")
    res = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            res[i + j] += x * y
    return res


def _karatsuba(A: list, B: list, c: Contador | None) -> list:
    n = len(A)
    if n == 1:
        if c is not None:
            c.tick(1, "mult")
        return [A[0] * B[0]]
    
    h = n // 2
    a0, a1, b0, b1 = A[:h], A[h:], B[:h], B[h:]
    z0, z2 = _karatsuba(a0, b0, c), _karatsuba(a1, b1, c)
    z1 = _karatsuba([x + y for x, y in zip(a0, a1)], [x + y for x, y in zip(b0, b1)], c)
    medio = [u - v - w for u, v, w in zip(z1, z0, z2)]
    res = [0] * (2 * n - 1)
    for i, v in enumerate(z0):
        res[i] += v
    for i, v in enumerate(medio):
        res[i + h] += v
    for i, v in enumerate(z2):
        res[i + 2 * h] += v
    if c is not None:
        c.tick(6 * n - 5, "suma")          
    return res


def multiplicar_karatsuba(a: Sequence[float], b: Sequence[float], contador: Contador | None = None) -> list:
    if not a or not b:
        return []
    n = siguiente_potencia_de_dos(max(len(a), len(b)))
    A, B = list(a) + [0] * (n - len(a)), list(b) + [0] * (n - len(b))
    return _karatsuba(A, B, contador)[:len(a) + len(b) - 1]


def multiplicar_fft(a: Sequence[float], b: Sequence[float], contador: Contador | None = None, redondear: bool = True) -> list:
    if not a or not b:
        return []
    
    m = len(a) + len(b) - 1
    N = siguiente_potencia_de_dos(m)
    fa = fft_iterativa(list(a) + [0] * (N - len(a)), 1, contador)
    fb = fft_iterativa(list(b) + [0] * (N - len(b)), 1, contador)
    if contador is not None:
        contador.tick(N, "mult")
    c = ifft([u * v for u, v in zip(fa, fb)], contador)[:m]
    return [round(z.real) for z in c] if redondear else [z.real for z in c]


def multiplicar_exacta(a: Sequence[int], b: Sequence[int]) -> list[int]:
    if not a or not b:
        return []
    
    s = (max(max(a), max(b)) ** 2 * min(len(a), len(b))).bit_length() + 1
    A = B = 0
    for x in reversed(a):
        A = (A << s) | x
    for x in reversed(b):
        B = (B << s) | x

    C, mascara = A * B, (1 << s) - 1
    return [(C >> (s * i)) & mascara for i in range(len(a) + len(b) - 1)]


def error_de_redondeo(N: int, cifras: int, semilla: int = 0) -> dict:
    rng = random.Random(semilla)
    a = [rng.randrange(10 ** cifras) for _ in range(N // 2)]
    b = [rng.randrange(10 ** cifras) for _ in range(N // 2)]
    aprox, bueno = multiplicar_fft(a, b, redondear=False), multiplicar_exacta(a, b)
    return {"N": N, "cifras": cifras,
            "error_maximo": max(abs(x - y) for x, y in zip(aprox, bueno)),
            "coeficientes_equivocados": sum(round(x) != y for x, y in zip(aprox, bueno)),
            "coeficiente_maximo": max(bueno), "suma_de_coeficientes": sum(bueno)}