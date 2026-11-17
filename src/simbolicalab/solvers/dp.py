from __future__ import annotations

import math

from ..nucleo.contrato import Presupuesto, Resultado
from ..nucleo.traza import TRAZA_NULA, Traza
from ..rs.datos import Datos
from ..rs.error import METRICAS
from ..rs.expresion import a_cadena
from ..rs.gramatica import Gramatica
from ..tecnicas.pd_tamano import tabla_pd


class SolverPD:
    """Mejor expresión por tamaño con un representante por firma. ancho=None es exacto; ancho=w poda por error."""

    nombre = "pd_tamano"

    def __init__(self, max_tam: int, metrica: str = "ecm", cifras: int | None = None, ancho: int | None = None,
                 vigilar: bool = False) -> None:
        if max_tam < 1:
            raise ValueError("max_tam debe ser al menos 1")
        if metrica not in METRICAS:
            raise ValueError(f"métrica desconocida: {metrica!r}; opciones: {sorted(METRICAS)}")
        if ancho is not None and ancho < 1:
            raise ValueError("ancho debe ser al menos 1 (o None para no podar)")
        self.max_tam, self.metrica, self.cifras, self.ancho, self.vigilar = max_tam, metrica, cifras, ancho, vigilar

    def resolver(self, datos: Datos, gramatica: Gramatica, presupuesto: Presupuesto,
                 traza: Traza | None = None) -> Resultado:
        traza = traza or TRAZA_NULA
        c = presupuesto.nuevo_contador()
        t = tabla_pd(datos, gramatica, self.max_tam, self.metrica, c, traza, self.cifras, self.ancho, self.vigilar)
        return Resultado(
            expresion=t.mejor,
            error=t.mejor_error if t.mejor is not None else math.inf,
            operaciones=c.total,
            agotado=t.agotado,
            detalle={
                "max_tam": self.max_tam, "metrica": self.metrica, "ancho": self.ancho, "cifras": self.cifras,
                "representantes": [n.representantes for n in t.niveles],
                "generadas": [n.generadas for n in t.niveles],
                "frente_de_pareto": [(s, a_cadena(e), err) for s, e, err in t.frente_de_pareto()],
            },
        )