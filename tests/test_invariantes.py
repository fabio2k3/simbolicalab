import itertools
import random

import pytest

from simbolicalab.conjuntos import kepler_real, kepler_sintetico
from simbolicalab.nucleo import tasa_de_deteccion
from simbolicalab.rs import (
    Const, Gramatica, InvarianteViolado, Op, Var, bien_formada, contar_por_size, cota_de_perdida,
    deduplicar_cuadratico, deduplicar_exacta, deduplicar_rejilla, enumerar, error_relativo_medio, firma,
    representante_de, tamano, verificar_enumeracion, violaciones_dedup,
)
from simbolicalab.rs.variantes_defectuosas import deduplicar_contra_todas, deduplicar_solo_ultimo

GRAMATICAS = [
    Gramatica(),
    Gramatica(variables=("a",)),
    Gramatica(variables=("x",), constants=(), unarios=(), binarios=("+",)),
    Gramatica(variables=("x", "y"), constants=(1.0,), unarios=("sqrt", "neg"), binarios=("+", "*")),
    Gramatica(variables=("x",), constants=(), unarios=("exp", "log"), binarios=()),
]


@pytest.mark.parametrize("g", GRAMATICAS)
def test_el_enumerador_real_cumple_el_invariante(g):
    niveles = verificar_enumeracion(g, 6)
    esperado = contar_por_size(g, 6)
    assert niveles == {s: esperado[s] for s in range(1, 7)}


def test_bien_formada():
    g = Gramatica()
    assert bien_formada(Op("+", (Var("x"), Const(1.0))), g)
    assert not bien_formada(Op("log", (Var("x"),)), g)                 
    assert not bien_formada(Op("sqrt", (Var("x"), Var("x"))), g)       
    assert not bien_formada(Var("z"), g)
    assert not bien_formada(Const(7.0), g)


def _saltar_un_tamano(g, max_tam, contador=None):
    por_tamano = [[]]
    for s in range(1, max_tam + 1):
        nivel = list(g.terminales) if s == 1 else []
        if s > 1:
            for nombre in g.unarios:
                nivel += [Op(nombre, (h,)) for h in por_tamano[s - 1]]
            for k in range(2, s - 1):                                  
                for izq in por_tamano[k]:
                    for der in por_tamano[s - 1 - k]:
                        nivel += [Op(n, (izq, der)) for n in g.binarios]
        por_tamano.append(nivel)
        yield from nivel


def _repetir_terminales(g, max_tam, contador=None):
    yield from g.terminales
    yield from enumerar(g, max_tam)


def _niveles_desordenados(g, max_tam, contador=None):
    todas = list(enumerar(g, max_tam))
    yield from sorted(todas, key=lambda e: -tamano(e))


def _operador_fuera_de_la_gramatica(g, max_tam, contador=None):
    lista = list(enumerar(g, max_tam))
    ultimo = [i for i, e in enumerate(lista) if tamano(e) == max_tam]
    anterior = next(e for e in lista if tamano(e) == max_tam - 1)
    lista[ultimo[-1]] = Op("log", (anterior,))
    yield from lista


def _repite_una_y_omite_otra(g, max_tam, contador=None):
    lista = list(enumerar(g, max_tam))
    nivel3 = [i for i, e in enumerate(lista) if tamano(e) == 3]
    lista[nivel3[-1]] = lista[nivel3[0]]
    yield from lista


def _termina_antes(g, max_tam, contador=None):
    yield from list(enumerar(g, max_tam))[:-5]


@pytest.mark.parametrize("roto", [
    _saltar_un_tamano, _repetir_terminales, _niveles_desordenados,
    _operador_fuera_de_la_gramatica, _termina_antes, _repite_una_y_omite_otra,
])
def test_el_verificador_atrapa_enumeradores_defectuosos(roto):
    with pytest.raises(InvarianteViolado):
        verificar_enumeracion(Gramatica(variables=("a",)), 6, enumerador=roto)


def firmas_al_azar(rng, n, k, eps):
    base = [tuple(rng.uniform(0, 10) for _ in range(k)) for _ in range(max(1, n // 3))]
    salida = []
    for _ in range(n):
        r = rng.random()
        if r < 0.1:
            salida.append(None)
        elif r < 0.4:
            salida.append(rng.choice(base))
        elif r < 0.7:
            salida.append(tuple(v + rng.uniform(-eps, eps) * 0.6 for v in rng.choice(base)))
        else:
            salida.append(tuple(rng.uniform(0, 10) for _ in range(k)))
    return salida


@pytest.mark.parametrize("k", [1, 2, 3])
def test_los_algoritmos_correctos_cumplen_la_especificacion(k):
    rng = random.Random(k)
    for _ in range(40):
        eps = rng.choice([0.2, 0.7, 1.5])
        f = firmas_al_azar(rng, rng.randint(0, 40), k, eps)
        for algoritmo in (deduplicar_cuadratico, deduplicar_rejilla):
            assert violaciones_dedup(f, eps, algoritmo(f, eps)) == {}, algoritmo.__name__
    f = firmas_al_azar(rng, 40, k, 0.0)
    assert violaciones_dedup(f, 0.0, deduplicar_exacta(f)) == {}


def test_la_especificacion_determina_el_resultado_exhaustivo():
    rng = random.Random(11)
    for _ in range(60):
        n = rng.randint(1, 9)
        eps = rng.choice([0.3, 1.0, 2.5])
        f = [None if rng.random() < 0.1 else (rng.uniform(0, 6),) for _ in range(n)]
        validos = [
            list(K)
            for r in range(n + 1) for K in itertools.combinations(range(n), r)
            if violaciones_dedup(f, eps, list(K)) == {}
        ]
        assert validos == [deduplicar_cuadratico(f, eps)]


def test_cada_clausula_atrapa_un_error_distinto():
    cadena = [(0.0,), (0.9,), (1.8,)]
    malo = deduplicar_contra_todas(cadena, 1.0)
    assert set(violaciones_dedup(cadena, 1.0, malo)) == {"cobertura"}
    intercaladas = [(0.0,), (5.0,), (0.0,)]
    malo = deduplicar_solo_ultimo(intercaladas, 1.0)
    assert set(violaciones_dedup(intercaladas, 1.0, malo)) == {"separacion"}
    assert set(violaciones_dedup(intercaladas, 1.0, [1, 0])) == {"orden"}


def test_dos_representantes_a_distancia_exactamente_eps_violan_la_separacion():
    assert "separacion" in violaciones_dedup([(0.0,), (1.0,)], 1.0, [0, 1])


def test_el_verificador_detecta_un_k_incompleto_y_uno_demasiado_grande():
    f = [(0.0,), (5.0,), (9.0,)]
    assert "cobertura" in violaciones_dedup(f, 1.0, [0, 1])           
    assert "separacion" in violaciones_dedup([(0.0,), (0.5,)], 1.0, [0, 1])   


@pytest.fixture(scope="module")
def firmas_de_formulas():
    g, d = Gramatica(variables=("a",)), kepler_real()
    return [firma(e, "a", d.xs) for e in enumerar(g, 5)]


def test_solo_ultimo_es_ciego_con_firmas_ordenadas_y_se_ve_con_el_orden_real(firmas_de_formulas):
    definidas = [s for s in firmas_de_formulas if s is not None]
    ordenadas = sorted(definidas)
    ventana = lambda lista: (lambda rng: lista[(i := rng.randrange(0, len(lista) - 60)): i + 60])
    correcto = lambda f: deduplicar_cuadratico(f, 1e-9)
    variante = lambda f: deduplicar_solo_ultimo(f, 1e-9)
    assert tasa_de_deteccion(ventana(ordenadas), correcto, variante, 60).detectadas == 0
    assert tasa_de_deteccion(ventana(firmas_de_formulas), correcto, variante, 60).tasa == 1.0


def test_contra_todas_es_ciego_con_formulas_reales_y_solo_lo_atrapa_una_cadena(firmas_de_formulas):
    correcto = lambda f: deduplicar_cuadratico(f, 1e-9)
    variante = lambda f: deduplicar_contra_todas(f, 1e-9)
    reales = lambda rng: rng.sample([s for s in firmas_de_formulas if s is not None], 60)
    cadenas = lambda rng: [(0.9 * j,) for j in range(rng.randint(3, 8))]
    assert tasa_de_deteccion(reales, correcto, variante, 60).detectadas == 0
    assert tasa_de_deteccion(
        cadenas, lambda f: deduplicar_cuadratico(f, 1.0), lambda f: deduplicar_contra_todas(f, 1.0), 60
    ).tasa == 1.0


def test_corolario_el_representante_nunca_es_mayor_que_la_formula_descartada():
    g, d = Gramatica(variables=("a",)), kepler_real()
    formulas = list(enumerar(g, 5))
    f = [firma(e, "a", d.xs) for e in formulas]
    K = deduplicar_cuadratico(f, 1e-9)
    descartadas = [t for t, s in enumerate(f) if s is not None and t not in set(K)]
    assert descartadas                                                  
    for t in descartadas:
        i = representante_de(t, f, K, 1e-9)
        assert i is not None and i < t and tamano(formulas[i]) <= tamano(formulas[t])


@pytest.mark.parametrize("datos", [kepler_real(), kepler_sintetico(25, 0.05, 2)], ids=["real", "sintetico"])
@pytest.mark.parametrize("eps", [1e-9, 1e-3, 0.05, 0.3, 1.0])
def test_teorema_de_la_perdida_del_mejor_error(datos, eps):
    g = Gramatica(variables=("a",))
    formulas = list(enumerar(g, 5))
    f = [firma(e, "a", datos.xs) for e in formulas]
    K = deduplicar_cuadratico(f, eps)
    mejor_todas = min(error_relativo_medio(formulas[i], datos) for i, s in enumerate(f) if s is not None)
    mejor_reps = min(error_relativo_medio(formulas[i], datos) for i in K)
    assert mejor_reps <= mejor_todas + cota_de_perdida(datos, eps) + 1e-12
    assert mejor_reps >= mejor_todas - 1e-12                              


def test_la_cota_de_perdida_es_ajustada():
    from simbolicalab.rs import Datos
    datos = Datos(xs=(2.0,), ys=(1.0,), nombre_x="x")
    formulas = [Const(1.04), Const(1.0)]
    f = [firma(e, "x", datos.xs) for e in formulas]
    eps = 0.04 + 1e-9          
    K = deduplicar_cuadratico(f, eps)
    assert K == [0]                                                   
    perdida = error_relativo_medio(formulas[0], datos) - error_relativo_medio(formulas[1], datos)
    assert perdida == pytest.approx(cota_de_perdida(datos, eps), rel=1e-6)


def test_valor_de_la_cota_de_perdida():
    from simbolicalab.rs import Datos
    datos = Datos(xs=(1.0, 2.0, 3.0), ys=(2.0, 4.0, 5.0))
    assert cota_de_perdida(datos, 0.1) == pytest.approx(0.1 * (1 / 2 + 1 / 4 + 1 / 5) / 3)


def test_la_cota_de_perdida_exige_y_distinto_de_cero():
    from simbolicalab.rs import Datos
    with pytest.raises(ValueError):
        cota_de_perdida(Datos(xs=(1.0,), ys=(0.0,)), 0.1)
