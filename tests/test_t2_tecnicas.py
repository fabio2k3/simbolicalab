"""Fase 1: PD por tamaño (estado = firma) y Monte Carlo (verificación de equivalencia por puntos aleatorios)."""
import math
import random
from math import comb

import pytest

from simbolicalab.conjuntos import (contraejemplo_de_la_poda, datos_desde_expresion, kepler_real, kepler_sintetico,
                                    oscilador_sintetico)
from simbolicalab.nucleo import Contador, Presupuesto, Solver, tasa_de_deteccion
from simbolicalab.rs import (Const, Gramatica, InvarianteViolado, METRICAS, Op, Var, a_cadena, enumerar, evaluar,
                             tamano)
from simbolicalab.solvers import SolverFuerzaBruta, SolverDP
from simbolicalab.tecnicas import (cota_falsa_fusion, costo_predicho, deduplicar_huella, equivalentes_mc,
                                   error_de_firma, es_polinomio, es_primo, evaluar_mod, firma_vectorial, grado, huella,
                                   polinomio_canonico, puntos_aleatorios, rondas_necesarias, tabla_pd,
                                   verificar_cobertura)
from simbolicalab.tecnicas.dp_tamano import mejora_de_verdad
from simbolicalab.tecnicas.variantes_defectuosa import puntos_mismo_punto, puntos_rango_pequeno

X = Var("x")


def gram_kepler(d):
    return Gramatica(variables=(d.nombre_x,))


def poli(m):
    return Gramatica(constants=(1.0, 2.0), unarios=(), binarios=("+", "-", "*"))


# ---------------------------------------------------------------- PD por tamaño

def test_solver_pd_cumple_el_contrato():
    assert isinstance(SolverDP(3), Solver)


def test_error_de_firma_coincide_con_las_metricas():
    d = kepler_real()
    g = gram_kepler(d)
    for e in list(enumerar(g, 5))[::7]:
        f = firma_vectorial(e, d.nombre_x, d.xs)
        if f is None:
            continue
        for m in ("ecm", "relativo"):
            ref = METRICAS[m](e, d)
            ref = ref if math.isfinite(ref) else math.inf
            assert error_de_firma(f, d.ys, m) == ref


def test_regla_de_mejora_igual_que_fuerza_bruta():
    from simbolicalab.solvers.fuerza_bruta import _mejora_de_verdad
    for a, b in [(1.0, math.inf), (0.5, 1.0), (1.0, 1.0), (1.0 - 1e-12, 1.0), (1e-14, 1e-13), (0.0, 0.0)]:
        assert mejora_de_verdad(a, b) == _mejora_de_verdad(a, b)


@pytest.mark.parametrize("m", [1, 2, 3, 4, 5, 6])
@pytest.mark.parametrize("metrica", ["ecm", "relativo"])
def test_pd_encuentra_el_mismo_error_que_fuerza_bruta_en_kepler(m, metrica):
    d = kepler_real()
    g = gram_kepler(d)
    a = SolverFuerzaBruta(m, metrica).resolver(d, g, Presupuesto(None))
    b = SolverDP(m, metrica, vigilar=True).resolver(d, g, Presupuesto(None))
    assert b.error == pytest.approx(a.error, rel=1e-9, abs=1e-12)
    assert tamano(b.expresion) <= m
    assert METRICAS[metrica](b.expresion, d) == pytest.approx(b.error, rel=1e-12, abs=1e-15)


def test_pd_igual_a_fuerza_bruta_con_exp_log_y_sintetico():
    d = kepler_sintetico(12, 0.05, 3)
    g = Gramatica(variables=(d.nombre_x,), unarios=("sqrt", "log", "exp"))
    a = SolverFuerzaBruta(5).resolver(d, g, Presupuesto(None))
    b = SolverDP(5, vigilar=True).resolver(d, g, Presupuesto(None))
    assert b.error == pytest.approx(a.error, rel=1e-9, abs=1e-12)


def test_pd_igual_a_fuerza_bruta_con_sin_cos_en_el_oscilador():
    d = oscilador_sintetico(16, 0.02, 1)
    g = Gramatica(variables=(d.nombre_x,), unarios=("sin", "cos"))
    a = SolverFuerzaBruta(4).resolver(d, g, Presupuesto(None))
    b = SolverDP(4, vigilar=True).resolver(d, g, Presupuesto(None))
    assert b.error == pytest.approx(a.error, rel=1e-9, abs=1e-12)


def test_pd_cubre_exactamente_las_firmas_de_la_fuerza_bruta():
    d = kepler_real()
    res = verificar_cobertura(d, gram_kepler(d), 5)
    assert res["firmas_distintas"] == res["representantes"] < res["formulas"]


def test_cobertura_detecta_un_pd_que_poda():
    d = contraejemplo_de_la_poda()
    g = Gramatica()
    brutas = verificar_cobertura(d, g, 4)["firmas_distintas"]
    podado = {f for nivel in tabla_pd(d, g, 4, ancho=2).representantes for _, f, _ in nivel}
    assert len(podado) < brutas


def test_pd_usa_menos_operaciones_y_el_ahorro_crece():
    d = kepler_real()
    g = gram_kepler(d)
    ahorro = []
    for m in (4, 5, 6):
        a = SolverFuerzaBruta(m).resolver(d, g, Presupuesto(None)).operaciones
        b = SolverDP(m).resolver(d, g, Presupuesto(None)).operaciones
        assert b < a
        ahorro.append(a / b)
    assert ahorro[0] < ahorro[1] < ahorro[2]


def test_costo_predicho_igual_al_medido():
    d = kepler_real()
    g = gram_kepler(d)
    c = Contador()
    t = tabla_pd(d, g, 7, contador=c)
    reps = [0] + [x.representantes for x in t.niveles]
    assert costo_predicho(reps, g.n_terminales, len(g.unarios), len(g.binarios), len(d), 7) == c.total


def test_representantes_por_tamano_son_menos_que_formulas_posibles():
    d = kepler_real()
    g = gram_kepler(d)
    from simbolicalab.rs import contar_por_size
    t = tabla_pd(d, g, 7)
    n = contar_por_size(g, 7)
    assert all(t.niveles[s - 1].representantes <= n[s] for s in range(1, 8))
    assert t.niveles[6].representantes < n[7] // 10


def test_el_primer_nivel_son_los_terminales():
    d = kepler_real()
    t = tabla_pd(d, gram_kepler(d), 1)
    assert t.niveles[0].representantes == 3 and t.mejor is not None


def test_recurrencia_falsa_la_poda_por_error_pierde_el_optimo():
    d = contraejemplo_de_la_poda()
    g = Gramatica()
    exacto = tabla_pd(d, g, 4)
    assert exacto.mejor_error == 0.0 and a_cadena(exacto.mejor) == "sqrt((x + 1))"
    for ancho in (1, 3, 10):
        podado = tabla_pd(d, g, 4, ancho=ancho)
        assert podado.mejor_error > 0.05


def test_ancho_muy_grande_equivale_a_no_podar():
    d = kepler_real()
    g = gram_kepler(d)
    a = tabla_pd(d, g, 5)
    b = tabla_pd(d, g, 5, ancho=10 ** 6)
    assert a.mejor_error == b.mejor_error
    assert [x.representantes for x in a.niveles] == [x.representantes for x in b.niveles]


def test_cifras_fusiona_equivalentes_por_redondeo_sin_perder_el_optimo():
    d = kepler_real()
    g = gram_kepler(d)
    exacta = tabla_pd(d, g, 6)
    redondeada = tabla_pd(d, g, 6, cifras=12)
    assert sum(x.representantes for x in redondeada.niveles) < sum(x.representantes for x in exacta.niveles)
    assert redondeada.mejor_error == pytest.approx(exacta.mejor_error, rel=1e-9)


def test_frente_de_pareto_es_estrictamente_decreciente():
    d = kepler_real()
    t = tabla_pd(d, gram_kepler(d), 7)
    frente = t.frente_de_pareto()
    assert frente and frente[-1][2] == t.mejor_error
    assert all(a[0] < b[0] and a[2] > b[2] for a, b in zip(frente, frente[1:]))


def test_presupuesto_agotado_devuelve_lo_mejor_hasta_ahora():
    d = kepler_real()
    r = SolverDP(8).resolver(d, gram_kepler(d), Presupuesto(5000))
    assert r.agotado
    assert r.expresion is not None and math.isfinite(r.error)


def test_pd_con_parametros_invalidos():
    with pytest.raises(ValueError):
        SolverDP(0)
    with pytest.raises(ValueError):
        SolverDP(3, ancho=0)
    with pytest.raises(ValueError):
        SolverDP(3, metrica="nada")


def test_pd_no_confunde_nan_con_infinito():
    # (x*x)*(x*x) desborda a inf sin excepción y 1/inf = 0 es válido: el PD debe conservar los inf y coincidir
    from simbolicalab.rs import Datos
    d = Datos(xs=(1e100, 2e100, 3e100), ys=(1.0, 2.0, 3.0))
    g = Gramatica(constants=(1.0,), unarios=(), binarios=("*", "/"))
    a = SolverFuerzaBruta(9).resolver(d, g, Presupuesto(None))
    b = SolverDP(9, vigilar=True).resolver(d, g, Presupuesto(None))
    assert b.error == pytest.approx(a.error, rel=1e-9, abs=1e-12)
    assert verificar_cobertura(d, g, 9)["firmas_distintas"] > 0
    assert any(math.isinf(v) for nivel in tabla_pd(d, g, 7).representantes for _, f, _ in nivel for v in f)


# ---------------------------------------------------------------- polinomios

def test_es_polinomio_y_grado():
    assert es_polinomio(Op("*", (X, Op("+", (X, Const(1.0))))))
    assert not es_polinomio(Op("sqrt", (X,)))
    assert not es_polinomio(Op("/", (X, Const(2.0))))
    assert grado(Op("*", (X, Op("*", (X, X))))) == 3
    assert grado(Op("+", (Op("*", (X, X)), X))) == 2
    with pytest.raises(ValueError):
        grado(Op("sqrt", (X,)))


def test_forma_canonica_identifica_equivalentes():
    a = Op("*", (X, Op("+", (X, Const(1.0)))))
    b = Op("+", (Op("*", (X, X)), X))
    assert polinomio_canonico(a) == polinomio_canonico(b)
    c = Op("*", (Op("+", (X, Const(1.0))), Op("-", (X, Const(1.0)))))
    d = Op("-", (Op("*", (X, X)), Const(1.0)))
    assert polinomio_canonico(c) == polinomio_canonico(d)
    assert polinomio_canonico(X) != polinomio_canonico(Op("*", (X, X)))
    assert polinomio_canonico(Op("-", (X, X))) == ()


# ---------------------------------------------------------------- Monte Carlo

def test_es_primo():
    assert [n for n in range(2, 30) if es_primo(n)] == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    assert es_primo(2 ** 31 - 1) and es_primo(2 ** 61 - 1)
    assert not es_primo(2 ** 61 + 1) and not es_primo(1) and not es_primo(561)


def test_evaluar_mod_coincide_con_la_forma_canonica():
    rng = random.Random(0)
    p = 1009
    for e in list(enumerar(poli(5), 5))[::5]:
        coef = polinomio_canonico(e)
        r = rng.randrange(p)
        esperado = sum(int(c.numerator) * pow(c.denominator, -1, p) * pow(r, i, p) for i, c in enumerate(coef)) % p
        assert evaluar_mod(e, "x", r, p) == esperado


def test_los_equivalentes_nunca_se_separan():
    fs = list(enumerar(poli(5), 7))
    canon = [polinomio_canonico(e) for e in fs]
    p = 101
    pts = puntos_aleatorios(2, p, random.Random(3))
    por_clase = {}
    for e, c in zip(fs, canon):
        por_clase.setdefault(c, set()).add(huella(e, "x", pts, p))
    assert all(len(v) == 1 for v in por_clase.values())


def test_equivalentes_mc_equivalentes_y_distintos():
    a = Op("*", (X, Op("+", (X, Const(1.0)))))
    b = Op("+", (Op("*", (X, X)), X))
    rng = random.Random(0)
    v = equivalentes_mc(a, b, "x", 5, 101, rng)
    assert v.equivalentes and v.testigo is None and v.rondas == 5
    v = equivalentes_mc(X, Op("*", (X, X)), "x", 20, 2 ** 31 - 1, rng)
    assert not v.equivalentes and v.testigo is not None
    r = v.testigo
    assert evaluar_mod(X, "x", r, 2 ** 31 - 1) != evaluar_mod(Op("*", (X, X)), "x", r, 2 ** 31 - 1)


def test_monte_carlo_rechaza_lo_que_no_garantiza():
    rng = random.Random(0)
    with pytest.raises(ValueError):
        equivalentes_mc(Op("sqrt", (X,)), X, "x", 3, 101, rng)
    with pytest.raises(ValueError):
        equivalentes_mc(Op("*", (X, Op("*", (X, X)))), X, "x", 3, 3, rng)     # p <= grado
    with pytest.raises(ValueError):
        equivalentes_mc(X, X, "x", 3, 100, rng)                              # p no primo
    with pytest.raises(ValueError):
        equivalentes_mc(X, X, "x", 0, 101, rng)


def test_cotas_de_schwartz_zippel():
    assert cota_falsa_fusion(4, 101, 1) == pytest.approx(4 / 101)
    assert cota_falsa_fusion(4, 101, 3) == pytest.approx((4 / 101) ** 3)
    k = rondas_necesarias(4, 101, 1e-6)
    assert cota_falsa_fusion(4, 101, k) <= 1e-6 < cota_falsa_fusion(4, 101, k - 1)
    with pytest.raises(ValueError):
        rondas_necesarias(4, 3, 0.1)


def test_dedup_por_huella_recupera_las_clases_exactas():
    fs = list(enumerar(poli(5), 7))
    exactas = len({polinomio_canonico(e) for e in fs})
    pts = puntos_aleatorios(3, 2 ** 61 - 1, random.Random(1))
    K = deduplicar_huella(fs, "x", pts, 2 ** 61 - 1)
    assert len(K) == exactas < len(fs) / 5
    assert K == sorted(K)


def test_falsas_fusiones_por_debajo_de_la_cota_de_la_union():
    fs = list(enumerar(poli(5), 7))
    canon = [polinomio_canonico(e) for e in fs]
    m, d, p = len(set(canon)), max(grado(e) for e in fs), 101
    for k in (1, 2, 3):
        perdidas = []
        for s in range(8):
            K = deduplicar_huella(fs, "x", puntos_aleatorios(k, p, random.Random(s)), p)
            perdidas.append(m - len(K))
        assert sum(perdidas) / len(perdidas) <= comb(m, 2) * cota_falsa_fusion(d, p, k)
    assert sum(perdidas) == 0                                       # con k = 3 no se pierde ninguna clase


def test_un_solo_punto_no_distingue_mas_clases_que_el_modulo():
    fs = list(enumerar(poli(5), 7))
    m = len({polinomio_canonico(e) for e in fs})
    p = 11
    K = deduplicar_huella(fs, "x", puntos_aleatorios(1, p, random.Random(0)), p)
    assert len(K) <= p < m


def test_variantes_defectuosas_se_detectan():
    fs = list(enumerar(poli(5), 7))
    canon = [polinomio_canonico(e) for e in fs]
    m, p, k = len(set(canon)), 101, 4
    ids = {}
    clase = [ids.setdefault(c, len(ids)) for c in canon]

    def tasa(fn):
        gen = lambda rng: (rng.randrange(len(fs)), rng.randrange(len(fs)), fn(k, p, rng))
        correcto = lambda x: clase[x[0]] == clase[x[1]]
        variante = lambda x: huella(fs[x[0]], "x", x[2], p) == huella(fs[x[1]], "x", x[2], p)
        return tasa_de_deteccion(gen, correcto, variante, 3000, 0)

    assert tasa(puntos_aleatorios).detectadas == 0
    assert tasa(puntos_mismo_punto).tasa > 0.002
    assert tasa(puntos_rango_pequeno).tasa > 0.01
    for fn in (puntos_mismo_punto, puntos_rango_pequeno):
        K = deduplicar_huella(fs, "x", fn(k, p, random.Random(0)), p)
        assert len(K) < m


def test_rango_pequeno_confunde_x_con_x_cuadrado():
    pts = puntos_rango_pequeno(6, 101, random.Random(0))
    assert huella(X, "x", pts, 101) == huella(Op("*", (X, X)), "x", pts, 101)


def test_con_mas_puntos_de_datos_que_grado_los_datos_no_fusionan_clases_distintas():
    d = kepler_real()
    fs = list(enumerar(Gramatica(variables=("a",), constants=(1.0, 2.0), unarios=(), binarios=("+", "-", "*")), 7))
    assert len(d) > max(grado(e) for e in fs)
    from simbolicalab.rs import firma
    grupos = {}
    for e in fs:
        grupos.setdefault(firma(e, "a", d.xs), set()).add(polinomio_canonico(e, "a"))
    assert all(len(v) == 1 for v in grupos.values())