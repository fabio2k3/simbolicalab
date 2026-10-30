import pytest

from simbolicalab.costo.aritmetica import (
    costo_multiplicacion_bits, costo_suma_bits, cuadrados_repetidos, fibonacci_contado,
)
from simbolicalab.nucleo import Contador, medir


def test_costos_de_bits_basicos():
    assert costo_suma_bits(255, 1) == 8
    assert costo_suma_bits(1, 255) == 8               
    assert costo_multiplicacion_bits(255, 3) == 8 * 2
    assert costo_multiplicacion_bits(3, 255) == 2 * 8


@pytest.mark.parametrize("k", [0, 1, 2, 5, 10])
def test_cuadrados_repetidos_da_2_a_la_2_a_la_k(k):
    x, c = medir(cuadrados_repetidos, k)
    assert x == 2 ** (2 ** k)
    assert x.bit_length() == 2 ** k + 1
    assert c.por_categoria.get("mult_unitaria", 0) == k              


def test_el_modelo_unitario_subestima_cada_vez_mas():
    razones = []
    for k in (4, 8, 12):
        _, c = medir(cuadrados_repetidos, k)
        razones.append(c.por_categoria["bits"] / c.por_categoria["mult_unitaria"])
    assert razones == sorted(razones) and razones[-1] > 100 * razones[0]


def test_costo_de_bits_de_los_cuadrados_es_aprox_4_a_la_k_sobre_3():
    k = 12
    _, c = medir(cuadrados_repetidos, k)
    assert c.por_categoria["bits"] == pytest.approx(4 ** k / 3, rel=0.01)


def test_fibonacci_es_correcto():
    esperado = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    assert [medir(fibonacci_contado, n)[0] for n in range(11)] == esperado
    assert medir(fibonacci_contado, 100)[0] == 354_224_848_179_261_915_075


def test_fibonacci_cuenta_n_sumas_y_bits_cuadraticos():
    n = 3000
    _, c = medir(fibonacci_contado, n)
    assert c.por_categoria["suma"] == n
    assert c.por_categoria["bits"] / n ** 2 == pytest.approx(0.347, rel=0.03)


def test_fibonacci_es_polinomial_en_n_y_exponencial_en_los_bits_de_n():
    """Al añadir 1 bit a n (duplicarlo), el costo en bits se multiplica por ≈ 4."""
    _, c1 = medir(fibonacci_contado, 1000)
    _, c2 = medir(fibonacci_contado, 2000)
    assert c2.por_categoria["bits"] / c1.por_categoria["bits"] == pytest.approx(4, rel=0.03)
