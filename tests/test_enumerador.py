import math

import pytest

from simbolicalab.nucleo import Contador, PresupuestoAgotado
from simbolicalab.rs import (
    Const, Gramatica, Op, Var, contar_por_size, costo_fuerza_bruta,
    enumerar, mayor_size_alcanzable, tamano,
)

GRAMATICAS = [
    Gramatica(),                                                        # la básica
    Gramatica(variables=("x",), constants=(), unarios=(), binarios=("+",)),
    Gramatica(variables=("x", "y"), constants=(1.0,), unarios=("sqrt", "neg"), binarios=("+", "*")),
    Gramatica(variables=("x",), constants=(), unarios=("exp", "log"), binarios=()),
]


@pytest.mark.parametrize("g", GRAMATICAS)
def test_cantidad_enumerada_coincide_con_la_recurrencia(g):
    max_tam = 6
    por_tamano = {}
    for e in enumerar(g, max_tam):
        por_tamano[tamano(e)] = por_tamano.get(tamano(e), 0) + 1
    esperado = contar_por_size(g, max_tam)
    for s in range(1, max_tam + 1):
        assert por_tamano.get(s, 0) == esperado[s], f"tamaño {s}"


@pytest.mark.parametrize("g", GRAMATICAS)
def test_sin_repetidas(g):
    todas = list(enumerar(g, 6))
    assert len(set(todas)) == len(todas)


def test_salen_por_tamano_no_decreciente():
    tamanos = [tamano(e) for e in enumerar(Gramatica(), 6)]
    assert tamanos == sorted(tamanos)


def test_catalan():
    """Una variable y un solo operador binario: las fórmulas de tamaño 2k+1 son
    los árboles binarios con k nodos internos, y hay Catalan(k) de ellos."""
    g = Gramatica(variables=("x",), constants=(), unarios=(), binarios=("+",))
    n = contar_por_size(g, 11)
    for k in range(0, 6):
        assert n[2 * k + 1] == math.comb(2 * k, k) // (k + 1)
    assert all(n[s] == 0 for s in range(2, 12, 2))


def test_la_ley_de_kepler_esta_en_el_espacio():
    g = Gramatica(variables=("a",))
    kepler = Op("*", (Var("a"), Op("sqrt", (Var("a"),))))
    assert kepler in set(enumerar(g, 4))


def test_el_presupuesto_corta_la_enumeracion():
    c = Contador(limite=50)
    with pytest.raises(PresupuestoAgotado):
        list(enumerar(Gramatica(), 8, c))


def test_construir_cuesta_uno_por_formula():
    c = Contador()
    n = sum(1 for _ in enumerar(Gramatica(), 5, c))
    assert c.total == n == sum(contar_por_size(Gramatica(), 5))


def test_estimacion_de_costo_es_monotona_y_alcanzable():
    g = Gramatica(variables=("a",))
    costos = [costo_fuerza_bruta(g, s, 8) for s in range(1, 9)]
    assert costos == sorted(costos)
    s = mayor_size_alcanzable(g, 1_000_000, 8)
    assert costo_fuerza_bruta(g, s, 8) <= 1_000_000 < costo_fuerza_bruta(g, s + 1, 8)
    assert mayor_size_alcanzable(g, 1, 8) == 0
