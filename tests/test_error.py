import math

import pytest

from simbolicalab.nucleo import Contador
from simbolicalab.rs import (
    Const, Datos, Op, Var, error_cuadratico_medio, error_relativo_medio, tamano,
)

X = Var("x")
DOBLE = Op("*", (Const(2.0), X))
DATOS = Datos(xs=(1.0, 2.0, 4.0), ys=(2.0, 4.0, 8.0), nombre_x="x")   


def test_ajuste_perfecto_da_cero():
    assert error_cuadratico_medio(DOBLE, DATOS) == 0.0
    assert error_relativo_medio(DOBLE, DATOS) == 0.0


def test_ecm_valor_conocido():
    assert error_cuadratico_medio(X, DATOS) == pytest.approx(7.0)


def test_relativo_valor_conocido():
    assert error_relativo_medio(X, DATOS) == pytest.approx(0.5)


def test_formula_indefinida_tiene_error_infinito():
    f = Op("/", (Const(1.0), Op("-", (X, Const(2.0)))))      
    assert error_cuadratico_medio(f, DATOS) == math.inf
    assert error_relativo_medio(f, DATOS) == math.inf


def test_relativo_exige_y_distinto_de_cero():
    with pytest.raises(ValueError):
        error_relativo_medio(X, Datos(xs=(1.0,), ys=(0.0,)))


def test_costo_del_error_es_tamano_por_puntos():
    c = Contador()
    error_cuadratico_medio(DOBLE, DATOS, c)
    assert c.total == tamano(DOBLE) * len(DATOS)


def test_datos_invalidos():
    with pytest.raises(ValueError):
        Datos(xs=(1.0,), ys=(1.0, 2.0))
    with pytest.raises(ValueError):
        Datos(xs=(), ys=())
    with pytest.raises(ValueError):
        Datos(xs=(math.nan,), ys=(1.0,))


def test_datos_se_recorren_como_pares():
    assert list(DATOS) == [(1.0, 2.0), (2.0, 4.0), (4.0, 8.0)]
    assert len(DATOS) == 3
