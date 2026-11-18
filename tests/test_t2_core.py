"""Fase 0: operadores sin/cos, semilla de Kepler y dataset oscilador."""
import math

import pytest

from simbolicalab.conjuntos import es_rejilla_uniforme, kepler_real, kepler_sintetico, oscilador_sintetico
from simbolicalab.rs import (Const, Gramatica, OPERADORES, Op, Var, a_cadena, contar_por_size, enumerar, evaluar,
                             verificar_enumeracion)
from simbolicalab.rs.error import error_cuadratico_medio


# ---------- sin / cos ----------

def test_sin_cos_registrados():
    assert OPERADORES["sin"].aridad == 1 and OPERADORES["cos"].aridad == 1
    assert not OPERADORES["sin"].infijo and not OPERADORES["cos"].conmutativo


def test_evaluar_sin_cos():
    x = Var("x")
    assert evaluar(Op("sin", (x,)), {"x": 0.0}) == 0.0
    assert evaluar(Op("cos", (x,)), {"x": 0.0}) == 1.0
    assert evaluar(Op("sin", (x,)), {"x": math.pi / 2}) == pytest.approx(1.0)
    assert evaluar(Op("cos", (x,)), {"x": math.pi}) == pytest.approx(-1.0)


@pytest.mark.parametrize("nombre", ["sin", "cos"])
@pytest.mark.parametrize("valor", [math.inf, -math.inf, math.nan])
def test_sin_cos_no_finitos_dan_nan(nombre, valor):
    assert math.isnan(evaluar(Op(nombre, (Var("x"),)), {"x": valor}))


def test_a_cadena_sin():
    assert a_cadena(Op("sin", (Var("x"),))) == "sin(x)"
    assert a_cadena(Op("cos", (Op("*", (Const(2.0), Var("x"))),))) == "cos((2 * x))"


def test_gramatica_acepta_sin_cos():
    g = Gramatica(unarios=("sin", "cos"))
    assert g.unarios == ("sin", "cos")


def test_enumerador_con_sin_cos_cumple_invariantes():
    g = Gramatica(unarios=("sqrt", "sin", "cos"))
    esperado = contar_por_size(g, 5)
    por_nivel = verificar_enumeracion(g, 5)
    assert all(por_nivel[s] == esperado[s] for s in range(1, 6))
    assert sum(1 for _ in enumerar(g, 5)) == sum(esperado)


def test_gramatica_por_defecto_no_cambia():
    g = Gramatica()
    assert g.unarios == ("sqrt",)
    assert contar_por_size(g, 3)[1:] == [3, 3, 39]


# ---------- semilla de Kepler ----------

def test_kepler_sintetico_reproducible_con_semilla():
    a = kepler_sintetico(n=20, ruido=0.05, semilla=7)
    b = kepler_sintetico(n=20, ruido=0.05, semilla=7)
    assert a.xs == b.xs and a.ys == b.ys


def test_kepler_sintetico_semillas_distintas_difieren():
    a = kepler_sintetico(n=20, ruido=0.05, semilla=1)
    b = kepler_sintetico(n=20, ruido=0.05, semilla=2)
    assert a.xs != b.xs or a.ys != b.ys


def test_kepler_sintetico_semilla_por_defecto_reproducible():
    assert kepler_sintetico().ys == kepler_sintetico().ys


# ---------- oscilador ----------

def test_oscilador_forma_y_rejilla():
    d = oscilador_sintetico(n=64)
    assert len(d) == 64 and d.nombre_x == "t" and d.ley_oculta
    assert d.xs[0] == 0.0
    assert es_rejilla_uniforme(d)


def test_oscilador_reproducible_y_semillas():
    assert oscilador_sintetico(semilla=3).ys == oscilador_sintetico(semilla=3).ys
    assert oscilador_sintetico(semilla=3).ys != oscilador_sintetico(semilla=4).ys


def test_oscilador_sin_ruido_coincide_con_la_ley():
    d = oscilador_sintetico(n=64, ruido=0.0, amplitud=2.0, frecuencia=0.5)
    ley = Op("*", (Const(2.0), Op("sin", (Op("*", (Const(2 * math.pi * 0.5), Var("t"))),))))
    assert error_cuadratico_medio(ley, d) < 1e-20


def test_oscilador_amortiguado_sin_ruido_coincide_con_la_ley():
    d = oscilador_sintetico(n=64, ruido=0.0, amortiguamiento=0.1)
    w = Const(2 * math.pi * 0.5)
    decaimiento = Op("exp", (Op("neg", (Op("*", (Const(0.1), Var("t"))),)),))
    ley = Op("*", (Const(2.0), Op("*", (decaimiento, Op("sin", (Op("*", (w, Var("t"))),))))))
    assert error_cuadratico_medio(ley, d) < 1e-20


def test_oscilador_ruido_es_aditivo_con_la_desviacion_pedida():
    limpio = oscilador_sintetico(n=4000, ruido=0.0)
    sucio = oscilador_sintetico(n=4000, ruido=0.1, semilla=1)
    resid = [b - a for a, b in zip(limpio.ys, sucio.ys)]
    desv = math.sqrt(sum(r * r for r in resid) / len(resid))
    assert desv == pytest.approx(0.1 * 2.0, rel=0.1)


@pytest.mark.parametrize("kw", [
    {"n": 1}, {"ruido": -0.1}, {"amplitud": 0.0}, {"paso": 0.0},
    {"amortiguamiento": -1.0}, {"frecuencia": 0.0},
    {"frecuencia": 5.0, "paso": 0.1},  # justo en Nyquist
    {"frecuencia": 6.0, "paso": 0.1},  # por encima: aliasing
])
def test_oscilador_parametros_invalidos(kw):
    with pytest.raises(ValueError):
        oscilador_sintetico(**kw)


def test_es_rejilla_uniforme_distingue_los_datasets():
    assert es_rejilla_uniforme(oscilador_sintetico())
    assert not es_rejilla_uniforme(kepler_real())
    assert not es_rejilla_uniforme(kepler_sintetico(n=30))