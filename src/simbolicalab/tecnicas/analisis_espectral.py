from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from .fourier import fft_iterativa, siguiente_potencia_de_dos
from ..nucleo.contador import Contador
from .ajuste_lineal import minimos_cuadrados



@dataclass(frozen=True)
class Espectro:
    frecuencias: tuple[float, ...]         
    valores: tuple[complex, ...]          
    N: int
    dt: float

    @property
    def magnitudes(self) -> tuple[float, ...]:
        return tuple(abs(v) for v in self.valores)

    @property
    def resolucion(self) -> float:
        return 1.0 / (self.N * self.dt)


@dataclass(frozen=True)
class Pico:
    indice: int
    frecuencia: float                      
    magnitud: float


def espectro(ys: Sequence[float], dt: float, quitar_media: bool = True, relleno: int = 1, contador: Contador | None = None) -> Espectro:
    n = len(ys)
    if n < 4:
        raise ValueError("hacen falta al menos 4 muestras")
    if dt <= 0:
        raise ValueError("dt debe ser positivo")
    if relleno < 1:
        raise ValueError("relleno debe ser al menos 1")
    media = sum(ys) / n if quitar_media else 0.0
    N = siguiente_potencia_de_dos(relleno * n)
    y = fft_iterativa([v - media for v in ys] + [0.0] * (N - n), 1, contador)
    mitad = N // 2
    return Espectro(tuple(k / (N * dt) for k in range(mitad + 1)), tuple(y[:mitad + 1]), N, dt)


def picos(e: Espectro, cuantos: int = 1, umbral: float = 0.0) -> list[Pico]:
    if cuantos < 1:
        raise ValueError("cuantos debe ser al menos 1")
    mag = e.magnitudes
    locales = [Pico(k, e.frecuencias[k], mag[k]) for k in range(1, len(mag) - 1) if mag[k - 1] < mag[k] >= mag[k + 1]]
    locales.sort(key=lambda p: -p.magnitud)
    if not locales:
        return []
    return [p for p in locales[:cuantos] if p.magnitud >= umbral * locales[0].magnitud]


def refinar_jacobsen(e: Espectro, pico: Pico) -> float:
    k, X = pico.indice, e.valores
    if not 1 <= k < len(X) - 1:
        return pico.frecuencia
    denom = 2 * X[k] - X[k - 1] - X[k + 1]
    if abs(denom) == 0:
        return pico.frecuencia
    delta = ((X[k - 1] - X[k + 1]) / denom).real
    delta = max(-0.5, min(0.5, delta))
    return (k + delta) * e.resolucion


def _columnas(ts: Sequence[float], omega: float) -> list[list[float]]:
    return [[1.0] * len(ts), [math.sin(omega * t) for t in ts], [math.cos(omega * t) for t in ts]]


def error_de_ajuste(ts: Sequence[float], ys: Sequence[float], omega: float, contador: Contador | None = None) -> float:
    try:
        return minimos_cuadrados(_columnas(ts, omega), ys, 1e-9, contador)[1]
    except ValueError:
        return math.inf


def refinar_por_ajuste(ts: Sequence[float], ys: Sequence[float], frecuencia: float, ancho: float, iteraciones: int = 40, contador: Contador | None = None) -> float:
    lo, hi = max(frecuencia - ancho, 1e-12), frecuencia + ancho
    fi = (math.sqrt(5) - 1) / 2
    a, b = hi - fi * (hi - lo), lo + fi * (hi - lo)
    ea = error_de_ajuste(ts, ys, 2 * math.pi * a, contador)
    eb = error_de_ajuste(ts, ys, 2 * math.pi * b, contador)
    for _ in range(iteraciones):
        if ea < eb:
            hi, b, eb = b, a, ea
            a = hi - fi * (hi - lo)
            ea = error_de_ajuste(ts, ys, 2 * math.pi * a, contador)
        else:
            lo, a, ea = a, b, eb
            b = lo + fi * (hi - lo)
            eb = error_de_ajuste(ts, ys, 2 * math.pi * b, contador)
    return (lo + hi) / 2


def submuestrear(ts: Sequence[float], ys: Sequence[float], cada: int) -> tuple[list[float], list[float]]:
    if cada < 1:
        raise ValueError("cada debe ser al menos 1")
    return list(ts[::cada]), list(ys[::cada])


def alias(frecuencia: float, dt: float) -> float:
    fs = 1.0 / dt
    return abs(frecuencia - fs * round(frecuencia / fs))