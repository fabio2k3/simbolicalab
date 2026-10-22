import pytest

from simbolicalab.costo.suma import suma_contada
from simbolicalab.nucleo import medir

@pytest.mark.parametrize("n", [0, 1, 2, 10, 1000])
def test_suma_cuesta_5n_mas_3(n):
    resultado, c = medir(suma_contada, list(range(n)))
    assert resultado == sum(range(n))
    assert c.total == 5 * n + 3


@pytest.mark.parametrize("n", [0, 1, 2, 10, 1000])
def test_suma_fusionando_cuesta_4n_mas_3(n):
    _, c = medir(suma_contada, list(range(n)), fusionar_acceso_y_suma=True)
    assert c.total == 4 * n + 3
