import math

import pytest

from simbolicalab.costo.crecimiento import (
    COSTOS_CLASICOS, mayor_n, pendientes, razon_media, razones, tabla_hardware,
)

HORA = 3600 * 10**9      #


def test_mayor_n_es_el_borde_exacto():
    for nombre, f in COSTOS_CLASICOS.items():
        for k in (1, 10, 1000):
            n = mayor_n(f, HORA * k)
            assert f(n) <= HORA * k < f(n + 1), nombre


def test_mayor_n_cuando_ni_uno_cabe():
    assert mayor_n(lambda n: n + 100, 5) == 0


def test_tabla_coincide_con_la_clasica_para_una_hora():
    t = tabla_hardware()
    assert t["n"] == [3_600_000_000_000, 36_000_000_000_000, 3_600_000_000_000_000]
    assert t["2^n"] == [41, 45, 51]
    assert t["n log n"][0] == pytest.approx(9.86e10, rel=0.01)
    assert t["n log n"][1] == pytest.approx(9.06e11, rel=0.01)
    assert t["n log n"][2] == pytest.approx(7.8e13, rel=0.01)
    assert t["n^2"][0] == pytest.approx(1.9e6, rel=0.01)
    assert t["n^3"][0] == pytest.approx(1.53e4, rel=0.01)


def test_mil_veces_mas_rapido_segun_la_clase_de_costo():
    base = HORA
    lineal = mayor_n(COSTOS_CLASICOS["n"], 1000 * base) / mayor_n(COSTOS_CLASICOS["n"], base)
    cuadratico = mayor_n(COSTOS_CLASICOS["n^2"], 1000 * base) / mayor_n(COSTOS_CLASICOS["n^2"], base)
    cubico = mayor_n(COSTOS_CLASICOS["n^3"], 1000 * base) / mayor_n(COSTOS_CLASICOS["n^3"], base)
    expo = mayor_n(COSTOS_CLASICOS["2^n"], 1000 * base) - mayor_n(COSTOS_CLASICOS["2^n"], base)
    assert lineal == pytest.approx(1000)
    assert cuadratico == pytest.approx(math.sqrt(1000), rel=0.01)       
    assert cubico == pytest.approx(10, rel=0.01)                        
    assert expo == 10                                                  


def test_datos_que_crecen_castigan_al_cuadratico():
    n, k = 10_000, 10
    assert (k * n) / k == n                       
    assert ((k * n) ** 2) / k == k * n ** 2         


def test_pendientes_de_un_polinomio_tienden_a_su_grado():
    puntos = [(n, 3 * n ** 2 + 5 * n) for n in (10, 100, 1000, 10_000)]
    p = pendientes(puntos)
    assert p == sorted(p) and p[-1] == pytest.approx(2, abs=0.01)


def test_las_razones_de_un_exponencial_son_su_base():
    assert razones([2 ** k for k in range(1, 10)]) == [2.0] * 8
    assert razon_media([3 ** k for k in range(1, 10)]) == pytest.approx(3.0)


def test_la_pendiente_de_un_exponencial_no_se_estabiliza():
    p = pendientes([(k, 2 ** k) for k in range(2, 20)])
    assert p == sorted(p) and p[-1] > 3 * p[0]       


def test_n_log_n_se_parece_a_n_pero_no_es_n():
    p = pendientes([(n, n * math.log2(n)) for n in (10 ** 3, 10 ** 6)])
    assert 1.05 < p[0] < 1.25


def test_razon_media_exige_dos_datos():
    with pytest.raises(ValueError):
        razon_media([1.0])
