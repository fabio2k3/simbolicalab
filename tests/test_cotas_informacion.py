"""
tests/test_cotas_informacion.py  —  Información, árboles de decisión y ordenamiento
===================================================================================
"""
import itertools
import json
import math
import random

import pytest

from simbolicalab.conjuntos import kepler_real
from simbolicalab.cotas.informacion import (
    Elemento, arbol_de_decision, cota_de_informacion, cota_de_ordenar,
)
from simbolicalab.cotas.ordenamiento import (
    frente_de_pareto, frente_de_pareto_cuadratico, insercion, mergesort, ordenar_por_conteo,
    ordenar_por_error, peor_caso_exacto,
)
from simbolicalab.nucleo import Contador
from simbolicalab.rs import (
    Gramatica, a_cadena, deduplicar_cuadratico, enumerar, error_relativo_medio, firma, tamano,
)


# ------------------------------------------------------------------ la cota de información

def test_cota_de_informacion_valores():
    assert [cota_de_informacion(s) for s in (1, 2, 3, 4, 5, 8, 9)] == [0, 1, 2, 2, 3, 3, 4]
    assert cota_de_informacion(27, 3) == 3 and cota_de_informacion(28, 3) == 4


def test_cota_de_informacion_argumentos_invalidos():
    with pytest.raises(ValueError):
        cota_de_informacion(0)
    with pytest.raises(ValueError):
        cota_de_informacion(5, 1)


def test_la_cota_es_el_menor_h_con_r_a_la_h_mayor_o_igual():
    for r in (2, 3, 5):
        for salidas in range(1, 300):
            h = cota_de_informacion(salidas, r)
            assert r ** h >= salidas and (h == 0 or r ** (h - 1) < salidas)


def test_cota_de_ordenar_coincide_con_una_derivacion_independiente():
    assert [cota_de_ordenar(n) for n in range(2, 9)] == [1, 3, 5, 7, 10, 13, 16]
    for n in range(2, 300):
        assert cota_de_ordenar(n) == (math.factorial(n) - 1).bit_length()      # ⌈log2 m⌉ = bits de (m-1)


def test_la_cota_de_ordenar_es_n_log_n_menos_1443_n():
    for n in range(2, 400):
        assert n * math.log2(n) - 1.443 * n <= cota_de_ordenar(n) <= n * math.log2(n)


# ------------------------------------------------------------------ los árboles de decisión

def ordenado(algoritmo, valores):
    return [e.valor for e in algoritmo([Elemento(v, i) for i, v in enumerate(valores)], lambda a, b: a.valor < b.valor)]


@pytest.mark.parametrize("algoritmo", [insercion, mergesort])
def test_los_algoritmos_ordenan_incluso_con_repetidos(algoritmo):
    rng = random.Random(1)
    for _ in range(100):
        v = [rng.randint(0, 6) for _ in range(rng.randint(0, 12))]
        assert ordenado(algoritmo, v) == sorted(v)


def test_mergesort_es_estable():
    elementos = [Elemento(1, 0), Elemento(0, 1), Elemento(1, 2), Elemento(0, 3)]
    salida = mergesort(elementos, lambda a, b: a.valor < b.valor)
    assert [e.posicion for e in salida] == [1, 3, 0, 2]


def test_peor_caso_exacto_de_mergesort_es_el_conocido_y_esta_a_una_de_la_cota():
    medido = [peor_caso_exacto(mergesort, n) for n in range(2, 9)]
    assert medido == [1, 3, 5, 8, 11, 14, 17]
    cotas = [cota_de_ordenar(n) for n in range(2, 9)]
    assert all(m >= c and m - c <= 1 for m, c in zip(medido, cotas))


def test_el_peor_caso_de_la_insercion_es_cuadratico():
    assert [peor_caso_exacto(insercion, n) for n in range(2, 8)] == [n * (n - 1) // 2 for n in range(2, 8)]


@pytest.mark.parametrize("algoritmo", [insercion, mergesort])
def test_el_arbol_tiene_n_factorial_hojas_y_altura_al_menos_la_cota(algoritmo):
    for n in range(2, 6):
        a = arbol_de_decision(algoritmo, n)
        assert a.hojas == math.factorial(n)                       # lema 2: una hoja por cada orden
        assert a.altura >= cota_de_ordenar(n)                      # lema 3
        assert a.hojas <= 2 ** a.altura                            # lema 1


def test_los_arboles_de_la_figura_clasica():
    a = arbol_de_decision(insercion, 3)
    assert (a.altura, a.hojas) == (3, 6)                           # óptimo: ⌈log2 6⌉ = 3
    b = arbol_de_decision(mergesort, 4)
    assert b.altura == 5 == cota_de_ordenar(4)                     # mergesort alcanza la cota en n = 4


def test_el_arbol_como_diccionario_es_binario_completo_y_serializable():
    a = arbol_de_decision(insercion, 3)
    arbol = a.como_dict()
    json.dumps(arbol)

    def contar(nodo):
        if "salida" in nodo:
            return 1, 0
        h1, i1 = contar(nodo["si"])
        h2, i2 = contar(nodo["no"])
        return h1 + h2, i1 + i2 + 1

    hojas, internos = contar(arbol)
    assert hojas == 6 and internos == hojas - 1
    salidas = []

    def recoger(nodo):
        if "salida" in nodo:
            salidas.append(tuple(nodo["salida"]))
        else:
            recoger(nodo["si"])
            recoger(nodo["no"])

    recoger(arbol)
    assert sorted(salidas) == sorted(itertools.permutations(range(3)))


def test_el_modelo_se_hace_cumplir_no_se_puede_mirar_el_valor_sin_preguntar():
    """Un 'algoritmo' que lee los valores directamente (sin `menor`) rompe el modelo: el árbol lo detecta."""
    def tramposo(lista, menor):
        return sorted(lista, key=lambda e: e.valor)

    with pytest.raises(AssertionError, match="solo de las respuestas"):
        arbol_de_decision(tramposo, 3)


# ------------------------------------------------------------------ ordenar fórmulas por error

def test_ordenar_por_error_ordena_y_cuenta_comparaciones():
    rng = random.Random(2)
    for n in (1, 2, 10, 300):
        errores = [rng.random() for _ in range(n)]
        c = Contador()
        orden = ordenar_por_error(errores, c)
        assert [errores[i] for i in orden] == sorted(errores)
        assert c.por_categoria.get("comparacion", 0) <= max(n * math.ceil(math.log2(n)) if n > 1 else 0, 0)


def test_las_comparaciones_de_mergesort_estan_cerca_de_la_cota():
    n = 1000
    errores = [random.Random(i).random() for i in range(n)]
    c = Contador()
    ordenar_por_error(errores, c)
    cota = cota_de_ordenar(n)
    assert 0.9 * cota <= c.total <= 1.1 * cota


# ------------------------------------------------------------------ salir del modelo: ordenar por conteo

def test_ordenar_por_conteo_es_correcto_y_estable():
    rng = random.Random(4)
    for _ in range(100):
        claves = [rng.randint(0, 9) for _ in range(rng.randint(0, 40))]
        assert ordenar_por_conteo(claves, 9) == sorted(range(len(claves)), key=lambda i: claves[i])


def test_ordenar_por_conteo_cuesta_2n_mas_k_mas_1_y_no_compara_nada():
    claves = [i % 7 for i in range(1000)]
    c = Contador()
    ordenar_por_conteo(claves, 6, c)
    assert c.total == 2 * 1000 + 6 + 1 and "comparacion" not in c.por_categoria


def test_el_conteo_baja_por_debajo_de_la_cota_de_comparaciones_sin_contradecirla():
    n = 5000
    c = Contador()
    ordenar_por_conteo([i % 12 for i in range(n)], 11, c)
    assert c.total < cota_de_ordenar(n) / 4                         # la cota habla de OTRO modelo


def test_ordenar_por_conteo_rechaza_claves_fuera_de_rango():
    with pytest.raises(ValueError):
        ordenar_por_conteo([0, 5], 4)


# ------------------------------------------------------------------ el frente de Pareto

def test_el_frente_lineal_coincide_con_la_definicion_cuadratica():
    rng = random.Random(5)
    for _ in range(300):
        n = rng.randint(1, 25)
        tamanos = [rng.randint(1, 6) for _ in range(n)]
        errores = [float(rng.randint(0, 6)) for _ in range(n)]          # con muchos empates a propósito
        assert frente_de_pareto(tamanos, errores) == frente_de_pareto_cuadratico(tamanos, errores)


def test_el_frente_cuesta_n_mas_s_y_es_monotono():
    tamanos = [1, 2, 2, 3, 3, 3, 5]
    errores = [9.0, 5.0, 6.0, 5.0, 4.0, 7.0, 1.0]
    c = Contador()
    frente = frente_de_pareto(tamanos, errores, c)
    assert c.total == len(tamanos) + max(tamanos)
    assert [tamanos[i] for i in frente] == sorted(tamanos[i] for i in frente)
    assert all(errores[a] > errores[b] for a, b in zip(frente, frente[1:]))
    assert frente == [0, 1, 4, 6]


def test_el_frente_casos_borde_y_errores():
    assert frente_de_pareto([], []) == []
    assert frente_de_pareto([3], [1.0]) == [0]
    with pytest.raises(ValueError):
        frente_de_pareto([0, 1], [1.0, 2.0])


def test_el_frente_de_kepler_tiene_dos_puntos_y_uno_es_la_ley():
    g, d = Gramatica(variables=("a",)), kepler_real()
    formulas = list(enumerar(g, 5))
    firmas = [firma(e, "a", d.xs) for e in formulas]
    reps = [formulas[i] for i in deduplicar_cuadratico(firmas, 1e-9)]      # equivalentes fuera ANTES del frente
    tam = [tamano(e) for e in reps]
    err = [error_relativo_medio(e, d) for e in reps]
    frente = frente_de_pareto(tam, err)
    assert frente == frente_de_pareto_cuadratico(tam, err)
    assert [a_cadena(reps[i]) for i in frente] == ["a", "a * sqrt(a)"]
    assert [tam[i] for i in frente] == [1, 4]


def test_sin_quitar_las_equivalentes_el_ruido_de_redondeo_ensucia_el_frente():
    """La advertencia del módulo, comprobada: con todas las fórmulas el frente tiene MÁS puntos
    (fórmulas equivalentes mayores 'mejoran' por 1e-17), con los representantes solo la ley."""
    g, d = Gramatica(variables=("a",)), kepler_real()
    formulas = [e for e in enumerar(g, 6) if firma(e, "a", d.xs) is not None]
    tam = [tamano(e) for e in formulas]
    err = [error_relativo_medio(e, d) for e in formulas]
    assert len(frente_de_pareto(tam, err)) > 2
