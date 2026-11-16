from __future__ import annotations

import random


def puntos_mismo_punto(rondas: int, p: int, rng: random.Random) -> list[int]:
    r = rng.randrange(p)
    return [r] * rondas


def puntos_rango_pequeno(rondas: int, p: int, rng: random.Random, rango: int = 2) -> list[int]:
    return [rng.randrange(min(rango, p)) for _ in range(rondas)]