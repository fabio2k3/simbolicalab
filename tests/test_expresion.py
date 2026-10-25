import math

import pytest

from simbolicalab.nucleo import Contador
from simbolicalab.rs import Const, Op, Var, a_cadena, evaluar, tamano

X = Var("x")
KEPLER = Op("*", (X, Op("sqrt", (X,))))       


def test_tamano_cuenta_nodos():
    assert tamano(X) == 1
    assert tamano(Op("sqrt", (X,))) == 2
    assert tamano(KEPLER) == 4


def test_a_cadena():
    assert a_cadena(KEPLER) == "x * sqrt(x)"
    assert a_cadena(Op("+", (Const(1.0), Op("*", (X, Const(2.5)))))) == "1 + (x * 2.5)"
    assert a_cadena(Const(3.0)) == "3"


def test_evaluar_valores():
    assert evaluar(KEPLER, {"x": 4.0}) == 8.0           
    assert evaluar(Op("-", (Const(1.0), X)), {"x": 5.0}) == -4.0
    assert evaluar(Op("neg", (X,)), {"x": 5.0}) == -5.0


def test_igualdad_estructural_y_hash():
    assert Op("sqrt", (X,)) == Op("sqrt", (Var("x"),))
    assert KEPLER != Op("*", (Op("sqrt", (X,)), X))      
    assert len({KEPLER, Op("*", (X, Op("sqrt", (X,))))}) == 1


@pytest.mark.parametrize("formula, x", [
    (Op("/", (Const(1.0), X)), 0.0),                     
    (Op("sqrt", (X,)), -1.0),                            
    (Op("log", (X,)), 0.0),                              
    (Op("log", (X,)), -3.0),                           
])
def test_fuera_de_dominio_da_nan(formula, x):
    assert math.isnan(evaluar(formula, {"x": x}))


def test_nan_se_propaga():
    f = Op("+", (Const(1.0), Op("sqrt", (X,))))
    assert math.isnan(evaluar(f, {"x": -1.0}))


def test_exp_desbordada_da_infinito():
    assert evaluar(Op("exp", (X,)), {"x": 1e6}) == math.inf


def test_evaluar_cuesta_exactamente_el_tamano():
    for f in [X, KEPLER, Op("+", (KEPLER, KEPLER))]:
        c = Contador()
        evaluar(f, {"x": 2.0}, c)
        assert c.total == tamano(f)
