import itertools
import math
import random

import pytest

from simbolicalab.conjuntos import kepler_real
from simbolicalab.estructuras.clases_formulas import (
    clases_por_conmutatividad, intercambios, reduccion_por_simetria,
)
from simbolicalab.estructuras.union_find import UnionFind
from simbolicalab.nucleo import Contador, tasa_de_deteccion
from simbolicalab.rs import Const, Gramatica, Op, Var, enumerar, firma
from simbolicalab.rs.operadores import OPERADORES

CONFIGURACIONES = [
    dict(por_rango=False, compresion=False),
    dict(por_rango=True, compresion=False),
    dict(por_rango=False, compresion=True),
    dict(por_rango=True, compresion=True),
    dict(por_rango=True, compresion=True, rango_en_empate=False),       
]


def particion_ingenua(n, uniones):
    """Oráculo: etiquetas por propagación, sin ninguna estructura inteligente."""
    etiqueta = list(range(n))
    for a, b in uniones:
        viejo, nuevo = etiqueta[b], etiqueta[a]
        etiqueta = [nuevo if e == viejo else e for e in etiqueta]
    return etiqueta


@pytest.mark.parametrize("config", CONFIGURACIONES)
def test_las_clases_coinciden_con_el_oraculo_incluso_con_el_error_plantado(config):
    rng = random.Random(7)
    for _ in range(40):
        n = rng.randint(1, 40)
        uniones = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 60))]
        uf = UnionFind(n, **config)
        for a, b in uniones:
            uf.union(a, b)
        etiqueta = particion_ingenua(n, uniones)
        for a, b in itertools.combinations(range(n), 2):
            assert (uf.find(a) == uf.find(b)) == (etiqueta[a] == etiqueta[b])
        assert uf.conjuntos == len(set(etiqueta))


def test_union_devuelve_si_hubo_fusion():
    uf = UnionFind(4)
    assert uf.union(0, 1) and not uf.union(1, 0) and uf.conjuntos == 3


def test_sin_heuristicas_un_find_cuesta_n_menos_1():
    n = 500
    uf = UnionFind(n, por_rango=False, compresion=False)
    for i in range(n - 1):
        uf.union(i + 1, i)
    antes = uf.contador.total
    uf.find(0)
    assert uf.contador.total - antes == n - 1


def binomial(uf, n):
    tam = 1
    while tam < n:
        for i in range(0, n, 2 * tam):
            uf.union(i, i + tam)
        tam *= 2


def test_con_union_por_rango_la_altura_es_log2_n_y_con_compresion_los_find_posteriores_cuestan_1():
    n = 1 << 10
    uf = UnionFind(n, compresion=False)
    binomial(uf, n)
    assert uf.altura_maxima() == 10
    hondo = max(range(n), key=uf.profundidad)
    sin_comprimir = Contador()
    uf.contador = sin_comprimir
    uf.find(hondo)
    assert sin_comprimir.total == 10

    uf2 = UnionFind(n, compresion=True)
    binomial(uf2, n)
    hondo = max(range(n), key=uf2.profundidad)
    uf2.find(hondo)                                                   
    antes = uf2.contador.total
    uf2.find(hondo)
    assert uf2.contador.total - antes == 1                              


def test_con_las_dos_heuristicas_el_costo_medio_es_casi_constante():
    n = 1 << 12
    rng = random.Random(2)
    uf = UnionFind(n)
    for _ in range(4 * n):
        uf.union(rng.randrange(n), rng.randrange(n)) if rng.random() < 0.5 else uf.find(rng.randrange(n))
    assert uf.contador.total / (4 * n) < 3


@pytest.mark.parametrize("compresion", [False, True])
def test_las_tres_propiedades_del_rango_se_cumplen_en_ejecuciones_grandes(compresion):
    for semilla in range(5):
        rng = random.Random(semilla)
        n = 1 << 11
        uf = UnionFind(n, compresion=compresion)
        for _ in range(3 * n):
            uf.union(rng.randrange(n), rng.randrange(n))
            uf.find(rng.randrange(n))
        uf.verificar_propiedades()
        if not compresion:
            assert uf.altura_maxima() <= math.log2(n)                      


def test_el_error_plantado_forma_una_cadena_y_la_propiedad_P1_lo_atrapa_de_inmediato():
    n = 400
    malo = UnionFind(n, compresion=False, rango_en_empate=False)
    for i in range(n - 1):
        malo.union(i + 1, i)
    assert malo.altura_maxima() == n - 1                                  
    with pytest.raises(AssertionError, match="P1"):
        malo.verificar_propiedades()
    bueno = UnionFind(n, compresion=False)
    for i in range(n - 1):
        bueno.union(i + 1, i)
    bueno.verificar_propiedades()
    assert bueno.altura_maxima() <= math.log2(n)


def test_las_pruebas_de_valores_no_ven_el_error_pero_medir_la_altura_si():
    def entrada(rng):
        return [(i + 1, i) for i in range(rng.randint(50, 120))]

    def clases(rango_en_empate):
        def f(uniones):
            n = len(uniones) + 1
            uf = UnionFind(n, compresion=False, rango_en_empate=rango_en_empate)
            for a, b in uniones:
                uf.union(a, b)
            return sorted(len(m) for m in uf.clases().values())
        return f

    def altura(rango_en_empate):
        def f(uniones):
            n = len(uniones) + 1
            uf = UnionFind(n, compresion=False, rango_en_empate=rango_en_empate)
            for a, b in uniones:
                uf.union(a, b)
            return uf.altura_maxima()
        return f

    assert tasa_de_deteccion(entrada, clases(True), clases(False), 30).detectadas == 0    
    assert tasa_de_deteccion(entrada, altura(True), altura(False), 30).tasa == 1.0         


def test_cada_propiedad_atrapa_su_propia_corrupcion():
    uf = UnionFind(4)
    uf.rango[0] = 2                                  
    with pytest.raises(AssertionError, match="P2"):
        uf.verificar_propiedades()

    uf = UnionFind(4)
    uf.padre[1] = 0                                  
    with pytest.raises(AssertionError, match="P1"):
        uf.verificar_propiedades()

    uf = UnionFind(8)
    for i in range(8):
        uf.rango[i] = 1                              
    with pytest.raises(AssertionError):
        uf.verificar_propiedades()


def test_parametros_invalidos_y_caso_vacio():
    with pytest.raises(ValueError):
        UnionFind(-1)
    uf = UnionFind(0)
    uf.verificar_propiedades()
    assert uf.altura_maxima() == 0


X = Var("x")


def test_intercambios_solo_en_operadores_conmutativos():
    assert set(intercambios(Op("+", (X, Const(1.0))))) == {Op("+", (Const(1.0), X))}
    assert list(intercambios(Op("-", (X, Const(1.0))))) == []            
    assert list(intercambios(X)) == []
    anidada = Op("*", (Op("+", (X, Const(1.0))), Const(2.0)))
    assert set(intercambios(anidada)) == {
        Op("*", (Const(2.0), Op("+", (X, Const(1.0))))),
        Op("*", (Op("+", (Const(1.0), X)), Const(2.0))),
    }


def forma_canonica(e):
    if not isinstance(e, Op):
        return e
    hijos = tuple(forma_canonica(h) for h in e.hijos)
    if OPERADORES[e.nombre].conmutativo and len(hijos) == 2:
        hijos = tuple(sorted(hijos, key=repr))
    return Op(e.nombre, hijos)


@pytest.mark.parametrize("max_tam", [3, 4, 5, 6])
def test_el_numero_de_clases_coincide_con_la_forma_canonica(max_tam):
    formulas = list(enumerar(Gramatica(variables=("a",)), max_tam))
    esperado = len({forma_canonica(e) for e in formulas})
    assert clases_por_conmutatividad(formulas).conjuntos == esperado


def test_las_clases_son_seguras_misma_clase_implica_misma_firma():
    d = kepler_real()
    formulas = list(enumerar(Gramatica(variables=("a",)), 5))
    sig = [firma(e, "a", d.xs) for e in formulas]
    for miembros in clases_por_conmutatividad(formulas).clases().values():
        assert len({sig[i] for i in miembros}) == 1


def test_son_incompletas_x_mas_x_y_2_por_x_son_la_misma_funcion_pero_otra_clase():
    g = Gramatica(variables=("x",), constants=(2.0,))
    formulas = list(enumerar(g, 3))
    uf = clases_por_conmutatividad(formulas)
    a = formulas.index(Op("+", (X, X)))
    b = formulas.index(Op("*", (Const(2.0), X)))
    assert uf.find(a) != uf.find(b)
    pts = (1.0, 2.0, 3.0)
    assert firma(formulas[a], "x", pts) == firma(formulas[b], "x", pts)


def test_la_simetria_colapsa_una_fraccion_apreciable_del_espacio():
    formulas = list(enumerar(Gramatica(variables=("a",)), 6))
    n, clases = reduccion_por_simetria(formulas)
    assert n == 5922 and clases == 3708


def test_formulas_repetidas_son_un_error():
    with pytest.raises(ValueError):
        clases_por_conmutatividad([X, X])
