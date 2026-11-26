from __future__ import annotations

import math

from ..conjuntos.oscilador import es_rejilla_uniforme
from ..nucleo.contador import PresupuestoAgotado
from ..nucleo.contrato import Presupuesto, Resultado
from ..nucleo.traza import TRAZA_NULA, Traza
from ..rs.datos import Datos
from ..rs.expresion import Const, Op, Var, a_cadena, tamano
from ..rs.gramatica import Gramatica
from ..tecnicas.ajuste_lineal import minimos_cuadrados, seleccion_hacia_adelante
from ..tecnicas.analisis_espectral import espectro, picos, refinar_jacobsen, refinar_por_ajuste
from ..tecnicas.biblioteca import REDUCCIONES, Termino, biblioteca_de_terminos, reducir_biblioteca
from ..tecnicas.fourier import es_potencia_de_dos
from ..tecnicas.seleccion_modelo import eliminacion_hacia_atras, elegir_k, piso_de_error
from .greedy import combinacion_lineal

CRITERIOS = ("ebic", "bic", "ninguno")
REFINADOS = ("auto", "ninguno", "jacobsen", "ajuste")


class SolverCombinado:
    """
    1. PD por tamaño: biblioteca de términos de la gramática, un representante por firma.
    2. FFT (si los datos están en rejilla uniforme): sin(w t) y cos(w t) para las frecuencias de los picos.
    3. Reducción de la biblioteca (clases paralelas por defecto: no pierde soluciones dispersas).
    4. Selección golosa de hasta k_max términos por reducción de error.
    5. Cuántos términos: el de menor BIC extendido (ebic), que cuenta el tamaño de la biblioteca; con "bic" se ignora y
       se sobreajusta. Después, eliminación hacia atrás de los que sobran. Coeficientes por mínimos cuadrados.

    La salida es una combinación lineal con coeficientes ajustados, como la de SolverGoloso.
    """

    nombre = "combinado"

    def __init__(self, max_tam: int = 4, k_max: int = 5, espectral: bool = True, m_frecuencias: int = 2,
                 umbral: float = 0.25, refinar: str = "auto", reduccion: str = "paralelas", criterio: str = "ebic",
                 eliminar: bool = True, min_ciclos: float = 2.0, cifras: int | None = None, tol: float = 1e-9) -> None:
        
        if max_tam < 1:
            raise ValueError("max_tam debe ser al menos 1")
        if k_max < 1:
            raise ValueError("k_max debe ser al menos 1")
        if m_frecuencias < 1:
            raise ValueError("m_frecuencias debe ser al menos 1")
        if refinar not in REFINADOS:
            raise ValueError(f"refinado desconocido: {refinar!r}; opciones: {REFINADOS}")
        if reduccion not in REDUCCIONES:
            raise ValueError(f"reducción desconocida: {reduccion!r}; opciones: {REDUCCIONES}")
        if min_ciclos < 0:
            raise ValueError("min_ciclos no puede ser negativo")
        if criterio not in CRITERIOS:
            raise ValueError(f"criterio desconocido: {criterio!r}; opciones: {CRITERIOS}")
        
        self.max_tam, self.k_max, self.espectral, self.m_frecuencias, self.umbral = max_tam, k_max, espectral, m_frecuencias, umbral
        self.refinar, self.reduccion, self.criterio, self.cifras, self.tol = refinar, reduccion, criterio, cifras, tol
        self.eliminar, self.min_ciclos = eliminar, min_ciclos


    def _terminos_espectrales(self, datos: Datos, c) -> tuple[list[Termino], list[float]]:
        ts, ys = datos.xs, datos.ys
        dt = ts[1] - ts[0]
        e = espectro(ys, dt, contador=c)
        refinar = self.refinar

        if refinar == "auto":
            refinar = "jacobsen" if es_potencia_de_dos(len(ys)) else "ajuste"

        frecuencias = []
        for p in picos(e, self.m_frecuencias, self.umbral, self.min_ciclos / (len(ys) * dt)):
            if refinar == "jacobsen":
                frecuencias.append(refinar_jacobsen(e, p))
            elif refinar == "ajuste":
                frecuencias.append(refinar_por_ajuste(ts, ys, p.frecuencia, e.resolucion, contador=c))
            else:
                frecuencias.append(p.frecuencia)

        terminos = []
        for f in frecuencias:
            w = 2 * math.pi * f
            arg = Op("*", (Const(w), Var(datos.nombre_x)))
            for expr, fn in ((Op("sin", (arg,)), math.sin), (Op("cos", (arg,)), math.cos)):
                terminos.append(Termino(expr, tuple(fn(w * t) for t in ts), tamano(expr)))

        return terminos, frecuencias



    def resolver(self, datos: Datos, gramatica: Gramatica, presupuesto: Presupuesto, traza: Traza | None = None) -> Resultado:
        traza = traza or TRAZA_NULA
        c = presupuesto.nuevo_contador()
        detalle: dict = {"max_tam": self.max_tam, "k_max": self.k_max, "criterio": self.criterio,
                         "reduccion": self.reduccion}
        try:
            terminos, t = biblioteca_de_terminos(datos, gramatica, self.max_tam, self.cifras, c)
            if t.agotado:
                return Resultado(None, math.inf, c.total, detalle, agotado=True)
            
            detalle["terminos_de_la_gramatica"] = len(terminos)
            frecuencias: list[float] = []
            if self.espectral and len(datos) >= 8 and es_rejilla_uniforme(datos):
                espectrales, frecuencias = self._terminos_espectrales(datos, c)
                terminos = terminos + espectrales

            detalle["terminos_espectrales"] = len(terminos) - detalle["terminos_de_la_gramatica"]
            detalle["frecuencias"] = frecuencias

            idx = reducir_biblioteca(terminos, self.reduccion, self.tol, c)
            detalle["terminos_tras_reducir"] = len(idx)
            cols = [terminos[i].columna for i in idx]
            sel = seleccion_hacia_adelante(cols, datos.ys, self.k_max, [float(terminos[i].costo) for i in idx], self.tol, c)
            if not sel.indices:
                return Resultado(None, math.inf, c.total, detalle)
            
            m_lib = len(idx) if self.criterio == "ebic" else 0
            if self.criterio != "ninguno":
                k, bics = elegir_k(sel.errores, len(datos.ys), piso_de_error(datos.ys), m_lib)
                detalle["bic"] = bics
            else:
                k = len(sel.indices)

            cols_idx = list(sel.indices[:k])
            if self.criterio != "ninguno" and self.eliminar:
                cols_idx, _ = eliminacion_hacia_atras(cols, datos.ys, cols_idx, piso_de_error(datos.ys), self.tol, c, m_lib)

            elegidos = [idx[i] for i in cols_idx]
            coefs, ecm = minimos_cuadrados([terminos[i].columna for i in elegidos], datos.ys, self.tol, c)

        except PresupuestoAgotado:
            return Resultado(None, math.inf, c.total, detalle, agotado=True)
        
        expr = combinacion_lineal(coefs, [terminos[i].expr for i in elegidos])
        detalle.update({"k_antes_de_eliminar": k, "k": len(elegidos), "terminos": [a_cadena(terminos[i].expr) for i in elegidos], "coeficientes": coefs,
                        "error_por_paso": list(sel.errores)})
        traza.emitir("mejora", formula=a_cadena(expr), tamano=k, error=ecm)
        
        return Resultado(expr, ecm, c.total, detalle)