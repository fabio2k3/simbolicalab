import math
import random

import pytest

from simbolicalab.conjuntos import kepler_real, kepler_sintetico, oscilador_sintetico
from simbolicalab.nucleo import Presupuesto, Solver
from simbolicalab.rs import Gramatica
from simbolicalab.solvers import SolverCombinado, SolverEspectral, SolverMedia, solvers_por_tecnica
from simbolicalab.tecnicas import (benchmarks, bic, comparar, eliminacion_hacia_atras, elegir_k, error_en, espectro, ganadores, picos, piso_de_error)

PRESUPUESTO = Presupuesto(3_000_000)


def por(bench, nombre):
    return next(b for b in bench if b.nombre == nombre)


def correr(solver, nombre):
    b = por(benchmarks(), nombre)
    return solver.resolver(b.datos, b.gramatica, Presupuesto(None)), b


@pytest.fixture(scope="module")
def tabla():
    bench = benchmarks()
    filas = comparar(bench, solvers_por_tecnica(), PRESUPUESTO)
    return {(f.benchmark, f.solver): f for f in filas}, filas


def test_bic_y_bic_extendido():
    assert bic(0.01, 30, 1) == pytest.approx(30 * math.log(0.01) + math.log(30))
    extra = 2 * math.log(math.comb(100, 3))
    assert bic(0.01, 30, 3, m=100) == pytest.approx(bic(0.01, 30, 3) + extra)
    assert bic(0.0, 30, 1, piso=1e-12) == pytest.approx(30 * math.log(1e-12) + math.log(30))
    for kw in ({"n": 1, "k": 1}, {"n": 30, "k": -1}, {"n": 30, "k": 5, "m": 3}):
        with pytest.raises(ValueError):
            bic(0.1, **kw)


def test_elegir_k():
    assert elegir_k([1.0, 0.01, 0.0099], 30)[0] == 2                  
    assert elegir_k([1.0, 1.0, 1.0], 30)[0] == 1
    assert elegir_k([1.0, 1e-30, 1e-31], 30, piso=1e-12)[0] == 2        
    with pytest.raises(ValueError):
        elegir_k([], 30)


def test_el_bic_extendido_frena_con_una_biblioteca_grande():
    errores = [1.0, 0.8]
    assert elegir_k(errores, 30)[0] == 2
    assert elegir_k(errores, 30, m=1000)[0] == 1


def test_piso_de_error():
    ys = [1.0, 2.0, 3.0, 4.0]
    assert piso_de_error(ys) == pytest.approx(1e-12 * 1.25)
    assert piso_de_error([5.0] * 4) > 0


def test_eliminacion_hacia_atras_quita_el_ruido_y_conserva_lo_necesario():
    rng = random.Random(0)
    a = [float(i) for i in range(1, 11)]
    b = [v * v for v in a]
    c = [rng.uniform(-1, 1) for _ in a]
    cols = [c, a, b]
    exacta = [2 * u + 3 * v for u, v in zip(a, b)]
    idx, ecm = eliminacion_hacia_atras(cols, exacta, [0, 1, 2], piso_de_error(exacta))
    assert idx == [1, 2] and ecm < 1e-20
    ruidosa = [v + rng.gauss(0, 0.01) for v in exacta]
    idx, _ = eliminacion_hacia_atras(cols, ruidosa, [0, 1, 2], piso_de_error(ruidosa))
    assert idx == [1, 2]
    with pytest.raises(ValueError):
        eliminacion_hacia_atras(cols, exacta, [])


def test_picos_con_frecuencia_minima():
    d = oscilador_sintetico()
    e = espectro(d.ys, d.xs[1] - d.xs[0])
    todos = picos(e, 5)
    assert any(abs(p.frecuencia - 0.46875) < 1e-9 for p in todos)
    filtrados = picos(e, 5, min_frecuencia=0.9)
    assert filtrados and all(p.frecuencia >= 0.9 for p in filtrados)


def test_sin_minimo_de_ciclos_el_espectral_degenera_con_pocos_datos():
    d = por(benchmarks(), "contraejemplo_poda").datos          
    g = Gramatica(variables=("x",))
    r = SolverEspectral(2, min_ciclos=0).resolver(d, g, Presupuesto(None))
    assert max(r.detalle["amplitudes"]) > 1e6 and abs(r.detalle["constante"]) > 1e6      
    r = SolverEspectral(2).resolver(d, g, Presupuesto(None))
    assert r.expresion is None and "ciclos" in r.detalle["motivo"]


def test_el_espectral_sigue_encontrando_los_tonos_con_el_minimo():
    r, b = correr(SolverEspectral(1), "oscilador")
    assert r.detalle["frecuencias"][0] == pytest.approx(0.5, abs=0.005)
    with pytest.raises(ValueError):
        SolverEspectral(1, min_ciclos=-1)


def test_solver_combinado_cumple_el_contrato():
    assert isinstance(SolverCombinado(), Solver)


def test_combinado_encuentra_la_ley_de_kepler_con_un_termino():
    r, b = correr(SolverCombinado(), "kepler_real")
    assert r.detalle["terminos"] == ["a * sqrt(a)"] and r.detalle["k"] == 1
    assert r.detalle["coeficientes"][0] == pytest.approx(1.0, abs=0.01) and r.detalle["terminos_espectrales"] == 0


def test_combinado_usa_los_terminos_espectrales_solo_si_ayudan():
    r, _ = correr(SolverCombinado(), "oscilador")
    assert r.detalle["terminos_espectrales"] == 2 and r.detalle["frecuencias"][0] == pytest.approx(0.5, abs=0.005)
    assert "sin(" in r.detalle["terminos"][0] and r.error < 0.0125
    sin_fft, _ = correr(SolverCombinado(espectral=False), "oscilador")
    assert sin_fft.error > 100 * r.error and sin_fft.detalle["terminos_espectrales"] == 0


def test_combinado_dos_terminos_la_eliminacion_hacia_atras_corrige_a_la_seleccion_golosa():
    con, b = correr(SolverCombinado(), "dos_terminos")
    sin, _ = correr(SolverCombinado(eliminar=False), "dos_terminos")
    assert sorted(con.detalle["terminos"]) == ["x", "x + sqrt(x)"] and con.error < 1e-20
    assert sin.detalle["k"] > con.detalle["k"] == con.detalle["k_antes_de_eliminar"] - (sin.detalle["k"] - con.detalle["k"])
    assert error_en(con.expresion, b.prueba) < 1e-20


def test_combinado_contraejemplo_de_la_poda():
    r, b = correr(SolverCombinado(), "contraejemplo_poda")
    assert r.error < 1e-20 and r.detalle["k"] == 1


def test_los_criterios_de_seleccion_ordenan_la_cantidad_de_terminos():
    for nombre in ("dos_tonos", "oscilador_amortiguado", "kepler_sintetico"):
        ks = {c: correr(SolverCombinado(criterio=c), nombre)[0].detalle["k"] for c in ("ninguno", "bic", "ebic")}
        assert ks["ninguno"] >= ks["bic"] >= ks["ebic"]
    assert correr(SolverCombinado(criterio="ninguno"), "kepler_real")[0].detalle["k"] == 5
    assert correr(SolverCombinado(criterio="ebic"), "oscilador_amortiguado")[0].detalle["k"] == 1
    assert correr(SolverCombinado(criterio="bic"), "oscilador_amortiguado")[0].detalle["k"] == 3


def test_el_criterio_no_mejora_el_caso_tipico_pero_evita_los_desastres():
    g = Gramatica(variables=("a",))
    fuera = {c: [] for c in ("ninguno", "bic", "ebic")}
    for s in range(20):
        entrenamiento, prueba = kepler_sintetico(30, 0.02, s), kepler_sintetico(30, 0.02, 1000 + s)
        for c in fuera:
            r = SolverCombinado(4, 5, criterio=c).resolver(entrenamiento, g, Presupuesto(None))
            fuera[c].append(error_en(r.expresion, prueba))
    mediana = {c: sorted(v)[10] for c, v in fuera.items()}
    assert mediana["ebic"] < 1.15 * mediana["ninguno"]                           
    peor = {c: max(v) for c, v in fuera.items()}
    assert peor["ninguno"] > 5 * peor["ebic"] and peor["ninguno"] > peor["bic"] > peor["ebic"]
    assert sum(fuera["ninguno"]) > 3 * sum(fuera["ebic"])


def test_una_biblioteca_mas_grande_con_pocos_datos_sobreajusta_aunque_se_penalice():
    r4, _ = correr(SolverCombinado(max_tam=4), "kepler_real")
    r5, _ = correr(SolverCombinado(max_tam=5), "kepler_real")
    assert r4.detalle["k"] == 1 and r5.detalle["k"] > 1                          


def test_combinado_presupuesto_agotado_y_parametros():
    r, _ = correr(SolverCombinado(), "oscilador")
    chico = SolverCombinado().resolver(*(lambda b: (b.datos, b.gramatica))(por(benchmarks(), "oscilador")), Presupuesto(500))
    assert chico.agotado and chico.expresion is None and r.operaciones > 500
    for kw in ({"max_tam": 0}, {"k_max": 0}, {"m_frecuencias": 0}, {"refinar": "nada"}, {"reduccion": "nada"},
               {"criterio": "nada"}, {"min_ciclos": -1}):
        with pytest.raises(ValueError):
            SolverCombinado(**kw)


def test_combinado_es_reproducible():
    a, _ = correr(SolverCombinado(), "dos_tonos")
    b, _ = correr(SolverCombinado(), "dos_tonos")
    assert a.detalle["terminos"] == b.detalle["terminos"] and a.error == b.error and a.operaciones == b.operaciones


def test_benchmarks_son_deterministas_y_la_prueba_continua_el_eje():
    a, b = benchmarks(), benchmarks()
    assert [x.nombre for x in a] == [x.nombre for x in b] and len(a) == 7
    assert all(x.datos.ys == y.datos.ys for x, y in zip(a, b))
    assert por(a, "kepler_real").prueba is None and por(a, "kepler_sintetico").prueba is not None
    for nombre in ("contraejemplo_poda", "dos_terminos", "oscilador", "dos_tonos", "oscilador_amortiguado"):
        x = por(a, nombre)
        assert min(x.prueba.xs) > max(x.datos.xs)


def test_error_en():
    b = por(benchmarks(), "dos_terminos")
    assert error_en(None, b.datos) == math.inf
    media = sum(b.datos.ys) / len(b.datos)
    assert error_en(media, b.datos) == pytest.approx(sum((y - media) ** 2 for y in b.datos.ys) / len(b.datos))


def test_capstone_todos_los_solvers_con_el_mismo_presupuesto(tabla):
    por_clave, filas = tabla
    assert len(filas) == 42 and not any(f.agotado for f in filas)
    for nombre in {f.benchmark for f in filas}:
        assert por_clave[(nombre, "media")].error_relativo == pytest.approx(1.0)


def test_capstone_kepler(tabla):
    t, _ = tabla
    for s in ("fuerza_bruta", "dp"):
        assert t[("kepler_real", s)].formula == "a * sqrt(a)"
    assert t[("kepler_real", "dp")].operaciones < t[("kepler_real", "fuerza_bruta")].operaciones / 3
    c = t[("kepler_real", "combinado")]
    assert "a * sqrt(a)" in c.formula and c.error_relativo < t[("kepler_real", "dp")].error_relativo
    assert t[("kepler_real", "espectral")].formula is None                    
    assert t[("kepler_sintetico", "combinado")].error_prueba_relativo < 1e-3


def test_capstone_contraejemplo_y_dos_terminos(tabla):
    t, _ = tabla
    for s in ("fuerza_bruta", "dp", "greedy", "combinado"):
        assert t[("contraejemplo_poda", s)].error_relativo < 1e-20
    c, p, g = t[("dos_terminos", "combinado")], t[("dos_terminos", "dp")], t[("dos_terminos", "greedy")]
    assert c.error_prueba_relativo < 1e-20 and p.error_relativo > 0.3 and p.error_prueba_relativo > 1
    assert 1e-3 < g.error_prueba_relativo < 0.1                             


def test_capstone_senales_periodicas(tabla):
    t, _ = tabla
    for nombre in ("oscilador", "dos_tonos"):
        for s in ("espectral", "combinado"):
            f = t[(nombre, s)]
            assert f.error_relativo < 0.01 and f.error_prueba_relativo < 0.02
        for s in ("fuerza_bruta", "dp", "greedy"):
            assert t[(nombre, s)].error_relativo > 0.95                           
    assert t[("oscilador", "espectral")].operaciones > 100 * t[("kepler_real", "dp")].operaciones


def test_capstone_el_amortiguado_no_se_aprende(tabla):
    t, filas = tabla
    otros = [f for f in filas if f.benchmark == "oscilador_amortiguado" and f.solver != "media"]
    assert min(f.error_prueba_relativo for f in otros) > 0.99                    
    for s in ("espectral", "combinado"):
        f = t[("oscilador_amortiguado", s)]
        assert f.error_relativo < 0.4 and f.error_prueba_relativo > 10           


def test_ganadores(tabla):
    _, filas = tabla
    g = ganadores(filas)
    assert g["dos_terminos"] == "combinado" and g["oscilador"] == "combinado" and g["contraejemplo_poda"] == "dp"
    assert set(g) == {f.benchmark for f in filas}
    entrenamiento = ganadores(filas, fuera_de_muestra=False)
    assert entrenamiento["oscilador"] == "espectral"                           


def test_sin_datos_de_prueba_gana_el_menor_error_de_entrenamiento(tabla):
    _, filas = tabla
    finitos = [f for f in filas if f.benchmark == "kepler_real" and math.isfinite(f.error)]
    mejor = min(f.error for f in finitos)
    assert ganadores(filas)["kepler_real"] in {f.solver for f in finitos if f.error <= mejor * (1 + 1e-6) + 1e-12}


def test_comparar_con_un_solo_solver():
    filas = comparar([por(benchmarks(), "kepler_real")], {"media": SolverMedia()}, Presupuesto(None))
    assert len(filas) == 1 and filas[0].error_relativo == pytest.approx(1.0) and filas[0].error_prueba is None