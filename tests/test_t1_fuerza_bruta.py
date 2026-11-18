import math

import pytest

from simbolicalab.conjuntos import kepler_real, kepler_sintetico
from simbolicalab.nucleo import Presupuesto, Solver, Traza
from simbolicalab.rs import Gramatica, a_cadena, costo_fuerza_bruta, tamano
from simbolicalab.solvers import SolverFuerzaBruta, SolverMedia

G = Gramatica(variables=("a",))
LEYES_EQUIVALENTES = {"a * sqrt(a)", "sqrt(a) * a"}


def test_cumple_el_protocolo():
    assert isinstance(SolverFuerzaBruta(4), Solver)


def test_redescubre_kepler_sin_ruido():
    d = kepler_sintetico(n=20, ruido=0.0, semilla=0)
    r = SolverFuerzaBruta(4, metrica="relativo").resolver(d, G, Presupuesto())
    assert a_cadena(r.expresion) in LEYES_EQUIVALENTES
    assert r.error < 1e-12 and not r.agotado


def test_desempate_gana_la_primera_enumerada():
    d = kepler_sintetico(n=20, ruido=0.0, semilla=0)
    r = SolverFuerzaBruta(4, metrica="relativo").resolver(d, G, Presupuesto())
    assert a_cadena(r.expresion) == "a * sqrt(a)"


def test_redescubre_kepler_con_los_planetas_reales():
    r = SolverFuerzaBruta(4, metrica="relativo").resolver(kepler_real(), G, Presupuesto())
    assert a_cadena(r.expresion) in LEYES_EQUIVALENTES
    assert r.error < 0.005


def test_costo_medido_coincide_con_el_predicho():
    d = kepler_real()
    for max_tam in (3, 4, 5):
        r = SolverFuerzaBruta(max_tam).resolver(d, G, Presupuesto())
        assert r.operaciones == costo_fuerza_bruta(G, max_tam, len(d))


def test_presupuesto_agotado_devuelve_lo_mejor_visto():
    d = kepler_real()
    r = SolverFuerzaBruta(6).resolver(d, G, Presupuesto(operaciones=5_000))
    assert r.agotado
    assert r.expresion is not None and math.isfinite(r.error)  
    assert r.operaciones > 5_000                                
    assert r.detalle["evaluadas"] > 0


def test_la_traza_registra_mejoras_estrictas():
    t = Traza()
    SolverFuerzaBruta(4).resolver(kepler_real(), G, Presupuesto(), traza=t)
    errores = [e.datos["error"] for e in t.eventos]
    assert errores == sorted(errores, reverse=True)
    assert len(set(errores)) == len(errores)                    
    assert all(e.tipo == "mejora" for e in t.eventos)


def test_el_tamano_maximo_acota_lo_que_se_encuentra():
    r = SolverFuerzaBruta(3).resolver(kepler_real(), G, Presupuesto())
    assert tamano(r.expresion) <= 3                              


def test_argumentos_invalidos():
    with pytest.raises(ValueError):
        SolverFuerzaBruta(0)
    with pytest.raises(ValueError):
        SolverFuerzaBruta(3, metrica="inventada")


def test_el_solver_de_la_media_acepta_datos_reales():
    r = SolverMedia().resolver(kepler_real(), G, Presupuesto())
    assert r.expresion == pytest.approx(sum(kepler_real().ys) / 8)


def test_equivalentes_numericas_no_desplazan_a_la_mas_pequena():
    for metrica in ("ecm", "relativo"):
        r = SolverFuerzaBruta(6, metrica).resolver(kepler_real(), G, Presupuesto())
        assert a_cadena(r.expresion) == "a * sqrt(a)", metrica


def test_el_resultado_no_depende_de_buscar_mas_alla_si_ya_esta_la_ley():
    d = kepler_sintetico(n=20, ruido=0.0, semilla=0)
    r4 = SolverFuerzaBruta(4, "relativo").resolver(d, G, Presupuesto())
    r6 = SolverFuerzaBruta(6, "relativo").resolver(d, G, Presupuesto())
    assert r4.expresion == r6.expresion


def test_la_primera_formula_definida_siempre_se_acepta():
    from simbolicalab.solvers.fuerza_bruta import _mejora_de_verdad
    assert _mejora_de_verdad(5.0, math.inf)
    assert not _mejora_de_verdad(math.inf, math.inf)
    assert not _mejora_de_verdad(1.0, 1.0)                   
    assert not _mejora_de_verdad(1.0 - 1e-12, 1.0)           
    assert _mejora_de_verdad(0.5, 1.0)                       
