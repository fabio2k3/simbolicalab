import math
import random

import pytest

from simbolicalab.estructuras.arreglo_dinamico import ArregloDinamico
from simbolicalab.estructuras.contador_binario import analizar_incrementos, potencial_unos
from simbolicalab.costo.turing import incrementar_k_veces
from simbolicalab.nucleo import LibroAmortizado, tasa_de_deteccion


def test_el_costo_amortizado_es_real_mas_variacion_de_potencial():
    libro = LibroAmortizado()
    assert libro.registrar(costo_real=5, potencial_nuevo=2) == 7          
    assert libro.registrar(costo_real=1, potencial_nuevo=0) == -1         


def test_la_suma_se_telescopa():
    rng = random.Random(1)
    libro = LibroAmortizado(potencial_inicial=3.0)
    for _ in range(200):
        libro.registrar(rng.uniform(0, 10), rng.uniform(0, 50))
    assert libro.residuo_del_telescopio() == pytest.approx(0, abs=1e-9)
    assert libro.total_amortizado == pytest.approx(libro.total_real + libro.potencial - libro.potencial_inicial)


def test_un_potencial_que_termina_por_debajo_de_donde_empezo_no_demuestra_nada():
    """El paso que todo el mundo olvida: sin Φ_final >= Φ_inicial, Σ c puede SUPERAR a Σ ĉ."""
    libro = LibroAmortizado(potencial_inicial=10)
    libro.registrar(costo_real=1, potencial_nuevo=0)                      
    assert not libro.suma_valida()
    assert libro.total_real > libro.total_amortizado                  


def test_la_peor_operacion_no_es_la_amortizada():
    libro = LibroAmortizado()
    for real, phi in [(1, 2), (1, 4), (9, 2)]:
        libro.registrar(real, phi)
    assert libro.max_real == 9 and libro.max_amortizado < libro.max_real


@pytest.mark.parametrize("reduccion", ["nunca", "cuarto", "mitad"])
def test_se_comporta_como_una_lista(reduccion):
    rng = random.Random(3)
    a, modelo = ArregloDinamico(reduccion=reduccion), []
    for i in range(3000):
        if modelo and rng.random() < 0.45:
            assert a.pop() == modelo.pop()
        else:
            a.append(i)
            modelo.append(i)
        assert len(a) == len(modelo)
    assert a.a_lista() == modelo
    if modelo:
        assert a[0] == modelo[0] and a[len(modelo) - 1] == modelo[-1]


def test_pop_y_getitem_fuera_de_rango():
    a = ArregloDinamico()
    with pytest.raises(IndexError):
        a.pop()
    a.append(1)
    with pytest.raises(IndexError):
        a[1]


def test_metodo_agregado_las_copias_totales_son_2_a_la_log_menos_1():
    for n in range(1, 300):
        a = ArregloDinamico()
        for i in range(n):
            a.append(i)
        assert a.contador.por_categoria.get("copia", 0) == 2 ** math.ceil(math.log2(n)) - 1, n


def test_metodo_agregado_n_appends_cuestan_menos_de_3n():
    for n in (1, 10, 1000, 4097):
        a = ArregloDinamico()
        for i in range(n):
            a.append(i)
        assert a.contador.total < 3 * n


def test_metodo_de_contabilidad_el_credito_nunca_es_negativo():
    a = ArregloDinamico()
    for i in range(5000):
        a.append(i)
        assert a.credito() >= 0


def test_metodo_del_potencial_cada_append_cuesta_amortizado_a_lo_sumo_3():
    libro = LibroAmortizado()
    a = ArregloDinamico(libro=libro)
    for i in range(5000):
        a.append(i)
    assert libro.max_amortizado <= 3
    assert libro.suma_valida() and libro.residuo_del_telescopio() == pytest.approx(0, abs=1e-9)
    assert libro.max_real > 1000                                         


def test_con_reduccion_a_un_cuarto_sigue_siendo_3_amortizado():
    for semilla in range(60):
        rng = random.Random(semilla)
        libro = LibroAmortizado()
        a = ArregloDinamico(reduccion="cuarto", libro=libro)
        sube = rng.choice([0.3, 0.5, 0.7])
        for _ in range(rng.randint(1, 500)):
            if len(a) == 0 or rng.random() < sube:
                a.append(0)
            else:
                a.pop()
            assert a.potencial() >= 0
        assert libro.max_amortizado <= 3 and libro.suma_valida(), semilla


def costo(politica, secuencia):
    a = ArregloDinamico(reduccion=politica)
    for op in secuencia:
        a.append(0) if op == "a" else a.pop()
    return a.contador.total


def test_reducir_a_la_mitad_cuesta_n_por_operacion_en_el_borde():
    base = ["a"] * 1025                                                  
    alternadas = ["p", "a"] * 100
    correcta = costo("cuarto", base + alternadas) - costo("cuarto", base)
    rota = costo("mitad", base + alternadas) - costo("mitad", base)
    assert correcta == 200                                               
    assert rota > 200 * 1000                                           


def test_una_bateria_de_solo_appends_no_ve_el_error_pero_alternar_en_el_borde_si():
    def solo_appends(rng):
        return ["a"] * rng.randint(1, 600)

    def en_el_borde(rng):
        n = 2 ** rng.randint(4, 9) + 1
        return ["a"] * n + ["p", "a"] * 10

    correcto = lambda s: costo("cuarto", s)
    variante = lambda s: costo("mitad", s)
    assert tasa_de_deteccion(solo_appends, correcto, variante, 100).detectadas == 0
    assert tasa_de_deteccion(en_el_borde, correcto, variante, 100).tasa == 1.0


@pytest.mark.parametrize("factor, esperado", [(2.0, 1.0), (1.5, 2.0), (4.0, 1 / 3)])
def test_las_copias_son_aproximadamente_n_sobre_factor_menos_1(factor, esperado):
    n = 60_000
    a = ArregloDinamico(factor=factor)
    for i in range(n):
        a.append(i)
    assert a.contador.por_categoria["copia"] / n == pytest.approx(esperado, rel=0.35)


def test_un_factor_menor_copia_mas_pero_sigue_siendo_lineal():
    por_n = {}
    for n in (10_000, 40_000):
        a = ArregloDinamico(factor=1.125)
        for i in range(n):
            a.append(i)
        por_n[n] = a.contador.total / n
    assert por_n[10_000] > 3                                               
    assert por_n[40_000] == pytest.approx(por_n[10_000], rel=0.25)       


def test_argumentos_invalidos():
    with pytest.raises(ValueError):
        ArregloDinamico(factor=1.0)
    with pytest.raises(ValueError):
        ArregloDinamico(reduccion="siempre")


def test_cada_incremento_cuesta_exactamente_4_amortizado():
    for k in (1, 2, 7, 64, 1000):
        libro = analizar_incrementos(k)
        assert set(libro.costos_amortizados) == {4.0}, k


def test_el_total_es_4k_menos_2_por_los_unos_de_k():
    for k in list(range(1, 200)) + [511, 512, 1000, 4095]:
        libro = analizar_incrementos(k)
        assert libro.total_real == 4 * k - 2 * bin(k).count("1"), k
        assert libro.total_real == incrementar_k_veces(k)                   
        assert libro.suma_valida()


def test_un_incremento_suelto_puede_costar_theta_de_n_aunque_el_promedio_no():
    libro = analizar_incrementos(1000)
    assert libro.max_real >= 20 and libro.total_real / 1000 < 4


def test_potencial_unos():
    assert potencial_unos("0") == 0 and potencial_unos("10110") == 6
