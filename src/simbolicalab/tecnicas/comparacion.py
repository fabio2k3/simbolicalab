
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Mapping, Sequence

from ..rs.datos import Datos
from ..rs.error import error_cuadratico_medio
from ..rs.expresion import Const, Expr, Op, Var, a_cadena, tamano
from ..rs.gramatica import Gramatica
from ..conjuntos import (contraejemplo_de_la_poda, datos_desde_expresion, kepler_sintetico, kepler_real, oscilador_sintetico)
from ..nucleo.contrato import Presupuesto

@dataclass(frozen=True)
class Benchmark:
    nombre: str
    datos: Datos
    gramatica: Gramatica
    descripcion: str
    prueba: Datos | None = None       


@dataclass(frozen=True)
class Fila:
    benchmark: str
    solver: str
    formula: str | None
    tamano: int | None
    error: float
    error_relativo: float               
    error_prueba: float | None          
    error_prueba_relativo: float | None
    operaciones: int
    agotado: bool


def varianza(ys: Sequence[float]) -> float:
    m = sum(ys) / len(ys)
    return sum((y - m) ** 2 for y in ys) / len(ys)


def _recortar(d: Datos, desde: int, nombre: str) -> Datos:
    return Datos(xs=d.xs[desde:], ys=d.ys[desde:], nombre_x=d.nombre_x, nombre=nombre, ley_oculta=d.ley_oculta)


def _dos_tonos(n: int = 256, semilla: int = 0) -> Datos:
    rng = random.Random(semilla)
    ts = [0.1 * k for k in range(n)]
    ys = [1 + math.sin(2 * math.pi * 0.7 * t) + 0.5 * math.sin(2 * math.pi * 2.3 * t) + rng.gauss(0, 0.05) for t in ts]
    return Datos(xs=tuple(ts), ys=tuple(ys), nombre_x="t", nombre="Dos tonos con constante (0.7 y 2.3)",
                 ley_oculta="1 + sin(2 pi 0.7 t) + 0.5 sin(2 pi 2.3 t)")


def _dos_terminos(xs: Sequence[float]) -> Datos:
    x = Var("x")
    ley = Op("+", (Op("*", (Const(2.0), x)), Op("*", (Const(3.0), Op("sqrt", (x,))))))
    return datos_desde_expresion(ley, [float(i) for i in xs], "x", "Ley de dos términos: y = 2x + 3 sqrt(x)")


def benchmarks() -> list[Benchmark]:
    def g(d: Datos) -> Gramatica:
        return Gramatica(variables=(d.nombre_x,))

    kepler = kepler_real()
    ks = kepler_sintetico(30, 0.02, 1)
    contra = contraejemplo_de_la_poda()
    contra_prueba = datos_desde_expresion(
        Op("sqrt", (Op("+", (Var("x"), Const(1.0))),)), [float(i) for i in range(9, 17)], "x", "sqrt(x + 1) más allá")
    dos = _dos_terminos(range(1, 11))
    osc = oscilador_sintetico()
    osc_prueba = _recortar(oscilador_sintetico(n=256, semilla=7), 128, "Oscilador, tiempos posteriores")
    tonos = _dos_tonos()
    tonos_prueba = _recortar(_dos_tonos(512, 1), 256, "Dos tonos, tiempos posteriores")
    amort = oscilador_sintetico(amortiguamiento=0.2, ruido=0.02)
    amort_prueba = _recortar(oscilador_sintetico(n=256, amortiguamiento=0.2, ruido=0.02, semilla=7), 128,
                             "Amortiguado, tiempos posteriores")
    
    return [
        Benchmark("kepler_real", kepler, g(kepler), "Ocho planetas: a * sqrt(a)"),
        Benchmark("kepler_sintetico", ks, g(ks), "Treinta puntos con 2 % de ruido multiplicativo",
                  kepler_sintetico(30, 0.02, 99)),
        Benchmark("contraejemplo_poda", contra, g(contra), "sqrt(x + 1): la poda por error lo pierde", contra_prueba),
        Benchmark("dos_terminos", dos, g(dos), "2x + 3 sqrt(x): la selección golosa elige un compuesto",
                  _dos_terminos(range(11, 21))),
        Benchmark("oscilador", osc, g(osc), "2 sin(pi t) en rejilla uniforme, con ruido", osc_prueba),
        Benchmark("dos_tonos", tonos, g(tonos), "Dos frecuencias y una constante", tonos_prueba),
        Benchmark("oscilador_amortiguado", amort, g(amort), "Un tono que decae: no es un tono puro", amort_prueba),
    ]


def error_en(modelo: Expr | float | None, datos: Datos) -> float:
    if modelo is None:
        return math.inf
    
    if isinstance(modelo, Expr):
        e = error_cuadratico_medio(modelo, datos)
        return e if math.isfinite(e) else math.inf
    
    return sum((y - modelo) ** 2 for y in datos.ys) / len(datos)



def _relativo(error: float, ys: Sequence[float]) -> float:
    if not math.isfinite(error):
        return math.inf
    
    v = varianza(ys)
    return error / v if v > 0 else (0.0 if error == 0 else math.inf)


def comparar(bench: Sequence[Benchmark], solvers: Mapping[str, object], presupuesto: Presupuesto) -> list[Fila]:
    filas = []
    for b in bench:
        for nombre, solver in solvers.items():
            r = solver.resolver(b.datos, b.gramatica, presupuesto)
            e = r.expresion
            if isinstance(e, Expr):
                formula, tam = a_cadena(e), tamano(e)
            elif e is None:
                formula, tam = None, None
            else:
                formula, tam = f"{e:.6g}", 1
            ep = error_en(e, b.prueba) if b.prueba is not None else None
            filas.append(Fila(b.nombre, nombre, formula, tam, r.error, _relativo(r.error, b.datos.ys), ep,
                              None if ep is None else _relativo(ep, b.prueba.ys), r.operaciones, r.agotado))
    return filas


def ganadores(filas: Sequence[Fila], tolerancia: float = 1e-6, fuera_de_muestra: bool = True) -> dict[str, str]:
    def e(f: Fila) -> float:
        return f.error_prueba if fuera_de_muestra and f.error_prueba is not None else f.error

    res: dict[str, str] = {}
    for nombre in dict.fromkeys(f.benchmark for f in filas):
        fs = [f for f in filas if f.benchmark == nombre and math.isfinite(e(f))]
        if not fs:
            continue
        mejor = min(e(f) for f in fs)
        empatados = [f for f in fs if e(f) <= mejor * (1 + tolerancia) + 1e-12]
        res[nombre] = min(empatados, key=lambda f: (f.operaciones, f.solver)).solver
        
    return res