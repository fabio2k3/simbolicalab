"""Funciones de la API: cada una recibe un dict de parámetros y llama a TU código real."""
from __future__ import annotations

import random
from dataclasses import replace

from ..conjuntos import kepler_real, kepler_sintetico
from ..cotas.adversario import (evaluar_todas, jugar_contra_el_adversario, mirar_solo_la_mitad,
                                saltar_la_primera, saltar_la_ultima, verificar_instancia)
from ..cotas.informacion import cota_de_ordenar
from ..cotas.ordenamiento import insercion, mergesort, peor_caso_exacto
from ..costo.bits import es_primo_contado, mochila_contada, tamaño_en_bits
from ..costo.crecimiento import tabla_hardware
from ..estructuras.arreglo_dinamico import ArregloDinamico
from ..estructuras.contador_binario import analizar_incrementos
from ..estructuras.splay import ArbolSplay, verificar_lema_de_acceso
from ..nucleo import Contador, LibroAmortizado, Presupuesto, Traza
from ..rs import (Gramatica, InvarianteViolado, a_cadena, contar_por_size, costo_fuerza_bruta, deduplicar_cuadratico,
                  deduplicar_exacta, deduplicar_rejilla, enumerar, firma, mayor_size_alcanzable,
                  verificar_enumeracion, violaciones_dedup)
from ..rs.variantes_defectuosas import deduplicar_contra_todas, deduplicar_solo_ultimo
from ..solvers import SolverFuerzaBruta


def _lista(t, conv=str):
    return tuple(conv(x.strip()) for x in str(t).split(",") if x.strip())


def _entorno(p):
    datos = kepler_real() if p.get("conjunto", "real") == "real" else kepler_sintetico(
        max(1, min(int(p.get("n", 30)), 500)), float(p.get("ruido", 0.02)), int(p.get("semilla", 0)))
    kw = {}
    if p.get("constantes") is not None: kw["constants"] = _lista(p["constantes"], float)
    if p.get("unarios") is not None: kw["unarios"] = _lista(p["unarios"])
    if p.get("binarios") is not None: kw["binarios"] = _lista(p["binarios"])
    return datos, Gramatica(variables=(datos.nombre_x,), **kw)


def _oraculo0(p):
    datos, g = _entorno(p)
    m = min(int(p.get("max_tam", 5)), 8)
    traza = Traza()
    r = SolverFuerzaBruta(m, p.get("metrica", "ecm"), vigilar=True).resolver(
        datos, g, Presupuesto(min(int(p.get("presupuesto", 3_000_000)), 20_000_000)), traza)
    n = contar_por_size(g, 21)
    return {
        "resumen": {"datos": datos.nombre, "ley_oculta": datos.ley_oculta,
                    "formula_encontrada": a_cadena(r.expresion) if r.expresion else None,
                    "error": r.error, "operaciones": r.operaciones,
                    "presupuesto_agotado": r.agotado, "formulas_evaluadas": r.detalle["evaluadas"],
                    "mayor_tamano_en_1_hora_a_1e9_ops": mayor_size_alcanzable(g, 3.6e12, len(datos))},
        "mejoras": [e.a_dict() for e in traza.eventos],
        "espacio": [{"tamano": s, "formulas": str(n[s]),
                     "costo_fuerza_bruta": str(costo_fuerza_bruta(g, s, len(datos)))} for s in range(1, 22)],
    }


def _bits0(p):
    filas, prev = [], None
    for b in range(12, min(int(p.get("max_bits", 32)), 36) + 1, 4):
        n = 2 ** b + 1
        while not es_primo_contado(n, Contador()):
            n += 1
        c = Contador()
        es_primo_contado(n, c)
        filas.append({"bits": tamaño_en_bits(n), "n": n, "divisiones": c.total,
                      "factor_vs_anterior": round(c.total / prev, 2) if prev else None})
        prev = c.total
    pesos = [3 + i for i in range(20)]
    moch = []
    for b in range(8, 17, 2):
        c = Contador()
        mochila_contada(pesos, pesos, 2 ** b, c)
        moch.append({"bits_de_W": b, "W": 2 ** b, "celdas": c.total})
    hw = [{"costo": k, "n_base": v[0], "10x_mas_rapida": v[1], "1000x_mas_rapida": v[2]}
          for k, v in tabla_hardware().items()]
    return {"primalidad_por_division": filas, "mochila_pseudopolinomial": moch, "mayor_n_en_una_hora": hw}


def _dedup0(p):
    datos, g = _entorno(p)
    m, eps = min(int(p.get("max_tam", 4)), 5), float(p.get("eps", 1e-6))
    firmas = [firma(e, datos.nombre_x, datos.xs) for e in enumerar(g, m)]
    algos = {"cuadratica (correcta)": lambda f, c: deduplicar_cuadratico(f, eps, c),
             "rejilla (correcta)": lambda f, c: deduplicar_rejilla(f, eps, c),
             "exacta (eps = 0)": lambda f, c: deduplicar_exacta(f, c),
             "solo contra la ultima (defectuosa)": lambda f, c: deduplicar_solo_ultimo(f, eps, c),
             "contra todas, incluso descartadas (defectuosa)": lambda f, c: deduplicar_contra_todas(f, eps, c)}
    filas = []
    for nombre, fn in algos.items():
        if "rejilla" in nombre and len(datos) > 8:
            filas.append({"algoritmo": nombre, "representantes": None, "comparaciones": None,
                          "violaciones": f"omitida: cada firma visitaría 3^{len(datos)} celdas"})
            continue
        c = Contador()
        K = fn(firmas, c)
        mal = violaciones_dedup(firmas, eps, K)
        filas.append({"algoritmo": nombre, "representantes": len(K), "comparaciones": c.total,
                      "violaciones": ", ".join(mal) or "ninguna"})
    sin_div = lambda gr, mt, c=None: enumerar(replace(g, binarios=g.binarios[:-1]), mt, c)
    try:
        defectuosa = "no detectado"; verificar_enumeracion(g, m, sin_div)
    except InvarianteViolado as e:
        defectuosa = f"InvarianteViolado: {e}"
    return {"resumen": {"formulas": len(firmas), "firmas_definidas": sum(f is not None for f in firmas),
                        "enumerador_correcto": "niveles " + str(verificar_enumeracion(g, m)),
                        "enumerador_sin_division": defectuosa},
            "deduplicacion": filas}


def amortizado(p):
    k = min(int(p.get("k", 500)), 5000)
    lb = analizar_incrementos(k)
    res = lambda l: {"operaciones": l.operaciones, "costo_real_total": l.total_real,
                     "costo_amortizado_total": l.total_amortizado, "max_real": l.max_real,
                     "max_amortizado": l.max_amortizado, "suma_valida": l.suma_valida(),
                     "residuo_telescopio": l.residuo_del_telescopio()}
    arr = ArregloDinamico(float(p.get("factor", 2)), p.get("reduccion", "mitad"), libro=LibroAmortizado())
    for i in range(64):
        arr.append(i)
    for i in range(40):
        arr.append(i) if i % 2 == 0 else arr.pop()
    n = min(int(p.get("n_splay", 100)), 200)
    splay = []
    for h in ("splay", "raiz"):
        t, t2 = ArbolSplay(h), ArbolSplay(h)
        for i in range(n):
            t.insertar(i); t2.insertar(i)
        costos = [t.acceso_instrumentado(i)["costo"] for i in range(n)]
        splay.append({"heuristica": h, "costo_total_accesos_en_orden": sum(costos), "max_un_acceso": max(costos),
                      "violaciones_del_lema": len(verificar_lema_de_acceso(t2, list(range(n))))})
    return {"contador_binario_en_maquina_de_turing": res(lb), "primeros_costos_reales": lb.costos_reales[:48],
            "arreglo_dinamico (llena 64, luego alterna append/pop)": res(arr.libro), "splay_vs_subir_a_la_raiz": splay}


def _cotas0(p):
    filas = [{"n": n, "cota_informacion": cota_de_ordenar(n), "mergesort_peor_caso": peor_caso_exacto(mergesort, n),
              "insercion_peor_caso": peor_caso_exacto(insercion, n)} for n in range(2, 8)]
    n = max(2, min(int(p.get("n", 8)), 64))
    adv = []
    for nombre, fn in {"evaluar_todas": evaluar_todas, "saltar_la_ultima": saltar_la_ultima,
                       "saltar_la_primera": saltar_la_primera, "mirar_solo_la_mitad": mirar_solo_la_mitad}.items():
        r = jugar_contra_el_adversario(fn, n)
        veredicto = "correcto" if r.correcta else ("falla en la instancia del adversario"
                                                   if not verificar_instancia(fn, r.instancia)[0] else "sin fallo")
        adv.append({"algoritmo": nombre, "consultas": r.consultas, "de": n, "veredicto": veredicto})
    return {"ordenar": filas, "minimo_de_n_candidatas": adv}




# ---------------------------------------------------------------- extensiones: todo lo demás de src
import json, math
from ..costo.aritmetica import cuadrados_repetidos, fibonacci_contado
from ..costo.asintotica import primer_contraejemplo_cota_inferior, primer_contraejemplo_cota_superior, razones_en_potencias_de_2
from ..costo.bits import SEGUNDOS_POR_ANIO, tiempo_division_de_prueba
from ..costo.crecimiento import COSTOS_CLASICOS, pendientes, razon_media, razones
from ..costo.suma import suma_contada
from ..costo.turing import incrementar_k_veces, maquina_incremento, maquina_palindromo, palindromo_ram
from ..cotas.adversario import mejor_formula
from ..cotas.identificacion import (DisenoDeExperimento, cota_de_identificacion, candidatas_en_el_dominio,
                                    clases_distinguibles, profundidad_del_diseno, x_separadores)
from ..cotas.informacion import arbol_de_decision, cota_de_informacion
from ..cotas.ordenamiento import frente_de_pareto, frente_de_pareto_cuadratico, ordenar_por_conteo, ordenar_por_error
from ..estructuras.clases_formulas import clases_por_conmutatividad, reduccion_por_simetria
from ..estructuras.union_find import UnionFind
from ..nucleo import tasa_de_deteccion
from ..rs import METRICAS, Const, Op, Var, bien_formada, cota_de_perdida, representante_de, tamano
from ..solvers import SolverMedia


def oraculo(p):
    r = _oraculo0(p)
    datos, g = _entorno(p)
    m, met = min(int(p.get("max_tam", 5)), 8), p.get("metrica", "ecm")
    med = SolverMedia().resolver(datos, g, Presupuesto())
    r["solver_media_de_referencia"] = {"valor_constante": med.expresion, "error": med.error, "operaciones": med.operaciones}
    if m <= 6:
        fs = [e for e in enumerar(g, m)]
        errs = [METRICAS[met](e, datos) for e in fs]
        ok = [i for i, x in enumerate(errs) if math.isfinite(x)]
        T, E = [tamano(fs[i]) for i in ok], [errs[i] for i in ok]
        c1, c2 = Contador(), Contador()
        a, b = frente_de_pareto(T, E, c1), frente_de_pareto_cuadratico(T, E)
        r["frente_de_pareto"] = [{"tamano": T[i], "formula": a_cadena(fs[ok[i]]), "error": E[i]} for i in a]
        r["pareto_lineal_vs_cuadratico"] = {"iguales": a == b, "accesos_lineal": c1.total, "pares_cuadratico": len(T) ** 2}
        r["mejor_formula"] = [{"omitir_ultimas": k, "indice": (q := mejor_formula(fs[:3000], datos, met, None, k))[0],
                               "formula": a_cadena(fs[q[0]]), "error": q[1]} for k in (0, 1)]
    return r


def bits(p):
    r = _bits0(p)
    cu, fi = [], []
    for k in (2, 4, 6, 8, 10, 12):
        c = Contador(); cuadrados_repetidos(k, c); cu.append({"k": k, "multiplicaciones": c.por_categoria["mult_unitaria"], "costo_en_bits": c.por_categoria["bits"]})
    for n in (10, 50, 100, 200, 400):
        c = Contador(); fibonacci_contado(n, c); fi.append({"n": n, "sumas": c.por_categoria["suma"], "costo_en_bits": c.por_categoria["bits"]})
    r["cuadrados_repetidos"], r["fibonacci"] = cu, fi
    A = list(range(int(p.get("n_suma", 100))))
    sm = []
    for fus in (False, True):
        c = Contador(); suma_contada(A, c, fus); sm.append({"fusionar_acceso_y_suma": fus, "total": c.total, **c.por_categoria})
    r["suma_contada"] = sm
    r["division_de_prueba_a_1e9_ops_s"] = [{"bits": b, "divisiones": 2 ** (b // 2), "segundos": (s := tiempo_division_de_prueba(b)),
                                           "anios": s / SEGUNDOS_POR_ANIO} for b in (32, 64, 96, 128)]
    return r


def modelos(p):
    out = {}
    nombre = p.get("maquina", "palindromo")
    entrada = str(p.get("entrada", "0110"))
    if not entrada or set(entrada) - {"0", "1"}:
        raise ValueError("la entrada debe ser una cadena no vacía de ceros y unos")
    mt = maquina_palindromo() if nombre == "palindromo" else maquina_incremento()
    tz = Traza()
    r = mt.ejecutar(entrada, 0 if nombre == "palindromo" else len(entrada) - 1, traza=tz)
    out["maquina_de_turing"] = {"maquina": nombre, "entrada": entrada, "aceptada": r.aceptada, "pasos": r.pasos, "cinta_final": r.cinta}
    out["primeros_pasos"] = [e.a_dict() for e in tz.eventos[:30]]
    filas = []
    for n in (4, 8, 16, 32, 64):
        s = "0" * n
        c = Contador(); palindromo_ram(s, c)
        filas.append({"largo": n, "pasos_maquina_de_turing": maquina_palindromo().ejecutar(s).pasos, "comparaciones_ram": c.total})
    out["palindromo_turing_vs_ram"] = filas
    out["incrementos_en_turing"] = [{"k": k, "pasos_totales": incrementar_k_veces(k)} for k in (8, 64, 512)]
    f, g = COSTOS_CLASICOS[p.get("f", "n^2")], COSTOS_CLASICOS[p.get("g", "n log n")]
    c, n0, hasta = float(p.get("c", 1)), int(p.get("n0", 2)), min(int(p.get("hasta", 500)), 1000)
    try:
        out["f_es_O_de_g"] = {"primer_contraejemplo": primer_contraejemplo_cota_superior(f, g, c, n0, hasta)}
        out["f_es_Omega_de_g"] = {"primer_contraejemplo": primer_contraejemplo_cota_inferior(f, g, c, n0, hasta)}
        try:
            out["razon_f_sobre_g"] = [{"n": n, "f/g": q} for n, q in razones_en_potencias_de_2(f, g, 12)]
        except OverflowError:
            out["razon_f_sobre_g"] = [{"n": n, "f/g": q} for n, q in razones_en_potencias_de_2(f, g, 9)]
    except OverflowError:
        out["f_es_O_de_g"] = {"error": "desbordamiento: baja 'hasta'"}
    ns = [2 ** k for k in range(2, 10)]
    costos = [COSTOS_CLASICOS[p.get("f", "n^2")](n) for n in ns]
    out["crecimiento_de_f"] = {"razon_media_al_duplicar_n": razon_media(costos), "pendiente_media_log_log": sum(pendientes(list(zip(ns, costos)))) / (len(ns) - 1)}
    out["razones_al_duplicar"] = razones(costos)
    return out


def dedup(p):
    r = _dedup0(p)
    datos, g = _entorno(p)
    m, eps = min(int(p.get("max_tam", 4)), 5), float(p.get("eps", 1e-6))
    fs = list(enumerar(g, m))
    firmas = [firma(e, datos.nombre_x, datos.xs) for e in fs]
    K = deduplicar_cuadratico(firmas, eps)
    desc = [t for t, f in enumerate(firmas) if f is not None and t not in K][:8]
    r["quien_cubre_a_cada_descartada"] = [{"descartada": a_cadena(fs[t]), "representante": (a_cadena(fs[i]) if (i := representante_de(t, firmas, K, eps)) is not None else None)} for t in desc]
    r["cota_de_perdida_de_error_relativo"] = {"eps": eps, "cota": cota_de_perdida(datos, eps)}
    malas = {"sqrt con dos hijos": Op("sqrt", (Var("a"), Var("a"))), "constante fuera de la gramatica": Const(7.0), "suma con un hijo": Op("+", (Var("a"),))}
    r["bien_formada"] = [{"formula": "todas las enumeradas", "bien_formada": all(bien_formada(e, g) for e in fs)}] + [{"formula": k, "bien_formada": bien_formada(v, g)} for k, v in malas.items()]
    n, dim, span, pr = int(p.get("n_firmas", 6)), 1, float(p.get("span", 4)), int(p.get("pruebas", 500))
    gen = lambda rng: [(rng.uniform(0, span * eps),) for _ in range(n)]
    base = lambda f: deduplicar_cuadratico(f, eps)
    filas = []
    for nombre, fn in {"rejilla (control)": lambda f: deduplicar_rejilla(f, eps), "solo contra la ultima": lambda f: deduplicar_solo_ultimo(f, eps),
                       "contra todas": lambda f: deduplicar_contra_todas(f, eps)}.items():
        d = tasa_de_deteccion(gen, base, fn, pr, int(p.get("semilla_pruebas", 0)))
        filas.append({"variante": nombre, "pruebas": d.pruebas, "detectadas": d.detectadas, "tasa": d.tasa,
                      "primer_contraejemplo": str([round(x[0] / eps, 2) for x in d.primer_contraejemplo]) if d.primer_contraejemplo else None})
    r["tasa_de_deteccion (firmas en unidades de eps)"] = filas
    return r


def estructuras(p):
    n, ops, pat, sem = max(2, min(int(p.get("n", 512)), 5000)), max(1, min(int(p.get("ops", 512)), 5000)), p.get("patron", "cadena"), int(p.get("semilla", 0))
    cfgs = {"rango + compresion": {}, "solo rango": {"compresion": False}, "solo compresion": {"por_rango": False},
            "ninguna": {"por_rango": False, "compresion": False}, "rango sin actualizar en empate": {"rango_en_empate": False}}
    filas = []
    for nombre, kw in cfgs.items():
        uf, rng = UnionFind(n, **kw), random.Random(sem)
        for i in range(min(ops, n - 1)):
            uf.union(i + 1, i) if pat == "cadena" else uf.union(rng.randrange(n), rng.randrange(n))
        for x in range(n):
            uf.find(x)
        try:
            uf.verificar_propiedades(); ver = "se cumplen P1-P3"
        except AssertionError as e:
            ver = str(e)
        filas.append({"configuracion": nombre, "conjuntos": uf.conjuntos, "altura_maxima": uf.altura_maxima(), "pasos_de_find": uf.contador.total, "propiedades": ver})
    datos, g = _entorno(p)
    fs = list(enumerar(g, min(int(p.get("max_tam", 4)), 5)))
    tot, cl = reduccion_por_simetria(fs)
    grupos = [v for v in clases_por_conmutatividad(fs).clases().values() if len(v) > 1][:6]
    return {"union_find": filas, "simetria_por_conmutatividad": {"formulas": tot, "clases": cl, "ahorro": 1 - cl / tot},
            "ejemplos_de_clases": [{"tamano_de_la_clase": len(v), "formulas": " | ".join(a_cadena(fs[i]) for i in v[:4])} for v in grupos]}


def cotas(p):
    r = _cotas0({**p, "n": p.get("n_cand", 8)})
    arb = []
    for n in (2, 3, 4):
        for nom, fn in (("insercion", insercion), ("mergesort", mergesort)):
            a = arbol_de_decision(fn, n)
            arb.append({"n": n, "algoritmo": nom, "altura": a.altura, "hojas": a.hojas, "n!": math.factorial(n), "cota_informacion": cota_de_informacion(math.factorial(n))})
    r["arboles_de_decision"] = arb
    r["arbol_mergesort_n3"] = {"json": json.dumps(arbol_de_decision(mergesort, 3).como_dict())}
    rng, n, mx = random.Random(1), 256, int(p.get("maximo", 64))
    claves = [rng.randint(0, mx) for _ in range(n)]
    c1, c2 = Contador(), Contador()
    ordenar_por_conteo(claves, mx, c1); ordenar_por_error([float(k) for k in claves], c2)
    r["ordenar_sin_comparar (n=256)"] = [{"algoritmo": "por conteo", "operaciones": c1.total}, {"algoritmo": "mergesort por comparaciones", "operaciones": c2.total}]
    datos, g = _entorno(p)
    fs = list(enumerar(g, min(int(p.get("max_tam", 4)), 4)))
    reps, firmas = candidatas_en_el_dominio(fs, datos.nombre_x, datos.xs)
    r["identificacion"] = {"formulas": len(fs), "candidatas_distintas": len(reps), "cota_de_identificacion": cota_de_identificacion(len(reps)),
                           "x_que_separan_todas": len(x_separadores(firmas)), **profundidad_del_diseno(firmas)}
    r["clases_distinguibles_segun_puntos"] = [{"puntos_de_consulta": k, "clases": clases_distinguibles(fs, datos.nombre_x, datos.xs[:k])} for k in range(1, len(datos.xs) + 1)]
    q = DisenoDeExperimento(firmas).consultas_para(len(reps) - 1)
    r["consultas_para_la_ultima_candidata"] = [{"x": datos.xs[c.x_indice], "umbral": c.umbral, "respuesta": ans} for c, ans in q]
    return r


API = {"oraculo": oraculo, "bits": bits, "modelos": modelos, "dedup": dedup, "amortizado": amortizado, "estructuras": estructuras, "cotas": cotas}
