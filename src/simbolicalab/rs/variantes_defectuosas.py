from __future__ import annotations

from typing import Sequence

from ..nucleo.contador import Contador
from .deduplicacion import Firma, _distancia2, _validar


def deduplicar_solo_ultimo(firmas: Sequence[Firma | None], eps: float, contador: Contador | None = None) -> list[int]:
    _validar(firmas, eps)
    c = contador if contador is not None else Contador()
    conservados: list[int] = []
    for i, f in enumerate(firmas):
        if f is None:
            continue
        if conservados:
            c.tick(1, "comparacion_firma")
            if _distancia2(f, firmas[conservados[-1]]) <= eps * eps:        
                continue
        conservados.append(i)
    return conservados


def deduplicar_contra_todas(firmas: Sequence[Firma | None], eps: float, contador: Contador | None = None) -> list[int]:
    _validar(firmas, eps)
    c = contador if contador is not None else Contador()
    vistas: list[int] = []
    conservados: list[int] = []
    for i, f in enumerate(firmas):
        if f is None:
            continue
        repetida = False
        for j in vistas:
            c.tick(1, "comparacion_firma")
            if _distancia2(f, firmas[j]) <= eps * eps:                      
                repetida = True
                break
        vistas.append(i)
        if not repetida:
            conservados.append(i)
    return conservados
