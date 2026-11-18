import pytest

from simbolicalab.nucleo import tasa_de_deteccion


def gen(rng):
    return [rng.randint(0, 9) for _ in range(rng.randint(0, 8))]


def test_una_variante_identica_nunca_se_detecta():
    r = tasa_de_deteccion(gen, sorted, sorted, pruebas=50)
    assert r.detectadas == 0 and r.tasa == 0.0 and r.primer_contraejemplo is None


def test_una_variante_siempre_distinta_se_detecta_siempre():
    r = tasa_de_deteccion(gen, lambda x: len(x), lambda x: len(x) + 1, pruebas=50)
    assert r.detectadas == 50 and r.tasa == 1.0


def test_la_tasa_depende_del_generador():
    correcto = lambda x: max(x)
    variante = lambda x: max(x[:-1] or x)
    sin_estructura = lambda rng: [rng.randint(0, 99) for _ in range(20)]
    maximo_al_final = lambda rng: sorted(rng.randint(0, 99) for _ in range(20))
    a = tasa_de_deteccion(sin_estructura, correcto, variante, pruebas=200)
    b = tasa_de_deteccion(maximo_al_final, correcto, variante, pruebas=200)
    assert a.tasa < 0.2         
    assert b.tasa > 0.8          


def test_es_reproducible_y_guarda_el_primer_contraejemplo():
    r1 = tasa_de_deteccion(gen, lambda x: sum(x), lambda x: sum(x[:-1]), pruebas=40, semilla=3)
    r2 = tasa_de_deteccion(gen, lambda x: sum(x), lambda x: sum(x[:-1]), pruebas=40, semilla=3)
    assert r1 == r2 and r1.primer_contraejemplo is not None


def test_pruebas_invalidas():
    with pytest.raises(ValueError):
        tasa_de_deteccion(gen, sorted, sorted, pruebas=0)
