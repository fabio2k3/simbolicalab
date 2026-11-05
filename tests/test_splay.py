import math
import random

import pytest

from simbolicalab.estructuras.splay import ArbolSplay, verificar_lema_de_acceso
from simbolicalab.nucleo import tasa_de_deteccion

HEURISTICAS = ["splay", "raiz"]


def camino(n, heuristica):
    t = ArbolSplay(heuristica)
    for k in range(1, n + 1):
        t.insertar(k, k * 10)
    return t


@pytest.mark.parametrize("heuristica", HEURISTICAS)
def test_se_comporta_como_un_diccionario_ordenado(heuristica):
    rng = random.Random(5)
    t, modelo = ArbolSplay(heuristica), {}
    for _ in range(600):
        k = rng.randint(0, 80)
        if rng.random() < 0.5:
            nuevo = t.insertar(k, k * 3)
            assert nuevo == (k not in modelo)
            modelo[k] = k * 3
        else:
            assert t.buscar(k) == modelo.get(k)
        t.verificar()
    assert t.en_orden() == sorted(modelo.items()) and len(t) == len(modelo)


@pytest.mark.parametrize("heuristica", HEURISTICAS)
def test_el_nodo_accedido_queda_en_la_raiz(heuristica):
    t = ArbolSplay(heuristica)
    for k in random.Random(1).sample(range(100), 40):
        t.insertar(k)
    for k in (t.en_orden()[7][0], t.en_orden()[30][0]):
        t.buscar(k)
        assert t.raiz.clave == k
    t.buscar(1000)                                   
    assert t.raiz.clave == t.en_orden()[-1][0]      
    t.verificar()


def test_arbol_vacio_y_claves_ausentes():
    t = ArbolSplay()
    assert t.buscar(3) is None and t.acceso_instrumentado(3) is None and t.potencial() == 0 and len(t) == 0
    t.insertar(1)
    assert t.acceso_instrumentado(7) is None


def test_la_heuristica_es_validada():
    with pytest.raises(ValueError):
        ArbolSplay("otra")


def test_insertar_en_orden_deja_un_camino_con_potencial_log2_factorial():
    t = camino(30, "splay")
    assert t.altura() == 30 and t.raiz.clave == 30
    assert t.potencial() == pytest.approx(math.lgamma(31) / math.log(2))


def test_el_primer_acceso_al_fondo_de_un_camino_cuesta_theta_de_n_aun_con_splay():
    n = 200
    t = camino(n, "splay")
    antes = t.contador.por_categoria["rotacion"]
    t.buscar(1)
    assert t.contador.por_categoria["rotacion"] - antes == n - 1


def costo_por_acceso(heuristica, n, rondas=3):
    t = camino(n, heuristica)
    total = 0
    for _ in range(rondas):
        for k in range(1, n + 1):
            antes = t.contador.por_categoria["rotacion"]
            t.buscar(k)
            total += max(t.contador.por_categoria["rotacion"] - antes, 1)
    return total / (rondas * n)


def test_en_orden_splay_es_constante_y_subir_a_la_raiz_es_lineal():
    s = [costo_por_acceso("splay", n) for n in (100, 200, 400)]
    r = [costo_por_acceso("raiz", n) for n in (100, 200, 400)]
    assert max(s) < 6 and max(s) - min(s) < 0.5          # constante
    for n, c in zip((100, 200, 400), r):
        assert c == pytest.approx(n / 2, rel=0.02)       # Θ(n) por acceso


def test_splay_rota_menos_que_subir_a_la_raiz_a_la_larga():
    assert costo_por_acceso("splay", 300) * 20 < costo_por_acceso("raiz", 300)


def test_acceder_a_la_raiz_cuesta_1_y_no_0():
    t = camino(10, "splay")
    a = t.acceso_instrumentado(t.raiz.clave)
    assert a["rotaciones"] == 0 and a["costo"] == 1


def test_el_lema_de_acceso_se_cumple_siempre_para_splay():
    for semilla in range(6):
        rng = random.Random(semilla)
        n = rng.randint(20, 70)
        t = camino(n, "splay")
        claves = [rng.randint(1, n) if i % 2 else (i // 2) % n + 1 for i in range(500)]
        assert verificar_lema_de_acceso(t, claves) == [], semilla
    t = camino(60, "splay")
    assert verificar_lema_de_acceso(t, list(range(1, 61)) * 3) == []


def test_el_lema_se_viola_al_subir_a_la_raiz():
    random.seed(4)
    n = 60
    t = camino(n, "raiz")
    claves = [random.randint(1, n) if i % 2 else (i // 2) % n + 1 for i in range(1500)]
    violaciones = verificar_lema_de_acceso(t, claves)
    assert 1 <= len(violaciones) < 50                       
    assert max(v["exceso"] for v in violaciones) > 10       


def test_en_orden_las_violaciones_se_repiten():
    t = camino(60, "raiz")
    assert len(verificar_lema_de_acceso(t, list(range(1, 61)) * 3)) > 100


def test_el_lema_funciona_como_detector_de_la_heuristica_incorrecta():
    def entrada(rng):
        n = rng.randint(30, 60)
        return [(n, [(i % n) + 1 for i in range(3 * n)])]

    def valores(heuristica):
        def f(caso):
            n, claves = caso[0]
            t = camino(n, heuristica)
            return [t.buscar(k) for k in claves]
        return f

    def violaciones(heuristica):
        def f(caso):
            n, claves = caso[0]
            return len(verificar_lema_de_acceso(camino(n, heuristica), claves)) > 0
        return f

    assert tasa_de_deteccion(entrada, valores("splay"), valores("raiz"), 20).detectadas == 0
    assert tasa_de_deteccion(entrada, violaciones("splay"), violaciones("raiz"), 20).tasa == 1.0
