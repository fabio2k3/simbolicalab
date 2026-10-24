from __future__ import annotations

import math
import random

from ..rs.datos import Datos

# (nombre, semieje mayor en UA, período en años)
PLANETAS : tuple[tuple[str, float, float], ...] = (
    ("Mercurio", 0.387, 0.241 ),
    ("Venus", 0.723, 0.615),
    ("Tierra", 1.000, 1.000),
    ("Marte", 1.524, 1.881),
    ("Júpiter", 5.203, 11.862),
    ("Saturno", 9.537, 29.457),
    ("Urano", 19.191, 84.011),
    ("Neptuno", 30.069, 164.79),
)

LEY = "a * sqrt(a)"

def kelper_real() -> Datos:
    return Datos(
        xs= tuple(a for _,a,_ in PLANETAS),
        ys = tuple(t for _,_, t in PLANETAS),
        nombre_x = "a",
        nombre= "Kepler (8 planetas)",
        ley_oculta=LEY,
    )

def kepler_sintetico(n: int = 30, ruido: float = 0.02, semilla: int = 0) -> Datos:
    if n < 1:
        raise ValueError("n debe ser al menos 1")
    if ruido < 0:
        raise ValueError("el ruido no pueder ser negativo")

    rng = random.Random()
    a_s = sorted(math.exp(rng.uniform(math.log(0.3), math.log(40.0))) for _ in range(n))

    ts = [a ** 1.5 * (1.0 + rng.gauss(0.0, ruido)) for a in a_s]

    return Datos( xs = tuple(a_s), ys =tuple(ts), nombre_x="a", 
                 nombre=f"Kepler sintético ( n={n}, ruido={ruido:g}, semilla = {semilla})",
                 ley_oculta=LEY,)

