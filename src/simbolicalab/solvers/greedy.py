from __future__ import annotations

import math

from ..tecnicas.ajuste_lineal import minimos_cuadrados, seleccion_hacia_adelante
from ..tecnicas.biblioteca import REDUCCIONES, biblioteca_de_terminos, reducir_biblioteca

from ..rs.datos import Datos
from ..rs.expresion import Const, Expr, Op, a_cadena
from ..rs.gramatica import Gramatica

from ..nucleo.contador import PresupuestoAgotado
from ..nucleo.contrato import Presupuesto, Resultado
from ..nucleo.traza import TRAZA_NULA, Traza




def combinacion_lineal(coefs: list[float], terminos: list[Expr]) -> Expr:
    partes = [Op("*", (Const(c), t)) for c, t in zip(coefs, terminos)]
    e = partes[0]
    for p in partes[1:]:
        e = Op("+", (e, p))

    return e


class SolverGreedy:
    nombre = "greedy_lineal"

    def __init__(self, k: int, max_tam: int, reduccion: str = "paralelas", cifras: int | None = None,
                 tol: float = 1e-9) -> None:
        if k < 1:
            raise ValueError("k debe ser al menos 1")
        if max_tam < 1:
            raise ValueError("max_tam debe ser al menos 1")
        if reduccion not in REDUCCIONES:
            raise ValueError(f"reducción desconocida: {reduccion!r}; opciones: {REDUCCIONES}")
        self.k, self.max_tam, self.reduccion, self.cifras, self.tol = k, max_tam, reduccion, cifras, tol


    def resolver(self, datos: Datos, gramatica: Gramatica, presupuesto: Presupuesto, traza: Traza | None = None) -> Resultado:
        traza = traza or TRAZA_NULA
        c = presupuesto.nuevo_contador()
        detalle: dict = {"k": self.k, "max_tam": self.max_tam, "reduccion": self.reduccion}

        try:
            terminos, t = biblioteca_de_terminos(datos, gramatica, self.max_tam, self.cifras, c)
            if t.agotado:
                raise PresupuestoAgotado(c.limite or 0, c.total)
            detalle["terminos_de_la_biblioteca"] = len(terminos)
            idx = reducir_biblioteca(terminos, self.reduccion, self.tol, c)
            detalle["terminos_tras_reducir"] = len(idx)
            cols = [terminos[i].columna for i in idx]
            sel = seleccion_hacia_adelante(cols, datos.ys, self.k, [float(terminos[i].costo) for i in idx], self.tol, c)
            if not sel.indices:
                return Resultado(None, math.inf, c.total, detalle)
            elegidos = [idx[i] for i in sel.indices]
            coefs, ecm = minimos_cuadrados([terminos[i].columna for i in elegidos], datos.ys, self.tol, c)
        except PresupuestoAgotado:
            return Resultado(None, math.inf, c.total, detalle, agotado=True)
        
        expr = combinacion_lineal(coefs, [terminos[i].expr for i in elegidos])
        detalle.update({"terminos": [a_cadena(terminos[i].expr) for i in elegidos], "coeficientes": coefs,"error_por_paso": list(sel.errores)})
        
        traza.emitir("mejora", formula=a_cadena(expr), tamano=len(elegidos), error=ecm)
        return Resultado(expr, ecm, c.total, detalle)