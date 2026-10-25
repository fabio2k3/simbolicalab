import pytest

from simbolicalab.conjuntos import kepler_real, kepler_sintetico
from simbolicalab.rs import Op, Var, error_relativo_medio

KEPLER = Op("*", (Var("a"), Op("sqrt", (Var("a"),))))


def test_kepler_real_tiene_ocho_planetas_y_cumple_la_ley():
    d = kepler_real()
    assert len(d) == 8 and d.nombre_x == "a"
    assert error_relativo_medio(KEPLER, d) < 0.005          # < 0.5 % de error relativo medio


def test_sintetico_sin_ruido_cumple_la_ley_exactamente():
    d = kepler_sintetico(n=25, ruido=0.0, semilla=1)
    assert error_relativo_medio(KEPLER, d) < 1e-12


def test_sintetico_con_ruido_se_desvia_en_la_escala_del_ruido():
    d = kepler_sintetico(n=400, ruido=0.02, semilla=3)
    # el error relativo medio de |N(0, 0.02)| es 0.02 * sqrt(2/pi) ~ 0.016
    assert 0.010 < error_relativo_medio(KEPLER, d) < 0.022


def test_sintetico_es_reproducible_y_depende_de_la_semilla():
    assert kepler_sintetico(10, 0.05, 7) == kepler_sintetico(10, 0.05, 7)
    assert kepler_sintetico(10, 0.05, 7) != kepler_sintetico(10, 0.05, 8)


def test_sintetico_valida_argumentos():
    with pytest.raises(ValueError):
        kepler_sintetico(n=0)
    with pytest.raises(ValueError):
        kepler_sintetico(ruido=-0.1)
