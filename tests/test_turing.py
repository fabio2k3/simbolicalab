import itertools

import pytest

from simbolicalab.costo.turing import (
    MaquinaTuring, incrementar_k_veces, maquina_incremento, maquina_palindromo, palindromo_ram,
)
from simbolicalab.nucleo import Contador, PresupuestoAgotado, Traza


def cadenas_binarias(max_n):
    for n in range(max_n + 1):
        for bits in itertools.product("01", repeat=n):
            yield "".join(bits)


def test_palindromo_decide_bien_todas_las_cadenas_hasta_12():
    m = maquina_palindromo()
    for s in cadenas_binarias(12):
        assert m.ejecutar(s).aceptada == (s == s[::-1]), s


def test_un_palindromo_cuesta_exactamente_n_mas_1_por_n_mas_2_entre_2():
    m = maquina_palindromo()
    for s in cadenas_binarias(12):
        if s == s[::-1]:
            n = len(s)
            assert m.ejecutar(s).pasos == (n + 1) * (n + 2) // 2, s


def test_un_no_palindromo_termina_antes_o_igual():
    m = maquina_palindromo()
    for s in cadenas_binarias(10):
        if s != s[::-1]:
            n = len(s)
            assert m.ejecutar(s).pasos < (n + 1) * (n + 2) // 2


def test_palindromo_turing_es_cuadratico_y_ram_es_lineal():
    m = maquina_palindromo()
    for n in (100, 200, 400):
        mitad = "01" * (n // 4)
        s = mitad + mitad[::-1]                       
        r = m.ejecutar(s)
        c = Contador()
        assert palindromo_ram(s, c)
        assert c.total == n // 2
        assert r.pasos == (n + 1) * (n + 2) // 2
        assert r.pasos / c.total > n                 


def test_la_traza_tiene_un_evento_por_paso():
    t = Traza()
    r = maquina_palindromo().ejecutar("0110", traza=t)
    assert len(t) == r.pasos
    assert t.eventos[0].tipo == "paso" and t.eventos[0].datos["estado"] == "inicio"


def test_incremento_suma_uno_a_todos_los_numeros_hasta_2000():
    m = maquina_incremento()
    for k in range(2001):
        binario = bin(k)[2:]
        r = m.ejecutar(binario, cabezal=len(binario) - 1)
        assert int(r.cinta, 2) == k + 1, k
        assert r.cabezal == len(r.cinta) - 1       


def test_incremento_cuesta_2t_mas_2_donde_t_son_los_unos_finales():
    m = maquina_incremento()
    for k in range(1000):
        binario = bin(k)[2:]
        t = len(binario) - len(binario.rstrip("1"))
        r = m.ejecutar(binario, cabezal=len(binario) - 1)
        assert r.pasos == 2 * t + 2, k


def test_peor_caso_de_un_incremento_es_lineal_en_los_bits():
    m = maquina_incremento()
    for n in (4, 16, 64):
        r = m.ejecutar("1" * n, cabezal=n - 1)
        assert r.pasos == 2 * n + 2 and r.cinta == "1" + "0" * n


def test_k_incrementos_desde_cero_cuestan_4k_menos_2_popcount():
    for k in list(range(0, 300)) + [511, 512, 1000, 1023]:
        assert incrementar_k_veces(k) == 4 * k - 2 * bin(k).count("1"), k


def test_el_promedio_por_incremento_queda_por_debajo_de_4():
    k = 5000
    assert incrementar_k_veces(k) / k < 4


def test_transicion_que_falta_es_un_error_de_diseno():
    m = MaquinaTuring({("q", "0"): ("0", "R", "fin")}, "q", frozenset({"fin"}), frozenset({"fin"}))
    assert m.ejecutar("0").aceptada
    with pytest.raises(ValueError):
        m.ejecutar("1")


def test_limite_de_pasos_evita_ciclos_infinitos():
    ciclo = MaquinaTuring({("q", "_"): ("_", "S", "q")}, "q", frozenset({"fin"}), frozenset({"fin"}))
    with pytest.raises(PresupuestoAgotado):
        ciclo.ejecutar("", limite_pasos=100)


def test_el_contador_con_limite_tambien_corta():
    with pytest.raises(PresupuestoAgotado):
        maquina_palindromo().ejecutar("0" * 50, contador=Contador(limite=100))


def test_validacion_de_la_definicion():
    with pytest.raises(ValueError):
        MaquinaTuring({("q", "0"): ("0", "X", "q")}, "q", frozenset({"f"}), frozenset({"f"}))
    with pytest.raises(ValueError):
        MaquinaTuring({}, "q", frozenset({"f"}), frozenset({"otro"}))
