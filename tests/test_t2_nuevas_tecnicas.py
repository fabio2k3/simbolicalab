"""Fase 3: recurrencias, FFT, multiplicación de polinomios y detector espectral."""
import cmath
import math
import random

import pytest

from simbolicalab.conjuntos import kepler_real, oscilador_sintetico
from simbolicalab.nucleo import Contador, Presupuesto, Solver
from simbolicalab.rs import Datos, Gramatica, a_cadena
from simbolicalab.rs.error import METRICAS
from simbolicalab.solvers import SolverEspectral
from simbolicalab.tecnicas import (alias, dft, error_de_redondeo, es_potencia_de_dos, espectro, fft, fft_iterativa,
                                   ifft, maestro, multiplicar_escolar, multiplicar_exacta, multiplicar_fft,
                                   multiplicar_karatsuba, picos, refinar_jacobsen, refinar_por_ajuste, resolver,
                                   siguiente_potencia_de_dos, submuestrear, trabajo_por_nivel, verificar_maestro)
from simbolicalab.tecnicas.vairantes_fft import (frecuencia_dominante_con_media, frecuencia_dominante_n_menos_1,
                                                 frecuencia_dominante_sin_dt, ifft_sin_dividir, multiplicar_fft_mal)

G = Gramatica(variables=("t",))


def cercanos(a, b, tol=1e-9):
    return max(abs(x - y) for x, y in zip(a, b)) < tol



@pytest.mark.parametrize("a,b,d,caso,notacion", [
    (1, 2, 0, "empate", "Θ(log n)"),
    (2, 2, 1, "empate", "Θ(n^1 log n)"),
    (3, 2, 1, "hojas", "Θ(n^1.585)"),
    (1, 2, 1, "raiz", "Θ(n^1)"),
    (4, 2, 1, "hojas", "Θ(n^2)"),
    (2, 4, 0.5, "empate", "Θ(n^0.5 log n)"),
])
def test_teorema_maestro_casos(a, b, d, caso, notacion):
    c = maestro(a, b, d)
    assert c.caso == caso and c.notacion == notacion
    assert c.razon == pytest.approx(a / b ** d)


@pytest.mark.parametrize("a,b,d", [(1, 2, 0), (2, 2, 1), (3, 2, 1), (1, 2, 1), (4, 2, 1), (2, 4, 0.5), (5, 3, 1)])
def test_la_cota_del_maestro_se_cumple_en_la_evaluacion_numerica(a, b, d):
    v = verificar_maestro(a, b, d, exponente_max=10 if b == 3 else 12)
    assert v["acotado"]


def test_adivinar_mal_la_cota_se_nota():
    razones = [resolver(3, 2, lambda m: m, 2 ** L) / (2 ** L * L) for L in range(4, 17)]
    assert all(b > a for a, b in zip(razones, razones[1:])) and razones[-1] > 3 * razones[0]


def test_trabajo_por_nivel_suma_lo_que_resuelve_la_recurrencia():
    for a, b, d in [(1, 2, 0), (2, 2, 1), (3, 2, 1), (4, 2, 2)]:
        n = 2 ** 8
        niveles = trabajo_por_nivel(a, b, d, n)
        assert len(niveles) == 9
        assert sum(niveles) == pytest.approx(resolver(a, b, lambda m: m ** d, n, base=1.0))
        if a / b ** d != 1:
            assert niveles[1] / niveles[0] == pytest.approx(a / b ** d)


def test_recurrencias_parametros_invalidos():
    for args in [(0.5, 2, 1), (2, 1, 1), (2, 2, -1)]:
        with pytest.raises(ValueError):
            maestro(*args)
    with pytest.raises(ValueError):
        resolver(2, 2, lambda m: m, 12)
    with pytest.raises(ValueError):
        resolver(2, 1, lambda m: m, 8)



@pytest.mark.parametrize("n", [1, 2, 4, 8, 16, 64, 256])
def test_fft_igual_a_la_dft(n):
    rng = random.Random(n)
    a = [complex(rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(n)]
    ref = dft(a)
    assert cercanos(fft(a), ref) and cercanos(fft_iterativa(a), ref)
    assert cercanos(dft(a, -1), fft(a, -1)) and cercanos(fft_iterativa(a, -1), fft(a, -1))


def test_dft_de_1_mas_x_a_mano():
    y = fft([1, 1, 0, 0])
    esperado = [2, 1 + 1j, 0, 1 - 1j]
    assert cercanos(y, esperado) and cercanos(fft_iterativa([1, 1, 0, 0]), esperado)


@pytest.mark.parametrize("n", [1, 2, 8, 128])
def test_inversa_recupera_la_senal(n):
    rng = random.Random(7)
    a = [rng.uniform(-5, 5) for _ in range(n)]
    assert cercanos(ifft(fft_iterativa(a)), a)


def test_parseval():
    rng = random.Random(3)
    a = [rng.uniform(-1, 1) for _ in range(64)]
    y = fft_iterativa(a)
    assert sum(v * v for v in a) == pytest.approx(sum(abs(z) ** 2 for z in y) / 64)


def test_un_tono_en_una_casilla_da_n_medios():
    N, k0 = 64, 5
    y = fft_iterativa([math.sin(2 * math.pi * k0 * j / N) for j in range(N)])
    mag = [abs(z) for z in y]
    assert mag[k0] == pytest.approx(N / 2) and mag[N - k0] == pytest.approx(N / 2)
    assert sum(m for i, m in enumerate(mag) if i not in (k0, N - k0)) < 1e-9


@pytest.mark.parametrize("f", [fft, fft_iterativa])
def test_fft_exige_potencia_de_dos(f):
    for n in (0, 3, 6, 12):
        with pytest.raises(ValueError):
            f([0.0] * n)


def test_potencias_de_dos():
    assert [es_potencia_de_dos(n) for n in (0, 1, 2, 3, 4, 6, 8)] == [False, True, True, False, True, False, True]
    assert [siguiente_potencia_de_dos(m) for m in (1, 2, 3, 5, 8, 9)] == [1, 2, 4, 8, 8, 16]


@pytest.mark.parametrize("n", [2, 8, 64, 512])
def test_el_costo_de_la_fft_es_la_recurrencia_2T_n_2_mas_n(n):
    L = int(math.log2(n))
    for f in (fft, fft_iterativa):
        c = Contador()
        f([0.0] * n, 1, c)
        assert c.por_categoria["mult"] == resolver(2, 2, lambda m: m / 2, n, base=0) == n // 2 * L
        assert c.por_categoria["suma"] == resolver(2, 2, lambda m: m, n, base=0) == n * L


def test_la_dft_cuesta_n_cuadrado_y_la_fft_n_log_n():
    n = 256
    c1, c2 = Contador(), Contador()
    dft([0.0] * n, 1, c1)
    fft_iterativa([0.0] * n, 1, c2)
    assert c1.total > 40 * c2.total



def test_las_tres_multiplicaciones_coinciden():
    rng = random.Random(0)
    for na in (1, 2, 3, 7, 16, 30):
        for nb in (1, 2, 5, 16, 17):
            a = [rng.randint(-9, 9) for _ in range(na)]
            b = [rng.randint(-9, 9) for _ in range(nb)]
            ref = multiplicar_escolar(a, b)
            assert multiplicar_fft(a, b) == ref == multiplicar_karatsuba(a, b)
    assert multiplicar_fft([], [1]) == multiplicar_karatsuba([], [1]) == multiplicar_escolar([], [1]) == []


def test_producto_exacto_por_kronecker():
    rng = random.Random(1)
    a = [rng.randrange(1000) for _ in range(50)]
    b = [rng.randrange(1000) for _ in range(70)]
    assert multiplicar_exacta(a, b) == multiplicar_escolar(a, b)


@pytest.mark.parametrize("L", [1, 2, 3, 4, 5, 6, 7, 8])
def test_karatsuba_cuenta_tres_a_la_L_productos(L):
    n = 2 ** L
    c = Contador()
    multiplicar_karatsuba([1] * n, [1] * n, c)
    assert c.por_categoria["mult"] == 3 ** L
    assert c.por_categoria["suma"] == resolver(3, 2, lambda m: 6 * m - 5, n, base=0)


def _productos(n):
    k, f = Contador(), Contador()
    a = [1] * n
    multiplicar_karatsuba(a, a, k)
    multiplicar_fft(a, a, f)
    return k.por_categoria["mult"], f.por_categoria["mult"]


def test_cuando_gana_cada_multiplicacion_en_productos():
    e = Contador()
    multiplicar_escolar([1] * 64, [1] * 64, e)
    assert e.por_categoria["mult"] == 64 * 64
    k, f = _productos(64)
    assert k < f < 64 * 64                 
    k, f = _productos(1024)
    assert f < k < 1024 * 1024              


def _falla(a, b):
    try:
        return multiplicar_fft_mal(a, b) != multiplicar_escolar(a, b)
    except Exception:
        return True


def test_error_plantado_falla_si_y_solo_si_el_grado_es_potencia_de_dos():
    rng = random.Random(0)
    for na in range(1, 20):
        for nb in range(1, 20):
            a = [rng.randint(1, 9) for _ in range(na)]
            b = [rng.randint(1, 9) for _ in range(nb)]
            assert _falla(a, b) == es_potencia_de_dos(na + nb - 2)


def test_la_bateria_con_largos_iguales_en_potencias_de_dos_no_lo_ve():
    rng = random.Random(1)
    for L in (4, 8, 16, 64, 256):
        a = [rng.randint(-9, 9) for _ in range(L)]
        b = [rng.randint(-9, 9) for _ in range(L)]
        assert not _falla(a, b)
    assert multiplicar_fft_mal([1, 1], [1, 1]) != [1, 2, 1]


def test_la_inversa_sin_dividir_devuelve_n_veces():
    a = [1.0, 2.0, 3.0, 4.0]
    y = fft_iterativa(a)
    assert cercanos(ifft_sin_dividir(y), [4 * v for v in a])


def test_el_redondeo_de_la_fft_crece_con_la_base():
    chicos = error_de_redondeo(2 ** 12, 3, semilla=123)
    grandes = error_de_redondeo(2 ** 12, 6, semilla=126)
    assert chicos["coeficientes_equivocados"] == 0 and chicos["error_maximo"] < 1e-5
    assert grandes["error_maximo"] > 1000 * chicos["error_maximo"]


def test_redondeo_el_resultado_cabe_en_un_float_pero_los_intermedios_no():
    r = error_de_redondeo(2 ** 14, 6, semilla=10 * 14 + 6)
    assert r["coeficiente_maximo"] < 2 ** 53 < r["suma_de_coeficientes"]
    assert r["coeficientes_equivocados"] > 500
    assert error_de_redondeo(2 ** 14, 3, semilla=10 * 14 + 3)["coeficientes_equivocados"] == 0



def test_espectro_forma_y_ejes():
    ys = [math.sin(0.3 * k) for k in range(100)]
    e = espectro(ys, 0.1)
    assert e.N == 128 and len(e.frecuencias) == 65 and e.resolucion == pytest.approx(1 / 12.8)
    assert e.frecuencias[-1] == pytest.approx(5.0)                           
    assert espectro(ys, 0.1, relleno=4).N == 512


def test_espectro_parametros_invalidos():
    for kw in ({"ys": [1.0] * 3, "dt": 0.1}, {"ys": [1.0] * 8, "dt": 0.0}, {"ys": [1.0] * 8, "dt": 0.1, "relleno": 0}):
        with pytest.raises(ValueError):
            espectro(**kw)
    with pytest.raises(ValueError):
        picos(espectro([1.0, 2.0, 3.0, 5.0], 0.1), 0)


def test_un_tono_exacto_en_su_casilla_da_esa_frecuencia():
    N, k0, dt = 128, 10, 0.05
    e = espectro([math.sin(2 * math.pi * k0 * j / N) for j in range(N)], dt)
    p = picos(e, 1)[0]
    assert p.indice == k0 and p.frecuencia == pytest.approx(k0 / (N * dt))


def test_pico_y_refinados_en_el_oscilador():
    d = oscilador_sintetico()
    dt = d.xs[1] - d.xs[0]
    e = espectro(d.ys, dt)
    p = picos(e, 1)[0]
    assert p.indice == 6 and abs(p.frecuencia - 0.5) > 0.03                    
    assert abs(refinar_jacobsen(e, p) - 0.5) < 0.005
    assert abs(refinar_por_ajuste(d.xs, d.ys, p.frecuencia, e.resolucion) - 0.5) < 0.005


@pytest.mark.parametrize("f", [0.31, 0.5, 1.234, 3.0])
def test_los_refinados_sin_ruido_dan_la_frecuencia_con_3_decimales(f):
    d = oscilador_sintetico(frecuencia=f, ruido=0.0)
    e = espectro(d.ys, d.xs[1] - d.xs[0])
    p = picos(e, 1)[0]
    assert abs(refinar_jacobsen(e, p) - f) < 2e-3
    assert abs(refinar_por_ajuste(d.xs, d.ys, p.frecuencia, e.resolucion) - f) < 1e-3


def test_dos_tonos_con_ruido():
    rng = random.Random(0)
    ts = [0.1 * k for k in range(256)]
    ys = [math.sin(2 * math.pi * 0.7 * t) + 0.5 * math.sin(2 * math.pi * 2.3 * t) + rng.gauss(0, 0.05) for t in ts]
    e = espectro(ys, 0.1)
    fs = sorted(refinar_jacobsen(e, p) for p in picos(e, 2))
    assert fs == pytest.approx([0.7, 2.3], abs=0.01)
    assert len(picos(e, 2, umbral=0.9)) == 1                                    


def test_con_largo_que_no_es_potencia_de_dos_el_rellenado_sesga_a_jacobsen_pero_no_al_ajuste():
    d = oscilador_sintetico(n=100)
    e = espectro(d.ys, d.xs[1] - d.xs[0])
    assert e.N == 128
    p = picos(e, 1)[0]
    assert abs(refinar_jacobsen(e, p) - 0.5) > 0.005
    assert abs(refinar_por_ajuste(d.xs, d.ys, p.frecuencia, e.resolucion) - 0.5) < 0.005


def test_aliasing_el_submuestreo_disfraza_la_frecuencia():
    d = oscilador_sintetico(frecuencia=4.0, ruido=0.0)                           
    assert picos(espectro(d.ys, 0.1), 1)[0].frecuencia == pytest.approx(4.0, abs=0.08)
    ts, ys = submuestrear(d.xs, d.ys, 2)                                         
    e = espectro(ys, ts[1] - ts[0])
    assert alias(4.0, 0.2) == pytest.approx(1.0)
    assert picos(e, 1)[0].frecuencia == pytest.approx(1.0, abs=e.resolucion)
    assert alias(7.0, 0.1) == pytest.approx(3.0) and alias(0.5, 0.1) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        submuestrear(d.xs, d.ys, 0)


def test_variante_sin_dt_olvida_el_paso():
    d = oscilador_sintetico(ruido=0.0)
    dt = d.xs[1] - d.xs[0]
    bien = picos(espectro(d.ys, dt), 1)[0].frecuencia
    mal = frecuencia_dominante_sin_dt(d.ys, dt)
    assert mal == pytest.approx(bien * dt) and abs(mal - 0.5) > 0.4


def test_variante_con_media_ve_solo_el_desplazamiento():
    d = oscilador_sintetico(ruido=0.0)
    dt = d.xs[1] - d.xs[0]
    desplazada = [v + 5.0 for v in d.ys]
    assert frecuencia_dominante_con_media(d.ys, dt) == pytest.approx(0.46875)      
    assert frecuencia_dominante_con_media(desplazada, dt) == 0.0
    assert picos(espectro(desplazada, dt), 1)[0].frecuencia == pytest.approx(0.46875)


def test_variante_n_menos_1_cae_dentro_de_una_casilla_y_pasa_desapercibida():
    d = oscilador_sintetico(ruido=0.0)
    dt = d.xs[1] - d.xs[0]
    e = espectro(d.ys, dt)
    bien = picos(e, 1)[0].frecuencia
    mal = frecuencia_dominante_n_menos_1(d.ys, dt)
    assert mal == pytest.approx(bien * 128 / 127) and 0 < mal - bien < e.resolucion


def test_solver_espectral_cumple_el_contrato():
    assert isinstance(SolverEspectral(), Solver)


def test_solver_espectral_recupera_el_oscilador():
    d = oscilador_sintetico()
    r = SolverEspectral(1).resolver(d, G, Presupuesto(None))
    assert r.detalle["frecuencias"][0] == pytest.approx(0.5, abs=0.005)
    assert r.detalle["amplitudes"][0] == pytest.approx(2.0, abs=0.05)
    assert r.error < 0.02                                                         
    assert METRICAS["ecm"](r.expresion, d) == pytest.approx(r.error, rel=1e-9)
    assert "sin(" in a_cadena(r.expresion) and not r.agotado


def test_sin_refinar_el_ajuste_es_mucho_peor():
    d = oscilador_sintetico()
    crudo = SolverEspectral(1, "ninguno").resolver(d, G, Presupuesto(None))
    fino = SolverEspectral(1, "jacobsen").resolver(d, G, Presupuesto(None))
    assert crudo.error > 20 * fino.error


def test_jacobsen_es_igual_de_bueno_y_mucho_mas_barato_que_el_ajuste():
    d = oscilador_sintetico()
    a = SolverEspectral(1, "ajuste").resolver(d, G, Presupuesto(None))
    j = SolverEspectral(1, "jacobsen").resolver(d, G, Presupuesto(None))
    assert j.error == pytest.approx(a.error, rel=0.05) and j.operaciones * 10 < a.operaciones


def test_solver_espectral_dos_tonos_y_constante():
    rng = random.Random(0)
    ts = [0.1 * k for k in range(256)]
    ys = [1 + math.sin(2 * math.pi * 0.7 * t) + 0.5 * math.sin(2 * math.pi * 2.3 * t) + rng.gauss(0, 0.05) for t in ts]
    d = Datos(xs=tuple(ts), ys=tuple(ys), nombre_x="t")
    r = SolverEspectral(2).resolver(d, G, Presupuesto(None))
    assert sorted(r.detalle["frecuencias"]) == pytest.approx([0.7, 2.3], abs=0.01)
    assert r.detalle["constante"] == pytest.approx(1.0, abs=0.02) and r.error < 0.005


def test_la_senal_amortiguada_no_es_un_tono_y_mas_frecuencias_no_lo_arreglan():
    d = oscilador_sintetico(amortiguamiento=0.2, ruido=0.02)
    e1 = SolverEspectral(1).resolver(d, G, Presupuesto(None)).error
    e3 = SolverEspectral(3).resolver(d, G, Presupuesto(None)).error
    assert e1 > 0.05 and e3 > 0.9 * e1


def test_solver_espectral_no_aplica_a_datos_sin_rejilla_uniforme():
    d = kepler_real()
    r = SolverEspectral().resolver(d, Gramatica(variables=(d.nombre_x,)), Presupuesto(None))
    assert r.expresion is None and math.isinf(r.error) and "rejilla" in r.detalle["motivo"]


def test_solver_espectral_presupuesto_agotado():
    r = SolverEspectral().resolver(oscilador_sintetico(), G, Presupuesto(200))
    assert r.agotado and r.expresion is None


def test_solver_espectral_parametros_invalidos():
    for kw in ({"m": 0}, {"refinar": "nada"}, {"relleno": 0}):
        with pytest.raises(ValueError):
            SolverEspectral(**kw)