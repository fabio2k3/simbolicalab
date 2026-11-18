"""Fase 2: matroides lineales, goloso de Rado-Edmonds, clases paralelas y selección golosa de términos."""
import math
import random

import pytest

from simbolicalab.conjuntos import datos_desde_expresion, kepler_real, kepler_sintetico
from simbolicalab.nucleo import Contador, Presupuesto, Solver
from simbolicalab.rs import Gramatica, InvarianteViolado, Var, a_cadena
from simbolicalab.rs.error import METRICAS
from simbolicalab.solvers import SolverGreedy
from simbolicalab.tecnicas import (BaseOrtonormal, MatroideLineal, Proyector, biblioteca_de_terminos, clases_paralelas,
                                   discrepancia, greedy_base, greedy_base_lineal, mejor_base_por_fuerza_bruta,
                                   mejor_subconjunto, minimos_cuadrados, oraculo_exacto, rango_exacto,
                                   reducir_biblioteca, seleccion_hacia_adelante, sistema_sin_intercambio, tabla_pd,
                                   verificar_axiomas)
from simbolicalab.tecnicas.variantes_matroides import independencia_por_pares

PLANO = [(1, 0), (0, 1), (1, 1)]                      # e1, e2, e1 + e2


def columnas_aleatorias(seed, n=7, dim=3):
    rng = random.Random(seed)
    return [tuple(rng.randint(-2, 2) for _ in range(dim)) for _ in range(n)]


def terminos_x(xs=range(1, 11), tam=3):
    d = datos_desde_expresion(Var("x"), [float(x) for x in xs])
    terminos, _ = biblioteca_de_terminos(d, Gramatica(constants=(1.0,)), tam)
    return terminos


def nombres(terminos, idx):
    return [a_cadena(terminos[i].expr) for i in idx]


# ---------------------------------------------------------------- axiomas

def test_rango_exacto_y_columnas_nulas():
    assert rango_exacto(PLANO) == 2
    assert rango_exacto([(0, 0, 0)]) == 0
    assert rango_exacto([(1, 2), (2, 4)]) == 1
    assert rango_exacto([]) == 0


def test_matroide_lineal_del_plano():
    m = MatroideLineal(PLANO)
    assert m.independiente([]) and m.independiente([0, 1]) and not m.independiente([0, 1, 2])
    assert m.rango([0, 1, 2]) == 2
    info = verificar_axiomas(m.oraculo(), 3)
    assert info == {"subconjuntos": 8, "independientes": 7, "bases": 3, "rango": 2}


def test_el_vector_cero_es_un_lazo():
    m = MatroideLineal([(0, 0), (1, 0)])
    assert not m.independiente([0]) and m.independiente([1]) and m.rango([0, 1]) == 1


@pytest.mark.parametrize("seed", range(25))
def test_matroide_lineal_cumple_los_axiomas_y_coincide_con_el_rango_exacto(seed):
    cols = columnas_aleatorias(seed)
    m = MatroideLineal(cols)
    verificar_axiomas(m.oraculo(), len(cols))
    assert discrepancia(m.oraculo(), oraculo_exacto(cols), len(cols)) is None


def test_el_vacio_debe_ser_independiente():
    with pytest.raises(InvarianteViolado, match="vacío"):
        verificar_axiomas(lambda S: False, 3)


def test_detecta_que_no_es_hereditario():
    with pytest.raises(InvarianteViolado, match="hereditario"):
        verificar_axiomas(lambda S: S in (frozenset(), frozenset({0, 1})), 2)


def test_sistema_sin_intercambio_viola_el_intercambio():
    oraculo, _, n = sistema_sin_intercambio()
    with pytest.raises(InvarianteViolado, match="intercambio"):
        verificar_axiomas(oraculo, n)


def test_verificacion_exhaustiva_tiene_limite():
    with pytest.raises(ValueError):
        verificar_axiomas(lambda S: True, 13)


# ---------------------------------------------------------------- goloso (Rado-Edmonds)

@pytest.mark.parametrize("seed", range(40))
def test_el_goloso_es_optimo_en_un_matroide_para_cualquier_costo(seed):
    cols = columnas_aleatorias(seed, n=8)
    rng = random.Random(1000 + seed)
    costos = [float(rng.randint(1, 4)) for _ in cols]                 # con muchos empates
    m = MatroideLineal(cols)
    g = greedy_base(m.oraculo(), costos)
    optimo, _ = mejor_base_por_fuerza_bruta(m.oraculo(), costos)
    assert g.costo == pytest.approx(optimo)
    assert len(g.elegidos) == rango_exacto(cols) == rango_exacto([cols[i] for i in g.elegidos])
    lineal = greedy_base_lineal(m, costos)
    assert lineal.elegidos == g.elegidos and lineal.descartados == g.descartados


def test_los_descartados_estan_en_el_espacio_de_los_elegidos_mas_baratos():
    cols = columnas_aleatorias(3, n=8)
    costos = [float(i % 3 + 1) for i in range(8)]
    m = MatroideLineal(cols)
    r = greedy_base_lineal(m, costos)
    for e in r.descartados:
        antes = [i for i in r.elegidos if (costos[i], i) < (costos[e], e)]
        assert rango_exacto([cols[i] for i in antes] + [cols[e]]) == len(antes)


def test_sin_intercambio_el_goloso_deja_de_ser_optimo():
    oraculo, costos, _ = sistema_sin_intercambio()
    g = greedy_base(oraculo, costos)
    optimo, bases = mejor_base_por_fuerza_bruta(oraculo, costos)
    assert (g.costo, optimo) == (6.0, 4.0) and bases == [frozenset({2, 3})]


def test_goloso_lineal_exige_un_costo_por_columna():
    with pytest.raises(ValueError):
        greedy_base_lineal(MatroideLineal(PLANO), [1.0])


def test_columnas_no_finitas_se_rechazan():
    with pytest.raises(ValueError):
        MatroideLineal([(1.0, math.inf)])
    with pytest.raises(ValueError):
        MatroideLineal([(1.0, 2.0), (1.0,)])


# ---------------------------------------------------------------- variantes defectuosas

def test_independencia_por_pares_pasa_los_axiomas_pero_no_es_el_matroide_lineal():
    o = independencia_por_pares(PLANO)
    verificar_axiomas(o, 3)                                              # es un matroide (de partición)...
    assert discrepancia(o, MatroideLineal(PLANO).oraculo(), 3) == frozenset({0, 1, 2})   # ...pero no el correcto
    assert len(greedy_base(o, [1.0, 1.0, 1.0]).elegidos) == 3 > rango_exacto(PLANO)
    assert len(greedy_base(MatroideLineal(PLANO).oraculo(), [1.0, 1.0, 1.0]).elegidos) == 2


def test_sin_tolerancia_el_ruido_de_punto_flotante_cuenta_como_independencia():
    v1, v2 = (0.1, 0.7, 0.3, 0.9), (0.2, 0.1, 0.8, 0.4)
    v3 = tuple(3 * a + 7 * b for a, b in zip(v1, v2))
    assert MatroideLineal([v1, v2, v3]).rango([0, 1, 2]) == 2
    assert MatroideLineal([v1, v2, v3], tol=0.0).rango([0, 1, 2]) == 3


# ---------------------------------------------------------------- clases paralelas

def test_clases_paralelas():
    cols = [(1.0, 2.0, 3.0), (2.0, 4.0, 6.0), (-1.0, -2.0, -3.0), (1.0, 2.0, 4.0), (0.0, 0.0, 0.0), (5.0, 10.0, 15.0)]
    grupos = sorted(sorted(g) for g in clases_paralelas(cols))
    assert grupos == [[0, 1, 2, 5], [3]]


def test_biblioteca_tiene_un_termino_por_firma_finita():
    ts = terminos_x()
    assert [a_cadena(t.expr) for t in ts[:3]] == ["x", "1", "sqrt(x)"]
    assert all(math.isfinite(v) for t in ts for v in t.columna)
    assert len({t.columna for t in ts}) == len(ts)
    d = datos_desde_expresion(Var("x"), [float(x) for x in range(1, 11)])
    assert len(ts) == sum(n.representantes for n in tabla_pd(d, Gramatica(constants=(1.0,)), 3).niveles)


def test_reducir_paralelas_conserva_el_mas_barato_de_cada_clase():
    ts = terminos_x()
    idx = reducir_biblioteca(ts, "paralelas")
    assert len(idx) < len(ts)
    for i in set(range(len(ts))) - set(idx):
        grupo = [j for j in idx if any(set(g) >= {i, j} for g in clases_paralelas([t.columna for t in ts]))]
        if grupo:
            assert ts[grupo[0]].costo <= ts[i].costo
    assert "x + x" not in nombres(ts, idx) and "x - x" not in nombres(ts, idx)


def test_reducir_base_conserva_el_espacio_generado():
    ts = terminos_x()
    idx = reducir_biblioteca(ts, "base")
    b = BaseOrtonormal()
    for i in idx:
        assert b.intentar(ts[i].columna)
    for i in set(range(len(ts))) - set(idx):
        assert not b.intentar(ts[i].columna)                              # todo descartado ya está en el espacio
    assert len(idx) == MatroideLineal([t.columna for t in ts]).rango(range(len(ts)))


def test_reducir_modo_desconocido():
    with pytest.raises(ValueError):
        reducir_biblioteca(terminos_x(), "nada")


# ---------------------------------------------------------------- ajuste lineal y selección golosa

def test_minimos_cuadrados_recupera_los_coeficientes():
    a, b = [1.0, 2.0, 3.0, 4.0, 5.0], [1.0, 4.0, 9.0, 16.0, 25.0]
    y = [2 * u + 3 * v for u, v in zip(a, b)]
    coefs, ecm = minimos_cuadrados([a, b], y)
    assert coefs == pytest.approx([2.0, 3.0]) and ecm < 1e-24
    with pytest.raises(ValueError):
        minimos_cuadrados([a, [2 * u for u in a]], y)


def test_proyector_ganancia_igual_a_la_bajada_real_del_error():
    ts = terminos_x()
    y = [3.0 * v + 1.0 for v in ts[0].columna]
    p = Proyector(y)
    for t in ts[2:6]:
        antes = p.error * len(y)
        g = p.ganancia(t.columna)
        if p.agregar(t.columna):
            assert antes - p.error * len(y) == pytest.approx(g, rel=1e-9, abs=1e-12)
        else:
            assert g == 0.0


def test_con_k_1_el_goloso_es_optimo():
    ts = terminos_x()
    cols = [t.columna for t in ts]
    y = [2 * a + 3 * b for a, b in zip(ts[0].columna, ts[2].columna)]
    s = seleccion_hacia_adelante(cols, y, 1)
    _, e = mejor_subconjunto(cols, y, 1)
    assert s.error == pytest.approx(e, rel=1e-9)


def test_la_seleccion_golosa_por_error_no_es_optima_para_k_2():
    ts = terminos_x()
    cols = [t.columna for t in ts]
    y = [2 * a + 3 * b for a, b in zip(ts[0].columna, ts[2].columna)]     # y = 2x + 3 sqrt(x)
    s = seleccion_hacia_adelante(cols, y, 2)
    idx, e = mejor_subconjunto(cols, y, 2)
    assert sorted(nombres(ts, idx)) == ["sqrt(x)", "x"] and e < 1e-20
    assert nombres(ts, s.indices) == ["x + 1", "x * x"] and s.error > 0.01


def test_los_errores_por_paso_no_crecen_y_k_grande_se_detiene_en_el_rango():
    ts = terminos_x()
    cols = [t.columna for t in ts]
    y = [math.sin(v) + v for v in ts[0].columna]
    s = seleccion_hacia_adelante(cols, y, 50)
    assert all(b <= a + 1e-12 for a, b in zip(s.errores, s.errores[1:]))
    assert len(s.indices) <= MatroideLineal(cols).rango(range(len(cols)))
    with pytest.raises(ValueError):
        seleccion_hacia_adelante(cols, y, 0)


def test_mejor_subconjunto_tiene_limite():
    cols = [tuple(float(i + j * j) for j in range(5)) for i in range(40)]
    with pytest.raises(ValueError):
        mejor_subconjunto(cols, [1.0] * 5, 12)


# ---------------------------------------------------------------- las dos reducciones

def test_paralelas_no_pierde_ninguna_solucion_dispersa():
    ts = terminos_x()
    cols = [t.columna for t in ts]
    idx = reducir_biblioteca(ts, "paralelas")
    reducida = [cols[i] for i in idx]
    rng = random.Random(0)
    leyes = [[2 * a + 3 * b for a, b in zip(cols[0], cols[2])], [a + 1 for a in cols[0]],
             [rng.uniform(-5, 5) for _ in cols[0]]]
    for y in leyes:
        for k in (1, 2):
            assert mejor_subconjunto(reducida, y, k)[1] == pytest.approx(mejor_subconjunto(cols, y, k)[1], rel=1e-8, abs=1e-18)


def test_la_base_conserva_el_ajuste_sin_limite_de_terminos_pero_pierde_soluciones_dispersas():
    ts = terminos_x()
    cols = [t.columna for t in ts]
    base = reducir_biblioteca(ts, "base")
    y = [a + 1 for a in cols[0]]                                          # y = x + 1, un solo término de la biblioteca
    completa, reducida = Proyector(y), Proyector(y)
    for c in cols:
        completa.agregar(c)
    for i in base:
        reducida.agregar(cols[i])
    assert reducida.error == pytest.approx(completa.error, abs=1e-20)     # mismo espacio, mismo ajuste libre
    assert seleccion_hacia_adelante(cols, y, 1).error < 1e-20             # con k = 1 la biblioteca completa acierta
    assert seleccion_hacia_adelante([cols[i] for i in base], y, 1).error > 0.1   # y la base ya no


def test_la_base_arregla_el_caso_donde_el_goloso_elige_un_compuesto():
    ts = terminos_x()
    cols = [t.columna for t in ts]
    base = reducir_biblioteca(ts, "base")
    y = [2 * a + 3 * b for a, b in zip(cols[0], cols[2])]
    s = seleccion_hacia_adelante([cols[i] for i in base], y, 2)
    assert s.error < 1e-20 and sorted(nombres(ts, [base[i] for i in s.indices])) == ["sqrt(x)", "x"]


# ---------------------------------------------------------------- solver

def test_solver_goloso_cumple_el_contrato():
    assert isinstance(SolverGreedy(1, 3), Solver)


def test_solver_goloso_encuentra_la_ley_de_kepler():
    d = kepler_real()
    g = Gramatica(variables=(d.nombre_x,))
    r = SolverGreedy(1, 5).resolver(d, g, Presupuesto(None))
    assert r.detalle["terminos"] == ["a * sqrt(a)"]
    assert r.detalle["coeficientes"][0] == pytest.approx(1.0, abs=0.01)
    assert METRICAS["ecm"](r.expresion, d) == pytest.approx(r.error, rel=1e-9, abs=1e-12)
    assert r.error < 1e-3 and not r.agotado


def test_solver_goloso_la_biblioteca_se_reduce_sin_cambiar_la_respuesta():
    d = kepler_real()
    g = Gramatica(variables=(d.nombre_x,))
    a = SolverGreedy(2, 5, "ninguna").resolver(d, g, Presupuesto(None))
    b = SolverGreedy(2, 5, "paralelas").resolver(d, g, Presupuesto(None))
    assert a.detalle["terminos"] == b.detalle["terminos"] and a.error == pytest.approx(b.error, rel=1e-9)
    assert b.detalle["terminos_tras_reducir"] < a.detalle["terminos_tras_reducir"] and b.operaciones < a.operaciones


def test_con_pocos_datos_la_base_pierde_el_termino_verdadero():
    d = kepler_real()                                                      # 8 puntos: el rango no pasa de 8
    g = Gramatica(variables=(d.nombre_x,))
    base = SolverGreedy(2, 5, "base").resolver(d, g, Presupuesto(None))
    par = SolverGreedy(2, 5, "paralelas").resolver(d, g, Presupuesto(None))
    assert base.detalle["terminos_tras_reducir"] <= len(d)
    assert "a * sqrt(a)" not in base.detalle["terminos"] and base.error > 100 * par.error


def test_solver_goloso_sobre_kepler_sintetico_es_reproducible():
    d = kepler_sintetico(30, 0.02, 4)
    g = Gramatica(variables=(d.nombre_x,))
    a = SolverGreedy(1, 4).resolver(d, g, Presupuesto(None))
    b = SolverGreedy(1, 4).resolver(kepler_sintetico(30, 0.02, 4), g, Presupuesto(None))
    assert a.detalle["terminos"] == b.detalle["terminos"] == ["a * sqrt(a)"] and a.error == b.error


def test_solver_goloso_con_presupuesto_agotado():
    d = kepler_real()
    r = SolverGreedy(2, 6).resolver(d, Gramatica(variables=(d.nombre_x,)), Presupuesto(100))
    assert r.agotado and r.expresion is None and math.isinf(r.error)


def test_solver_goloso_parametros_invalidos():
    for kw in ({"k": 0, "max_tam": 3}, {"k": 1, "max_tam": 0}, {"k": 1, "max_tam": 3, "reduccion": "nada"}):
        with pytest.raises(ValueError):
            SolverGreedy(**kw)