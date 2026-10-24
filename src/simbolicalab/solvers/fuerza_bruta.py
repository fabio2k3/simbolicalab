from    __future__ import annotations

import math

from ..nucleo.contador import PresupuestoAgotado
from ..nucleo.contrato import Presupuesto, Resultado
from ..nucleo.traza import TRAZA_NULA, Traza
from ..rs.datos import Datos
from ..rs.enumerador import enumerar
from ..rs.error import METRICAS
from ..rs.expresion import a_cadena, tamano
from ..rs.gramatica import Gramatica

TOLERANCIA_RELATIVA = 1e-9
TOLERANCIA_ABSOLUTA = 1e-12

def _mejora_de_verdad(nuevo: float, actual: float) -> bool:
    if math.isinf(actual):
        return nuevo < actual
    return nuevo < actual - max(TOLERANCIA_RELATIVA * actual, TOLERANCIA_ABSOLUTA)

class SolverFuerzaBruta:
    nombre = "fuerza_bruta"

    def __init__(self, max_tam:int, metrica: str = "ecm") -> None:
        if max_tam < 1:
            raise ValueError("max_tam debe ser al menos 1")
        if metrica not in METRICAS:
            raise ValueError(f"métrica desconocida: {metrica!r}; opciones: {sorted(METRICAS)}")
        self.max_tam = max_tam
        self.metrica = metrica


    def resolver(self, datos: Datos, gramatica: Gramatica, presupuesto: Presupuesto, traza: Traza | None = None) -> Resultado:
        
        traza = traza or TRAZA_NULA
        medir_error = METRICAS[self.metrica]

        c = presupuesto.nuevo_contador()
        
        mejor = None
        mejor_error = math.inf
        evaluadas = 0 

        agotado = False

        try: 
            for e in enumerar(gramatica, self.max_tam, c):
                err = medir_error(e, datos, c)
                evaluados += 1
                if _mejora_de_verdad(err, mejor_error):
                    mejor = e
                    mejor_error = err
                    traza.emitir("mejora", formula= a_cadena(e), tamano=tamano(e), error = err)
        except PresupuestoAgotado:
            agotado = True

        return Resultado(expresion=mejor, error = mejor_error, operaciones=c.total, agotado=agotado,
                         detalle={"evaluadas": evaluadas, "max_tam": self.max_tam, "métrica": self.metrica})