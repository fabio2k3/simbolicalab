from __future__ import annotations

from ..costo.turing import maquina_incremento
from ..nucleo.amortizado import LibroAmortizado


def potencial_unos(cinta: str) -> float:
    return 2.0 * cinta.count("1")


def analizar_incrementos(k: int) -> LibroAmortizado:
    maquina = maquina_incremento()
    libro = LibroAmortizado(potencial_inicial=potencial_unos("0"))
    cinta, cabezal = "0", 0

    for _ in range(k):
        r = maquina.ejecutar(cinta, cabezal)
        cinta, cabezal = r.cinta, r.cabezal
        libro.registrar(r.pasos, potencial_unos(cinta))
        
    return libro