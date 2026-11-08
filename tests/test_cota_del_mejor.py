import random

import pytest

from simbolicalab.conjuntos import kepler_real
from simbolicalab.cotas.adversario import (
    evaluar_todas, jugar_contra_el_adversario, mejor_formula, mirar_solo_la_mitad,
    saltar_la_primera, saltar_la_ultima, verificar_instancia,
)
from simbolicalab.nucleo import Contador, tasa_de_deteccion
from simbolicalab.rs import Datos, Gramatica, deduplicar_cuadratico, enumerar, firma, tamano
from simbolicalab.solvers.fuerza_bruta import tolerancia

ATAJOS = [saltar_la_ultima, saltar_la_primera, mirar_solo_la_mitad]


def algoritmo_con_consultas(indices):
    def alg(n, consultar):
        return min(indices, key=consultar)
    return alg


def test_el_algoritmo_que_lo_evalua_todo_es_correcto():
    for n in (2, 5, 12):
        p = jugar_contra_el_adversario(evaluar_todas, n)
        assert p.consultas == n and p.correcta and p.instancia is None


@pytest.mark.parametrize("atajo", ATAJOS)
def test_todo_algoritmo_que_evalua_menos_de_n_es_refutado_con_una_instancia_concreta(atajo):
    for n in range(2, 13):
        p = jugar_contra_el_adversario(atajo, n)
        assert p.consultas < n and not p.correcta
        acierta, _ = verificar_instancia(atajo, p.instancia)        
        assert not acierta


def test_cualquier_subconjunto_propio_de_consultas_es_refutado():
    import itertools
    for n in range(2, 8):
        for k in range(1, n):
            for indices in itertools.combinations(range(n), k):
                alg = algoritmo_con_consultas(indices)
                p = jugar_contra_el_adversario(alg, n)
                assert not p.correcta and not verificar_instancia(alg, p.instancia)[0], (n, indices)


def test_la_instancia_es_consistente_con_lo_que_el_adversario_contesto():
    for atajo in ATAJOS:
        n = 9
        vistos = []

        def espia(m, consultar, atajo=atajo):
            def c(i):
                vistos.append(i)
                return consultar(i)
            return atajo(m, c)

        p = jugar_contra_el_adversario(espia, n)
        assert all(p.instancia[i] == 1.0 for i in set(vistos))      #


def test_la_instancia_cruel_hace_que_otra_candidata_sea_la_mejor():
    p = jugar_contra_el_adversario(saltar_la_ultima, 8)
    assert p.instancia.index(min(p.instancia)) == 7 and p.instancia[7] == 0.0


def test_un_caso_con_una_sola_candidata_oculta_que_es_la_elegida():
    def alg(n, consultar):
        for i in range(n - 1):
            consultar(i)
        return n - 1                                           
    p = jugar_contra_el_adversario(alg, 6)
    assert not p.correcta and p.instancia[5] == 2.0
    assert not verificar_instancia(alg, p.instancia)[0]


def test_con_menos_de_dos_candidatas_es_un_error():
    with pytest.raises(ValueError):
        jugar_contra_el_adversario(evaluar_todas, 1)


@pytest.fixture(scope="module")
def candidatas():
    g, d = Gramatica(variables=("a",)), kepler_real()
    formulas = list(enumerar(g, 4))
    firmas = [firma(e, "a", d.xs) for e in formulas]
    return [formulas[i] for i in deduplicar_cuadratico(firmas, 1e-9)], d


def datos_de(formula, d):
    return Datos(xs=d.xs, ys=tuple(firma(formula, "a", d.xs)), nombre_x="a")


def test_mejor_formula_encuentra_cualquier_ley_oculta_si_evalua_todas(candidatas):
    C, d = candidatas
    assert len(C) == 59
    for k, verdadera in enumerate(C):
        i, error = mejor_formula(C, datos_de(verdadera, d))
        assert error <= 1e-12 and i == k


def test_el_atajo_de_omitir_la_ultima_falla_en_exactamente_una_ley_de_las_59(candidatas):
    C, d = candidatas
    falla = []
    for k, verdadera in enumerate(C):
        datos = datos_de(verdadera, d)
        _, e_bien = mejor_formula(C, datos)
        _, e_mal = mejor_formula(C, datos, omitir_ultimas=1)
        if e_mal > tolerancia(e_bien) + 1e-12:
            falla.append(k)
    assert falla == [len(C) - 1]                                   


def test_una_bateria_de_leyes_al_azar_no_ve_el_atajo_pero_la_instancia_construida_si(candidatas):
    C, d = candidatas
    sin_la_ultima = C[:-1]                                         

    def ley_oculta(rng):
        return datos_de(rng.choice(sin_la_ultima), d)

    def con_ultima(rng):
        return datos_de(C[-1], d)                                 

    correcto = lambda datos: round(mejor_formula(C, datos)[1], 9)
    atajo = lambda datos: round(mejor_formula(C, datos, omitir_ultimas=1)[1], 9)
    assert tasa_de_deteccion(ley_oculta, correcto, atajo, pruebas=80).detectadas == 0
    assert tasa_de_deteccion(con_ultima, correcto, atajo, pruebas=5).tasa == 1.0


def test_el_atajo_evalua_una_candidata_menos(candidatas):
    C, d = candidatas
    c1, c2 = Contador(), Contador()
    mejor_formula(C, d, contador=c1)
    mejor_formula(C, d, contador=c2, omitir_ultimas=1)
    assert c2.total == c1.total - tamano(C[-1]) * len(d)             


def test_la_deduplicacion_sale_del_modelo_de_caja_negra_y_no_viola_la_cota():
    g, d = Gramatica(variables=("a",)), kepler_real()
    formulas = [e for e in enumerar(g, 5) if firma(e, "a", d.xs) is not None]
    firmas = [firma(e, "a", d.xs) for e in formulas]
    reps = [formulas[i] for i in deduplicar_cuadratico(firmas, 1e-9)]
    assert len(reps) == 214 and len(formulas) == 1201
    _, e_todas = mejor_formula(formulas, d, metrica="relativo")
    _, e_reps = mejor_formula(reps, d, metrica="relativo")
    assert e_todas == pytest.approx(e_reps, abs=1e-12)
