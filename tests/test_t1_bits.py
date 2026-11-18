import itertools
import random

import pytest

from simbolicalab.costo.bits import (
    SEGUNDOS_POR_ANIO, es_primo_contado, mochila_contada, tamaño_en_bits,
    tiempo_division_de_prueba,
)
from simbolicalab.nucleo import Contador, medir


def test_tamano_en_bits():
    assert [tamaño_en_bits(n) for n in (0, 1, 2, 3, 4, 255, 256)] == [1, 1, 2, 2, 3, 8, 9]
    with pytest.raises(ValueError):
        tamaño_en_bits(-1)


@pytest.mark.parametrize("n, esperadas", [(97, 8), (10_007, 99), (1_000_003, 999), (1_000_000_007, 31_621)])
def test_divisiones_conocidas(n, esperadas):
    primo, c = medir(lambda n, contador: (es_primo_contado(n, contador)), n)
    assert primo is True and c.total == esperadas


def test_primalidad_contra_una_criba():
    """Oráculo independiente: la criba de Eratóstenes."""
    limite = 3000
    criba = [True] * (limite + 1)
    criba[0] = criba[1] = False
    for i in range(2, int(limite ** 0.5) + 1):
        if criba[i]:
            for j in range(i * i, limite + 1, i):
                criba[j] = False
    for n in range(limite + 1):
        assert es_primo_contado(n, Contador()) == criba[n], n


def test_divisiones_son_exponenciales_en_bits():
    primos = {16: 65_521, 24: 16_777_213, 32: 4_294_967_291}
    div = {}
    for b, p in primos.items():
        c = Contador()
        assert es_primo_contado(p, c) and tamaño_en_bits(p) == b
        div[b] = c.total
    assert 14 < div[24] / div[16] < 18
    assert 14 < div[32] / div[24] < 18


def test_tiempos_del_peor_caso():
    assert tiempo_division_de_prueba(64) == pytest.approx(4.29, rel=0.01)              
    assert tiempo_division_de_prueba(128) / SEGUNDOS_POR_ANIO == pytest.approx(585, rel=0.01)
    assert tiempo_division_de_prueba(1024) / SEGUNDOS_POR_ANIO > 1e137                   


def mochila_por_fuerza_bruta(pesos, valores, capacidad):
    mejor = 0
    for mascara in itertools.product((0, 1), repeat=len(pesos)):
        if sum(p for p, m in zip(pesos, mascara) if m) <= capacidad:
            mejor = max(mejor, sum(v for v, m in zip(valores, mascara) if m))
    return mejor


def test_mochila_contra_fuerza_bruta():
    rng = random.Random(5)
    for _ in range(200):
        n = rng.randint(0, 8)
        pesos = [rng.randint(1, 10) for _ in range(n)]
        valores = [rng.randint(1, 20) for _ in range(n)]
        cap = rng.randint(0, 30)
        assert mochila_contada(pesos, valores, cap, Contador()) == mochila_por_fuerza_bruta(pesos, valores, cap)


def test_mochila_cuesta_n_por_w_mas_uno_celdas():
    for n, w in [(5, 10), (20, 1000), (3, 0)]:
        c = Contador()
        mochila_contada([1] * n, [1] * n, w, c)
        assert c.total == n * (w + 1)


def test_mochila_es_lineal_en_w_y_exponencial_en_sus_bits():
    costos = {}
    for b in (8, 10, 12):
        w = 2 ** b
        c = Contador()
        mochila_contada([3] * 10, [1] * 10, w, c)
        costos[b] = c.total
    assert costos[10] / costos[8] == pytest.approx(4, rel=0.01)     
    assert costos[12] / costos[10] == pytest.approx(4, rel=0.01)


def test_mochila_longitudes_distintas():
    with pytest.raises(ValueError):
        mochila_contada([1, 2], [1], 5, Contador())
