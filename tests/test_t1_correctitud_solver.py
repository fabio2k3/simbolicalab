import math

import pytest

from simbolicalab.conjuntos import kepler_real, kepler_sintetico
from simbolicalab.nucleo import Presupuesto
from simbolicalab.rs import Gramatica
from simbolicalab.solvers import SolverFuerzaBruta
from simbolicalab.solvers import fuerza_bruta as modulo
from simbolicalab.solvers.fuerza_bruta import tolerancia

G = Gramatica(variables=("a",))


@pytest.mark.parametrize("metrica", ["ecm", "relativo"])
@pytest.mark.parametrize("datos", [kepler_real(), kepler_sintetico(20, 0.03, 1), kepler_sintetico(10, 0.0, 4)],
                         ids=["real", "ruido", "exacto"])
def test_el_invariante_reforzado_se_mantiene_en_cada_paso(datos, metrica):
    SolverFuerzaBruta(5, metrica, vigilar=True).resolver(datos, G, Presupuesto())      


def test_la_garantia_final():
    r = SolverFuerzaBruta(6, "relativo").resolver(kepler_real(), G, Presupuesto())
    m = r.detalle["min_visto"]
    assert r.error - tolerancia(r.error) <= m <= r.error


def test_el_invariante_ingenuo_es_falso():
    r = SolverFuerzaBruta(6, "relativo").resolver(kepler_real(), G, Presupuesto())
    assert r.detalle["min_visto"] < r.error
    assert r.error - r.detalle["min_visto"] < tolerancia(r.error)          


def test_vigilar_atrapa_un_solver_que_no_actualiza_el_mejor(monkeypatch):
    monkeypatch.setattr(modulo, "_mejora_de_verdad", lambda nuevo, actual: math.isinf(actual) and nuevo < actual)
    with pytest.raises(AssertionError, match="invariante violado"):
        SolverFuerzaBruta(5, "relativo", vigilar=True).resolver(kepler_real(), G, Presupuesto())


def test_vigilar_no_cambia_el_resultado_ni_el_costo():
    a = SolverFuerzaBruta(5, "relativo").resolver(kepler_real(), G, Presupuesto())
    b = SolverFuerzaBruta(5, "relativo", vigilar=True).resolver(kepler_real(), G, Presupuesto())
    assert (a.expresion, a.error, a.operaciones) == (b.expresion, b.error, b.operaciones)


def test_tolerancia():
    assert tolerancia(0.0) == 1e-12
    assert tolerancia(1.0) == pytest.approx(1e-9)
    assert tolerancia(1e-6) == pytest.approx(1e-12)
