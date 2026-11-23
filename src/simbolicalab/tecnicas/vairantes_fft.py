from __future__ import annotations
from typing import Sequence
from .fourier import fft_iterativa, ifft
from .analisis_espectral import espectro, picos


def multiplicar_fft_mal(a: Sequence[float], b: Sequence[float]) -> list[int]:
    m = len(a) + len(b) - 1
    N = 1
    while N < m - 1:
        N *= 2
    fa = fft_iterativa(list(a) + [0] * (N - len(a)))
    fb = fft_iterativa(list(b) + [0] * (N - len(b)))
    c = ifft([u * v for u, v in zip(fa, fb)])
    return [round(z.real) for z in c[:m]]


def ifft_sin_dividir(y: Sequence[complex]) -> list[complex]:
    return fft_iterativa(y, -1)


def frecuencia_dominante_sin_dt(ys: Sequence[float], dt: float) -> float:
    e = espectro(ys, dt)
    p = picos(e, 1)[0]
    return p.indice / e.N


def frecuencia_dominante_con_media(ys: Sequence[float], dt: float) -> float:
    e = espectro(ys, dt, quitar_media=False)
    mag = e.magnitudes
    k = max(range(len(mag)), key=lambda i: mag[i])
    return e.frecuencias[k]


def frecuencia_dominante_n_menos_1(ys: Sequence[float], dt: float) -> float:
    e = espectro(ys, dt)
    p = picos(e, 1)[0]
    return p.indice / ((e.N - 1) * dt)