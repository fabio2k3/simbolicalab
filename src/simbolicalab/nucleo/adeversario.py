from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Callable

@dataclass(frozen=True)
class Deteccion:
    pruebas: int
    detectadas: int
    primer_contraejemplo: Any

    @property
    def tasa(self) -> float:
        return self.detectadas / self.pruebas if self.pruebas else 0.0


def tasa_de_deteccion(generador: Callable[[random.Random], Any], correcto: Callable[[Any], Any], variante: Callable[[Any], Any], pruebas: int = 100, semilla: int = 0) -> Deteccion:
    if pruebas < 1:
        raise ValueError("pruebas debe ser al menos 1")

    rng = random.Random(semilla)
    detectadas, primero = 0, None

    for _ in range(pruebas):
        entrada = generador(rng)
        if correcto(entrada) != variante(entrada):
            detectadas += 1
            if primero is None:
                primero = entrada
    return Deteccion(pruebas, detectadas, primero)