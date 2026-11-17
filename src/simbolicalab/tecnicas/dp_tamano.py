"""Programación dinámica por tamaño sobre árboles de expresión.

El estado de una subexpresión es su vector de valores en los datos (su firma), no su error: dos subexpresiones con
la misma firma son intercambiables dentro de cualquier fórmula mayor, así que basta un representante por firma
(el más pequeño). Quedarse solo con las de menor error por tamaño (ancho) rompe esa propiedad.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

from ..nucleo.contador import Contador, PresupuestoAgotado
from ..nucleo.traza import TRAZA_NULA, Traza
from ..rs.datos import Datos
from ..rs.expresion import Const, Expr, Op, Var, a_cadena, evaluar, tamano
from ..rs.gramatica import Gramatica
from ..rs.invariantes import InvarianteViolado, bien_formada
from ..rs.operadores import OPERADORES

Firma = tuple[float, ...]            # puede contener inf, nunca NaN
TOLERANCIA_RELATIVA = 1e-9           # misma regla de mejora que SolverFuerzaBruta
TOLERANCIA_ABSOLUTA = 1e-12


def mejora_de_verdad(nuevo: float, actual: float) -> bool:
    if math.isinf(actual):
        return nuevo < actual
    return nuevo < actual - max(TOLERANCIA_RELATIVA * actual, TOLERANCIA_ABSOLUTA)


def aplicar(nombre: str, *args: float) -> float:
    """Misma semántica que evaluar: los fallos numéricos dan NaN."""
    try:
        return OPERADORES[nombre].function(*args)
    except (OverflowError, ZeroDivisionError, ValueError):
        return math.nan


def firma_vectorial(e: Expr, nombre_x: str, xs: Sequence[float]) -> Firma | None:
    """Firma por evaluación directa del árbol (referencia). None si algún valor es NaN."""
    f = tuple(evaluar(e, {nombre_x: x}) for x in xs)
    return None if any(math.isnan(v) for v in f) else f


def error_de_firma(f: Firma, ys: Sequence[float], metrica: str) -> float:
    """Calcula el error con el mismo orden de sumas que rs.error, así que da el mismo valor exacto."""
    total = 0.0
    if metrica == "ecm":
        for v, y in zip(f, ys):
            d = v - y
            total += d * d
        err = total / len(ys)
    elif metrica == "relativo":
        if any(y == 0 for y in ys):
            raise ValueError("el error relativo no está definido si algún y es 0")
        for v, y in zip(f, ys):
            total += abs(v - y) / abs(y)
        err = total / len(ys)
    else:
        raise ValueError(f"métrica desconocida: {metrica!r}")
    return err if math.isfinite(err) else math.inf


def _redondear(f: Firma, cifras: int | None) -> Firma:
    if cifras is None:
        return f
    return tuple(v if math.isinf(v) else float(f"{v:.{cifras}g}") for v in f)


@dataclass
class Nivel:
    tamano: int
    generadas: int = 0
    representantes: int = 0
    descartadas: int = 0            # firma ya vista en este tamaño o en uno menor
    podadas_por_ancho: int = 0
    operaciones: int = 0
    mejor_error: float = math.inf
    mejor_formula: str | None = None


@dataclass
class TablaPD:
    niveles: list[Nivel] = field(default_factory=list)
    representantes: list[list[tuple[Expr, Firma, float]]] = field(default_factory=lambda: [[]])
    mejor: Expr | None = None
    mejor_error: float = math.inf
    agotado: bool = False
    mejor_por_tamano: dict[int, tuple[Expr, float]] = field(default_factory=dict)

    def frente_de_pareto(self) -> list[tuple[int, Expr, float]]:
        """Tamaños donde el mejor error acumulado mejora de verdad: el equilibrio entre error y complejidad."""
        frente, actual = [], math.inf
        for s in sorted(self.mejor_por_tamano):
            e, err = self.mejor_por_tamano[s]
            if mejora_de_verdad(err, actual):
                frente.append((s, e, err))
                actual = err
        return frente


def costo_predicho(reps: Sequence[int], n_terminales: int, n_unarios: int, n_binarios: int, n_puntos: int,
                   max_tam: int) -> int:
    """Operaciones previstas dado el número de representantes por tamaño (reps[s], con reps[0] sin usar).

    Cada candidata cuesta 1 de construcción, 1 de acceso al hash y n_puntos de nodo, se descarte o no.
    """
    total = n_terminales * (n_puntos + 2)
    for s in range(2, max_tam + 1):
        cand = n_unarios * reps[s - 1] + n_binarios * sum(reps[k] * reps[s - 1 - k] for k in range(1, s - 1))
        total += cand * (n_puntos + 2)
    return total


def tabla_pd(datos: Datos, g: Gramatica, max_tam: int, metrica: str = "ecm", contador: Contador | None = None,
             traza: Traza | None = None, cifras: int | None = None, ancho: int | None = None,
             vigilar: bool = False) -> TablaPD:
    if max_tam < 1:
        raise ValueError("max_tam debe ser al menos 1")
    if ancho is not None and ancho < 1:
        raise ValueError("ancho debe ser al menos 1 (o None para no podar)")
    c = contador if contador is not None else Contador()
    traza = traza or TRAZA_NULA
    xs, ys, nx = datos.xs, datos.ys, datos.nombre_x
    n = len(xs)
    t = TablaPD()
    vistas: set[Firma] = set()

    def registrar(nivel: Nivel, e: Expr, f: Firma) -> bool:
        clave = _redondear(f, cifras)
        if clave in vistas:
            nivel.descartadas += 1
            return False
        vistas.add(clave)
        err = error_de_firma(f, ys, metrica)
        t.representantes[-1].append((e, f, err))
        nivel.representantes += 1
        if err < nivel.mejor_error:
            nivel.mejor_error, nivel.mejor_formula = err, a_cadena(e)
        return True

    try:
        for s in range(1, max_tam + 1):
            nivel = Nivel(s)
            t.niveles.append(nivel)
            t.representantes.append([])
            antes = c.total
            try:
                if s == 1:
                    for term in g.terminales:
                        c.tick(1, "construccion")
                        c.tick(1, "acceso_hash")
                        c.tick(n, "nodo")
                        nivel.generadas += 1
                        f = tuple(evaluar(term, {nx: x}) for x in xs)
                        registrar(nivel, term, f)
                else:
                    for nombre in g.unarios:
                        for h, fh, _ in t.representantes[s - 1]:
                            c.tick(1, "construccion")
                            c.tick(1, "acceso_hash")
                            c.tick(n, "nodo")
                            nivel.generadas += 1
                            f = tuple(aplicar(nombre, v) for v in fh)
                            if any(math.isnan(v) for v in f):
                                nivel.descartadas += 1
                                continue
                            registrar(nivel, Op(nombre, (h,)), f)
                    for k in range(1, s - 1):
                        for izq, fi, _ in t.representantes[k]:
                            for der, fd, _ in t.representantes[s - 1 - k]:
                                for nombre in g.binarios:
                                    c.tick(1, "construccion")
                                    c.tick(1, "acceso_hash")
                                    c.tick(n, "nodo")
                                    nivel.generadas += 1
                                    f = tuple(aplicar(nombre, a, b) for a, b in zip(fi, fd))
                                    if any(math.isnan(v) for v in f):
                                        nivel.descartadas += 1
                                        continue
                                    registrar(nivel, Op(nombre, (izq, der)), f)
            finally:
                nivel.operaciones = c.total - antes
                _actualizar_mejor(t, nivel, traza, s)

            if ancho is not None and len(t.representantes[s]) > ancho:
                ordenadas = sorted(t.representantes[s], key=lambda r: r[2])
                nivel.podadas_por_ancho = len(ordenadas) - ancho
                t.representantes[s] = ordenadas[:ancho]
                nivel.representantes = ancho
            if vigilar:
                _vigilar(t, g, s, nx, xs, cifras)
            traza.emitir("nivel", tamano=s, generadas=nivel.generadas, representantes=nivel.representantes,
                         descartadas=nivel.descartadas, mejor_error=nivel.mejor_error)
    except PresupuestoAgotado:
        t.agotado = True
    return t


def _actualizar_mejor(t: TablaPD, nivel: Nivel, traza: Traza, s: int) -> None:
    for e, _, err in t.representantes[s]:
        if s not in t.mejor_por_tamano or err < t.mejor_por_tamano[s][1]:
            t.mejor_por_tamano[s] = (e, err)
        if mejora_de_verdad(err, t.mejor_error):
            t.mejor, t.mejor_error = e, err
            traza.emitir("mejora", formula=a_cadena(e), tamano=s, error=err)


def _vigilar(t: TablaPD, g: Gramatica, s: int, nx: str, xs: Sequence[float], cifras: int | None) -> None:
    claves: set[Firma] = set()
    for e, f, _ in t.representantes[s]:
        if tamano(e) != s:
            raise InvarianteViolado(f"representante de tamaño {tamano(e)} en el nivel {s}: {a_cadena(e)}")
        if not bien_formada(e, g):
            raise InvarianteViolado(f"representante mal formado: {e!r}")
        directa = tuple(evaluar(e, {nx: x}) for x in xs)
        if directa != f:
            raise InvarianteViolado(f"la firma vectorial no coincide con evaluar el árbol en {a_cadena(e)}")
        clave = _redondear(f, cifras)
        if clave in claves:
            raise InvarianteViolado(f"dos representantes con la misma firma en el nivel {s}: {a_cadena(e)}")
        claves.add(clave)


def verificar_cobertura(datos: Datos, g: Gramatica, max_tam: int, cifras: int | None = None) -> dict[str, int]:
    """El PD no pierde ninguna función: sus representantes cubren exactamente las firmas de la fuerza bruta.

    Compara el conjunto de firmas de todas las fórmulas de tamaño <= max_tam con el de los representantes.
    """
    from ..rs.enumerador import enumerar
    brutas: set[Firma] = set()
    formulas = 0
    for e in enumerar(g, max_tam):
        formulas += 1
        f = firma_vectorial(e, datos.nombre_x, datos.xs)
        if f is not None:
            brutas.add(_redondear(f, cifras))
    t = tabla_pd(datos, g, max_tam, cifras=cifras)
    pd = {_redondear(f, cifras) for nivel in t.representantes for _, f, _ in nivel}
    if brutas != pd:
        raise InvarianteViolado(f"el PD cubre {len(pd)} firmas y la fuerza bruta {len(brutas)}; "
                                f"faltan {len(brutas - pd)} y sobran {len(pd - brutas)}")
    return {"formulas": formulas, "firmas_distintas": len(brutas), "representantes": len(pd)}