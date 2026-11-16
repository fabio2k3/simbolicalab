from __future__ import annotations

import math
import random

from ..rs.datos import Datos


def oscilador_sintetico(n: int = 128, ruido: float = 0.05, semilla: int = 0, amplitud: float = 2.0,
    frecuencia: float = 0.5, paso: float = 0.1, amortiguamiento: float = 0.0,) -> Datos:
    
    if n < 2:
        raise ValueError("n debe ser al menos 2")
    if ruido < 0:
        raise ValueError("el ruido no puede ser negativo")
    if amplitud <= 0:
        raise ValueError("la amplitud debe ser positiva")
    if paso <= 0:
        raise ValueError("el paso debe ser positivo")
    if amortiguamiento < 0:
        raise ValueError("el amortiguamiento no puede ser negativo")
    if frecuencia <= 0:
        raise ValueError("la frecuencia debe ser positiva")
    if frecuencia >= 1.0 / (2.0 * paso):
        raise ValueError("la frecuencia debe ser menor que la de Nyquist, 1 / (2 * paso)")

    rng = random.Random(semilla)
    omega = 2.0 * math.pi * frecuencia
    ts = [k * paso for k in range(n)]
    ys = [
        amplitud * math.exp(-amortiguamiento * t) * math.sin(omega * t) + rng.gauss(0.0, ruido * amplitud)
        for t in ts
    ]

    if amortiguamiento > 0:
        ley = f"{amplitud:g} * exp(-{amortiguamiento:g} * t) * sin({omega:.6g} * t)"
    else:
        ley = f"{amplitud:g} * sin({omega:.6g} * t)"

    return Datos(
        xs=tuple(ts),
        ys=tuple(ys),
        nombre_x="t",
        nombre=(f"Oscilador sintético (n={n}, ruido={ruido:g}, f={frecuencia:g}, "
                f"paso={paso:g}, semilla={semilla})"),
        ley_oculta=ley,
    )


def es_rejilla_uniforme(datos: Datos, tol: float = 1e-9) -> bool:
    xs = datos.xs
    if len(xs) < 2:
        return False
    d = xs[1] - xs[0]
    if d <= 0:
        return False
    return all(abs((b - a) - d) <= tol * d for a, b in zip(xs, xs[1:]))