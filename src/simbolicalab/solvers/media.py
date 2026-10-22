from __future__ import annotations

import math

from ..nucleo.contador import PresupuestoAgotado
from ..nucleo.contrato import Presupuesto, Resultado
from ..nucleo.traza import TRAZA_NULA, Traza

class SolverMedia:
    nombre = "media"

    def resolver(self, datos, gramatica, presupuesto: Presupuesto, traza: Traza | None = None) -> Resultado:
        traza = traza or TRAZA_NULA
        c = presupuesto.nuevo_contador()

        try:
            suma = 0.0
            for _ , y in datos:
                c.tick(1, "lectura")
                suma += y
            media = suma / len(datos)
            traza.emitir("media_calculada", valor = media)
            
            error = 0.0
            for _, y in datos:
                c.tick(1, "lectura")
                error += (y - media) ** 2
            error /= len(datos)
            traza.emitir("error_calculado", valor=error)
            return Resultado(media, error, c.total)
        
        except PresupuestoAgotado:
            return Resultado(None, math.inf, c.total,agotado=True)