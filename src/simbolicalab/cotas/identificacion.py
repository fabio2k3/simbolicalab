from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..rs.deduplicacion import deduplicar_cuadratico, firma
from ..rs.expresion import Expr
from .informacion import cota_de_informacion

RESOLUCION = 1e-9


@dataclass(frozen=True)
class Consulta:
    """«¿f*(xs[x_indice]) <= umbral?»"""
    x_indice: int
    umbral: float


def candidatas_en_el_dominio(formulas: Sequence[Expr], nombre_x: str, xs: Sequence[float], eps: float = RESOLUCION) -> tuple[list[int], list[tuple[float, ...]]]:
    firmas = [firma(e, nombre_x, xs) for e in formulas]
    reps = deduplicar_cuadratico(firmas, eps)
    return reps, [firmas[i] for i in reps]          


def cota_de_identificacion(n_candidatas: int) -> int:
    return cota_de_informacion(n_candidatas, 2)


def x_separadores(firmas: Sequence[Sequence[float]], resolucion: float = RESOLUCION) -> list[int]:
    if not firmas:
        return []
    
    buenos = []
    for j in range(len(firmas[0])):
        valores = sorted(f[j] for f in firmas)
        if all(b - a > resolucion for a, b in zip(valores, valores[1:])):
            buenos.append(j)

    return buenos


class DisenoDeExperimento:
    def __init__(self, firmas: Sequence[Sequence[float]], resolucion: float = RESOLUCION) -> None:
        if not firmas:
            raise ValueError("hacen falta candidatas")
        self.firmas = [tuple(f) for f in firmas]
        self.resolucion = resolucion
        self._arbol = self._construir()


    def _mejor_corte(self, conjunto: list[int]) -> tuple[Consulta, list[int], list[int]]:
        mejor: tuple[int, int, int, float, list[int]] | None = None     

        for j in range(len(self.firmas[0])):
            ordenados = sorted(conjunto, key=lambda i: self.firmas[i][j])
            for p in range(1, len(ordenados)):
                a, b = self.firmas[ordenados[p - 1]][j], self.firmas[ordenados[p]][j]
                if b - a > self.resolucion:
                    peor = max(p, len(ordenados) - p)
                    if mejor is None or peor < mejor[0]:
                        mejor = (peor, j, p, a, ordenados)

        if mejor is None:
            raise ValueError("candidatas indistinguibles con estos puntos de consulta")
        _, j, p, umbral, ordenados = mejor
        return Consulta(j, umbral), ordenados[:p], ordenados[p:]

    def _construir(self) -> dict:
        raiz: dict = {}
        pila = [(list(range(len(self.firmas))), raiz)]
        while pila:
            conjunto, nodo = pila.pop()
            if len(conjunto) == 1:
                nodo["candidata"] = conjunto[0]
                continue
            consulta, si, no = self._mejor_corte(conjunto)
            nodo["consulta"], nodo["si"], nodo["no"] = consulta, {}, {}
            pila.append((si, nodo["si"]))
            pila.append((no, nodo["no"]))
        return raiz


    def consultas_para(self, verdadera: int) -> list[tuple[Consulta, bool]]:
        nodo, camino = self._arbol, []

        while "candidata" not in nodo:
            q = nodo["consulta"]
            respuesta = self.firmas[verdadera][q.x_indice] <= q.umbral
            camino.append((q, respuesta))
            nodo = nodo["si"] if respuesta else nodo["no"]

        assert nodo["candidata"] == verdadera, "el diseño no identifica a la candidata"
        return camino

    def profundidades(self) -> list[int]:
        return [len(self.consultas_para(i)) for i in range(len(self.firmas))]


def profundidad_del_diseno(firmas: Sequence[Sequence[float]]) -> dict[str, float]:
    d = DisenoDeExperimento(firmas).profundidades()
    return {
        "candidatas": len(firmas),
        "peor_caso": max(d),
        "medio": sum(d) / len(d),
        "cota": cota_de_identificacion(len(firmas)),
    }


def clases_distinguibles(formulas: Sequence[Expr], nombre_x: str, puntos: Sequence[float], eps: float = RESOLUCION) -> int:
    firmas = [firma(e, nombre_x, puntos) for e in formulas]
    return len(deduplicar_cuadratico(firmas, eps))
