import itertools
import random

import pytest

from simbolicalab.conjuntos import kepler_real
from simbolicalab.cotas.identificacion import (
    Consulta, DisenoDeExperimento, candidatas_en_el_dominio, clases_distinguibles,
    cota_de_identificacion, profundidad_del_diseno, x_separadores,
)
from simbolicalab.rs import Gramatica, enumerar, firma

POOL = [0.3 * (40 / 0.3) ** (k / 39) for k in range(40)]       


def firmas_al_azar(rng, n, m):
    vistos, salida = set(), []
    while len(salida) < n:
        f = tuple(round(rng.uniform(0, 100), 3) for _ in range(m))
        if f not in vistos:
            vistos.add(f)
            salida.append(f)
    return salida



def test_la_cota_de_identificacion_es_el_techo_del_log2():
    assert [cota_de_identificacion(n) for n in (1, 2, 3, 4, 5, 59, 214, 220)] == [0, 1, 2, 2, 3, 6, 8, 8]


def test_el_diseno_siempre_respeta_la_cota_de_informacion_y_siempre_identifica():
    rng = random.Random(1)
    for _ in range(40):
        n, m = rng.randint(2, 60), rng.randint(1, 6)
        f = firmas_al_azar(rng, n, m)
        diseno = DisenoDeExperimento(f)
        profundidades = diseno.profundidades()                   
        assert max(profundidades) >= cota_de_identificacion(n)
        assert min(profundidades) >= 1


def test_con_valores_distintos_en_un_x_es_busqueda_binaria_y_alcanza_la_cota():
    for n in (2, 3, 7, 8, 16, 33, 100):
        f = [(float(i),) for i in range(n)]
        r = profundidad_del_diseno(f)
        assert r["peor_caso"] == r["cota"] == cota_de_identificacion(n)


def test_las_preguntas_identifican_de_forma_unica():
    rng = random.Random(2)
    f = firmas_al_azar(rng, 40, 4)
    diseno = DisenoDeExperimento(f)
    for verdadera in range(len(f)):
        camino = diseno.consultas_para(verdadera)
        consistentes = [
            i for i in range(len(f))
            if all((f[i][q.x_indice] <= q.umbral) == r for q, r in camino)
        ]
        assert consistentes == [verdadera]


def test_con_empates_en_un_x_hace_falta_cambiar_de_x():
    f = [(1.0, 5.0), (1.0, 6.0), (2.0, 7.0), (2.0, 8.0)]          
    diseno = DisenoDeExperimento(f)
    usados = {q.x_indice for i in range(4) for q, _ in diseno.consultas_para(i)}
    assert usados == {0, 1}
    assert profundidad_del_diseno(f)["peor_caso"] == 2 == cota_de_identificacion(4)


def test_candidatas_indistinguibles_son_un_error():
    with pytest.raises(ValueError, match="indistinguibles"):
        DisenoDeExperimento([(1.0, 2.0), (1.0, 2.0)])
    with pytest.raises(ValueError):
        DisenoDeExperimento([])


def test_la_resolucion_limita_lo_que_una_pregunta_distingue():
    f = [(1.0,), (1.0 + 1e-12,)]
    with pytest.raises(ValueError):
        DisenoDeExperimento(f, resolucion=1e-9)
    assert DisenoDeExperimento(f, resolucion=1e-15).profundidades() == [1, 1]


def test_x_separadores():
    f = [(1.0, 5.0, 9.0), (1.0, 6.0, 8.0), (2.0, 7.0, 9.0)]
    assert x_separadores(f) == [1]                                  
    assert x_separadores([]) == []


def test_un_modelo_exige_log2_n_preguntas_y_el_otro_una_sola_medido_con_formulas_reales():
    g = Gramatica(variables=("a",))
    formulas = list(enumerar(g, 4))
    _, firmas = candidatas_en_el_dominio(formulas, "a", POOL)
    r = profundidad_del_diseno(firmas)
    assert r["candidatas"] == 59
    assert r["peor_caso"] == r["cota"] == 6                          
    assert len(x_separadores(firmas)) == len(POOL)                   


def test_candidatas_en_el_dominio_filtra_indefinidas_y_equivalentes():
    g = Gramatica(variables=("a",))
    formulas = list(enumerar(g, 4))
    indices, firmas = candidatas_en_el_dominio(formulas, "a", POOL)
    assert len(indices) == len(firmas) < len(formulas)
    assert all(f is not None for f in firmas)
    assert len({tuple(round(v, 6) for v in f) for f in firmas}) == len(firmas)


def test_un_punto_generico_ya_separa_todas_pero_la_tierra_casi_no_informa():
    g, d = Gramatica(variables=("a",)), kepler_real()
    fijas = [e for e in enumerar(g, 5) if firma(e, "a", d.xs) is not None]
    assert len(fijas) == 1201
    assert clases_distinguibles(fijas, "a", d.xs) == 214
    assert clases_distinguibles(fijas, "a", [d.xs[0]]) == 214        
    assert clases_distinguibles(fijas, "a", [1.0]) == 47            
    assert clases_distinguibles(fijas, "a", [x for x in d.xs if x != 1.0]) == 214  


def test_clases_distinguibles_es_monotono_con_un_conjunto_fijo():
    g, d = Gramatica(variables=("a",)), kepler_real()
    fijas = [e for e in enumerar(g, 4) if firma(e, "a", d.xs) is not None]
    cuentas = [clases_distinguibles(fijas, "a", d.xs[:k]) for k in range(1, 9)]
    assert cuentas == sorted(cuentas)
