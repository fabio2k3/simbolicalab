"""Autoprueba de la API con los valores por defecto (Kepler real). Uso: python -m simbolicalab.web.autotest"""
from .api import API


def main():
    errores = []
    def ok(cond, msg):
        print(("OK    " if cond else "FALLA ") + msg)
        if not cond: errores.append(msg)

    r = API["oraculo"]({})
    ok(r["resumen"]["formula_encontrada"] == "a * sqrt(a)", "oráculo encuentra a * sqrt(a)")
    ok(r["resumen"]["error"] < 0.01 and not r["resumen"]["presupuesto_agotado"], "error < 0.01 y presupuesto sin agotar")
    ok(r["espacio"][0]["formulas"] == "3", "N(1) = 3 fórmulas")
    ok(r["pareto_lineal_vs_cuadratico"]["iguales"], "Pareto lineal = cuadrático")

    r = API["bits"]({})
    f = r["primalidad_por_division"]
    ok(all(3.9 < x["factor_vs_anterior"] < 4.1 for x in f[1:]), "primalidad: ×4 divisiones cada 4 bits")
    ok(r["suma_contada"][0]["total"] == 503 and r["suma_contada"][1]["total"] == 403, "suma_contada: 503 sin fusión, 403 con fusión")

    r = API["dedup"]({})
    d = {x["algoritmo"]: x for x in r["deduplicacion"]}
    ok(d["cuadratica (correcta)"]["violaciones"] == "ninguna" and d["rejilla (correcta)"]["violaciones"] == "ninguna", "dedup correctas sin violaciones")
    ok(d["solo contra la ultima (defectuosa)"]["violaciones"] != "ninguna", "dedup defectuosa viola una propiedad")
    ok("InvarianteViolado" in r["resumen"]["enumerador_sin_division"], "enumerador sin división: InvarianteViolado")
    t = {x["variante"]: x for x in r["tasa_de_deteccion (firmas en unidades de eps)"]}
    ok(t["rejilla (control)"]["detectadas"] == 0 and t["solo contra la ultima"]["tasa"] > 0.5, "tasa de detección: control 0, defectuosa > 50 %")

    r = API["amortizado"]({})
    c = r["contador_binario_en_maquina_de_turing"]
    ok(c["suma_valida"] and c["costo_real_total"] <= 2 * c["operaciones"] * 2, "contador binario: suma válida y costo acotado")
    s = {x["heuristica"]: x for x in r["splay_vs_subir_a_la_raiz"]}
    ok(s["splay"]["violaciones_del_lema"] == 0 and s["raiz"]["violaciones_del_lema"] > 0, "splay cumple el lema; subir a la raíz lo viola")

    r = API["cotas"]({})
    o = {x["n"]: x for x in r["ordenar"]}
    ok(all(x["mergesort_peor_caso"] >= x["cota_informacion"] for x in o.values()), "mergesort nunca baja de la cota de información")
    v = {x["algoritmo"]: x["veredicto"] for x in r["minimo_de_n_candidatas"]}
    ok(v["evaluar_todas"] == "correcto" and all("falla" in v[k] for k in v if k != "evaluar_todas"), "adversario: solo evaluar_todas es correcto")
    ok(r["identificacion"]["peor_caso"] == r["identificacion"]["cota_de_identificacion"], "diseño de experimento alcanza la cota")

    r = API["modelos"]({})
    ok(r["palindromo_turing_vs_ram"][-1]["pasos_maquina_de_turing"] > 20 * r["palindromo_turing_vs_ram"][-1]["comparaciones_ram"], "palíndromo: Turing ≫ RAM")
    ok(abs(r["crecimiento_de_f"]["pendiente_media_log_log"] - 2) < 0.01, "n^2: pendiente log-log = 2")

    r = API["estructuras"]({})
    u = {x["configuracion"]: x for x in r["union_find"]}
    ok(u["rango + compresion"]["propiedades"].startswith("se cumplen") and u["ninguna"]["altura_maxima"] > 100, "UnionFind: óptimo cumple P1-P3, sin nada la altura explota")
    print("\n" + ("TODO CORRECTO" if not errores else f"{len(errores)} FALLOS"))
    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
