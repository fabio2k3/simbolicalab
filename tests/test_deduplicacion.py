import math
import random

import pytest

from simbolicalab.conjuntos import kepler_real
from simbolicalab.nucleo import Contador
from simbolicalab.rs import (
    Const, Gramatica, Op, Var, deduplicar_cuadratico, deduplicar_exacta, deduplicar_rejilla,
    enumerar, error_relativo_medio, firma, todas_distintas,
)


def test_la_cercania_no_es_transitiva_y_el_resultado_depende_del_orden():
    a, b, c = (0.0,), (0.9,), (1.8,)       
    assert deduplicar_cuadratico([a, b, c], 1.0) == [0, 2]  
    assert deduplicar_cuadratico([b, a, c], 1.0) == [0]      


def test_firmas_indefinidas_se_descartan_y_no_cuentan():
    assert deduplicar_cuadratico([(1.0,), None, (2.0,), None], 0.0) == [0, 2]


def test_eps_cero_es_igualdad_exacta():
    firmas = [(1.0, 2.0), (1.0, 2.0), (1.0, 2.0000001)]
    assert deduplicar_cuadratico(firmas, 0.0) == [0, 2]


def test_a_distancia_exactamente_eps_cuenta_como_repetida():
    firmas = [(0.0,), (1.0,)]
    assert deduplicar_cuadratico(firmas, 1.0) == [0]
    assert deduplicar_rejilla(firmas, 1.0) == [0]


def test_entradas_invalidas():
    with pytest.raises(ValueError):
        deduplicar_cuadratico([(1.0,)], -1.0)
    with pytest.raises(ValueError):
        deduplicar_cuadratico([(1.0,), (1.0, 2.0)], 0.5)
    with pytest.raises(ValueError):
        deduplicar_rejilla([(1.0,)], math.inf)


def test_la_firma_de_formulas_equivalentes_coincide():
    x = Var("x")
    f1 = Op("+", (x, Const(1.0)))
    f2 = Op("+", (Const(1.0), x))
    pts = [0.5, 1.0, 2.0, 7.0]
    assert firma(f1, "x", pts) == firma(f2, "x", pts)
    assert firma(Op("/", (Const(1.0), x)), "x", [0.0, 1.0]) is None       
    assert firma(Op("sqrt", (x,)), "x", [-1.0]) is None

def firmas_con_cercanas(rng, n, k, eps):
    """Firmas al azar, con duplicados exactos, casi-duplicados y algunas indefinidas."""
    base = [tuple(rng.uniform(0, 10) for _ in range(k)) for _ in range(max(1, n // 3))]
    salida = []
    for _ in range(n):
        r = rng.random()
        if r < 0.05:
            salida.append(None)
        elif r < 0.35:
            salida.append(rng.choice(base))                                         
        elif r < 0.65:
            b = rng.choice(base)
            salida.append(tuple(v + rng.uniform(-eps, eps) * 0.5 for v in b))        
        else:
            salida.append(tuple(rng.uniform(0, 10) for _ in range(k)))
    return salida


@pytest.mark.parametrize("k", [1, 2, 3, 4])
def test_rejilla_igual_al_oraculo(k):
    rng = random.Random(100 + k)
    for _ in range(60):
        eps = rng.choice([0.05, 0.3, 1.0])
        firmas = firmas_con_cercanas(rng, rng.randint(0, 60), k, eps)
        assert deduplicar_rejilla(firmas, eps) == deduplicar_cuadratico(firmas, eps)


def test_exacta_igual_al_oraculo_con_eps_cero():
    rng = random.Random(7)
    for _ in range(100):
        firmas = firmas_con_cercanas(rng, rng.randint(0, 50), 2, 0.0)
        assert deduplicar_exacta(firmas) == deduplicar_cuadratico(firmas, 0.0)
        assert deduplicar_rejilla(firmas, 0.0) == deduplicar_cuadratico(firmas, 0.0)


def test_valores_enormes_respecto_a_eps_siguen_siendo_correctos():
    rng = random.Random(3)
    for _ in range(40):
        firmas = [(rng.choice([1.0, 1e300, 1e20]) + rng.uniform(-1e-3, 1e-3) * rng.choice([0, 1]),
                   rng.choice([2.0, 5.0])) for _ in range(30)]
        assert deduplicar_rejilla(firmas, 1e-2) == deduplicar_cuadratico(firmas, 1e-2)


def test_frontera_del_rango_de_la_rejilla():
    limite = 2.0 ** 50                           
    for firmas in ([(limite,), (limite - 0.5,)], [(limite - 0.5,), (limite,)]):
        assert deduplicar_cuadratico(firmas, 1.0) == [0]
        assert deduplicar_rejilla(firmas, 1.0) == [0]


def par_a_ambos_lados_de_una_frontera(eps):
    return [(0.999 * eps,), (1.001 * eps,)]      


def test_radio_cero_es_un_error_que_se_ve_con_la_entrada_adecuada():
    firmas = par_a_ambos_lados_de_una_frontera(1.0)
    assert deduplicar_cuadratico(firmas, 1.0) == [0]            
    assert deduplicar_rejilla(firmas, 1.0, radio=1) == [0]      
    assert deduplicar_rejilla(firmas, 1.0, radio=0) == [0, 1]  


def test_radio_cero_pasa_pruebas_al_azar_cuando_no_hay_pares_cercanos():
    """Puntos uniformes y eps minúsculo: casi no hay pares cercanos, y entonces
    el algoritmo ROTO es indistinguible del correcto. La prueba no ve el error."""
    rng = random.Random(1)
    discrepancias = 0
    for _ in range(100):
        firmas = [tuple(rng.uniform(0, 1) for _ in range(2)) for _ in range(50)]
        if deduplicar_rejilla(firmas, 1e-9, radio=0) != deduplicar_cuadratico(firmas, 1e-9):
            discrepancias += 1
    assert discrepancias == 0


def test_radio_cero_si_se_ve_cuando_hay_muchos_pares_cercanos():
    rng = random.Random(2)
    discrepancias = 0
    for _ in range(100):
        firmas = firmas_con_cercanas(rng, 60, 2, 0.5)
        if deduplicar_rejilla(firmas, 0.5, radio=0) != deduplicar_cuadratico(firmas, 0.5):
            discrepancias += 1
    assert discrepancias > 30


def test_rejilla_hace_exactamente_3_a_la_k_accesos_por_firma_distinta():
    for k in (1, 2, 3):
        rng = random.Random(k)
        firmas = [tuple(rng.uniform(0, 1e6) for _ in range(k)) for _ in range(40)]   # todas lejanas
        c = Contador()
        assert len(deduplicar_rejilla(firmas, 1e-6, c)) == 40
        assert c.por_categoria["acceso_hash"] == 40 * 3 ** k


def test_cuadratico_hace_n_por_n_menos_1_entre_2_comparaciones_si_todas_son_distintas():
    firmas = [(float(i),) for i in range(50)]
    c = Contador()
    deduplicar_cuadratico(firmas, 0.1, c)
    assert c.total == 50 * 49 // 2


def test_la_rejilla_gana_en_dimension_baja_y_pierde_en_alta():
    rng = random.Random(5)
    costo = {}
    for k in (1, 6):
        firmas = [tuple(rng.uniform(0, 100) for _ in range(k)) for _ in range(300)]
        cq, cr = Contador(), Contador()
        deduplicar_cuadratico(firmas, 0.5, cq)
        deduplicar_rejilla(firmas, 0.5, cr)
        costo[k] = (cq.total, cr.total)
    assert costo[1][1] < costo[1][0] / 5          
    assert costo[6][1] > costo[6][0]              

def test_todas_distintas_coincide_con_comparar_con_un_conjunto():
    rng = random.Random(9)
    for _ in range(200):
        xs = [rng.randint(0, 30) for _ in range(rng.randint(0, 25))]
        assert todas_distintas(xs) == (len(set(xs)) == len(xs))


def test_distincion_de_elementos_es_deduplicar_con_k_1_y_eps_0():
    assert deduplicar_cuadratico([(1.0,), (2.0,), (3.0,)], 0.0) == [0, 1, 2]    
    assert deduplicar_cuadratico([(1.0,), (2.0,), (1.0,)], 0.0) == [0, 1]         


def test_la_version_hash_cuesta_un_acceso_por_elemento():
    c = Contador()
    todas_distintas(list(range(1000)), c)
    assert c.total == 1000

@pytest.fixture(scope="module")
def formulas_y_datos():
    g, d = Gramatica(variables=("a",)), kepler_real()
    return list(enumerar(g, 5)), d


def test_deduplicar_no_pierde_la_mejor_formula(formulas_y_datos):
    formulas, d = formulas_y_datos
    sigs = [firma(e, "a", d.xs) for e in formulas]
    reps = deduplicar_cuadratico(sigs, 1e-9)
    mejor = lambda lista: min(error_relativo_medio(formulas[i], d) for i in lista)
    todas_definidas = [i for i, s in enumerate(sigs) if s is not None]
    assert abs(mejor(reps) - mejor(todas_definidas)) < 1e-6
    assert len(reps) < len(todas_definidas) / 3


def test_el_representante_es_el_mas_pequeno(formulas_y_datos):
    from simbolicalab.rs import tamano
    formulas, d = formulas_y_datos
    sigs = [firma(e, "a", d.xs) for e in formulas]
    reps = deduplicar_cuadratico(sigs, 1e-9)
    tamanos = [tamano(formulas[i]) for i in reps]
    assert tamanos == sorted(tamanos)
