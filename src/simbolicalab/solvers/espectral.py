from __future__ import annotations

from ..conjuntos.oscilador import es_rejilla_uniforme
from ..nucleo.contador import PresupuestoAgotado
from ..nucleo.contrato import Presupuesto, Resultado
from ..nucleo.traza import TRAZA_NULA, Traza
from ..rs.datos import Datos
from ..rs.expresion import Const, Expr, Op, Var, a_cadena
from ..rs.gramatica import Gramatica
from ..tecnicas.ajuste_lineal import minimos_cuadrados
from ..tecnicas.analisis_espectral import espectro, picos, refinar_jacobsen, refinar_por_ajuste

import math

REFINADOS = ("ninguno", "jacobsen", "ajuste")


def _seno_coseno(omega: float, t: str) -> tuple[Expr, Expr]:
    arg = Op("*", (Const(omega), Var(t)))
    return Op("sin", (arg,)), Op("cos", (arg,))


class SolverEspectral:
    nombre = "espectral"

    def __init__(self, m: int = 1, refinar: str = "ajuste", quitar_media: bool = True, relleno: int = 1) -> None:
        if m < 1:
            raise ValueError("m debe ser al menos 1")
        if refinar not in REFINADOS:
            raise ValueError(f"refinado desconocido: {refinar!r}; opciones: {REFINADOS}")
        if relleno < 1:
            raise ValueError("relleno debe ser al menos 1")
        self.m, self.refinar, self.quitar_media, self.relleno = m, refinar, quitar_media, relleno

    def resolver(self, datos: Datos, gramatica: Gramatica, presupuesto: Presupuesto,
                 traza: Traza | None = None) -> Resultado:
        traza = traza or TRAZA_NULA
        c = presupuesto.nuevo_contador()
        detalle: dict = {"m": self.m, "refinar": self.refinar}
        if len(datos) < 4 or not es_rejilla_uniforme(datos):
            detalle["motivo"] = "la FFT necesita al menos 4 muestras en rejilla uniforme"
            return Resultado(None, math.inf, 0, detalle)
        ts, ys, t = datos.xs, datos.ys, datos.nombre_x
        dt = ts[1] - ts[0]
        try:
            e = espectro(ys, dt, self.quitar_media, self.relleno, c)
            ps = picos(e, self.m)
            if not ps:
                detalle["motivo"] = "el espectro no tiene ningún máximo local"
                return Resultado(None, math.inf, c.total, detalle)
            frecuencias = []
            for p in ps:
                if self.refinar == "jacobsen":
                    f = refinar_jacobsen(e, p)
                elif self.refinar == "ajuste":
                    f = refinar_por_ajuste(ts, ys, p.frecuencia, e.resolucion, contador=c)
                else:
                    f = p.frecuencia
                frecuencias.append(f)
            columnas = [[1.0] * len(ts)]
            for f in frecuencias:
                w = 2 * math.pi * f
                columnas += [[math.sin(w * x) for x in ts], [math.cos(w * x) for x in ts]]
            coefs, ecm = minimos_cuadrados(columnas, ys, 1e-9, c)
        except PresupuestoAgotado:
            return Resultado(None, math.inf, c.total, detalle, agotado=True)
        except ValueError as ex:
            detalle["motivo"] = f"las frecuencias candidatas son casi iguales: {ex}"
            return Resultado(None, math.inf, c.total, detalle)
        expr: Expr = Const(coefs[0])
        for i, f in enumerate(frecuencias):
            seno, coseno = _seno_coseno(2 * math.pi * f, t)
            expr = Op("+", (expr, Op("*", (Const(coefs[1 + 2 * i]), seno))))
            expr = Op("+", (expr, Op("*", (Const(coefs[2 + 2 * i]), coseno))))
        detalle.update({
            "frecuencias_sin_refinar": [p.frecuencia for p in ps], "frecuencias": frecuencias,
            "amplitudes": [math.hypot(coefs[1 + 2 * i], coefs[2 + 2 * i]) for i in range(len(frecuencias))],
            "constante": coefs[0], "resolucion": e.resolucion, "N": e.N,
        })
        traza.emitir("mejora", formula=a_cadena(expr), tamano=1 + 2 * len(frecuencias), error=ecm)
        return Resultado(expr, ecm, c.total, detalle)