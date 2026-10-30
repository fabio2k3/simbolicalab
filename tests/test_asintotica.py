import pytest

from simbolicalab.costo.asintotica import (
    primer_contraejemplo_cota_inferior, primer_contraejemplo_cota_superior,
    razones_en_potencias_de_2,
)


def f(n): return 3 * n ** 2 + 5 * n
def g(n): return n ** 2


def test_testigos_correctos_no_encuentran_contraejemplo():
    assert primer_contraejemplo_cota_superior(f, g, c=4, n0=5, hasta=10_000) is None


def test_testigos_incorrectos_se_refutan_con_un_n_concreto():
    assert primer_contraejemplo_cota_superior(f, g, c=4, n0=4, hasta=10_000) == 4   


def test_cota_inferior():
    assert primer_contraejemplo_cota_inferior(f, g, c=3, n0=1, hasta=1000) is None  
    assert primer_contraejemplo_cota_inferior(f, g, c=4, n0=1, hasta=1000) == 6


def test_2_a_la_2n_no_es_O_de_2_a_la_n():
    """Para CUALQUIER c hay un n que lo viola: con c=1000, desde n=10."""
    f2, g2 = (lambda n: 2 ** (2 * n)), (lambda n: 2 ** n)
    assert primer_contraejemplo_cota_superior(f2, g2, c=1000, n0=1, hasta=100) == 10


def test_2_a_la_n_mas_1_si_es_O_de_2_a_la_n():
    assert primer_contraejemplo_cota_superior(lambda n: 2 ** (n + 1), lambda n: 2 ** n, c=2, n0=1, hasta=200) is None


def test_razones_en_potencias_de_2():
    r = razones_en_potencias_de_2(f, g, hasta_exponente=20)
    assert r[-1][1] == pytest.approx(3.0, rel=1e-3)        
    assert [n for n, _ in r][:3] == [2, 4, 8]
