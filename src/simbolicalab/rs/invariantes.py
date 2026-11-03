from __future__ import annotations

import math
from typing import Callable, Iterable, Sequence

from ..nucleo.contador import Contador
from .datos import Datos
from .deduplicacion import Firma , _distancia2
from .enumerador import enumerar
from .espacio import contar_por_size
from .expresion import Const, Expr, Op, Var, tamano
from .gramatica import Gramatica

class InvarianteViolado(AssertionError):
    """"""

def bien_formada(e: Expr, g: Gramatica) -> bool:
    match e:
        case Var(n):
            return n in g.variables
        case Const(v):
            return v in g.constants
        case Op(nombre, hijos):
            aridad_ok = (nombre in g.unarios and len(hijos) == 1) or (nombre in g.binarios and len(hijos) == 2)
            return aridad_ok and all(bien_formada(h, g) for h in hijos)

    return False

def verificar_enumeracion(g: Gramatica, max_tam: int, enumerador: Callable[..., Iterable[Expr]] = enumerar, contador: Contador | None = None, ) -> dict[int, int]:
    esperado = contar_por_size(g, max_tam)
    total = sum(esperado)
    nivel, en_nivel, niveles, generadas = 1, set(), {}, 0

    def cerrar(s: int) -> None:
        if len(en_nivel) != esperado[s]:
            raise InvarianteViolado(f"nivel {s}: hay {len(en_nivel)} fórmulas y debería haber {esperado[s]}")
        niveles[s] = len(en_nivel)

    for e in enumerador(g, max_tam, contador):
        s = tamano(e)
        if not 1 <= s <= max_tam:
            raise InvarianteViolado(f"fórmula de tamaño {s} fuera de [1, {max_tam}]")
        if s < nivel:
            raise InvarianteViolado(f"nivel {s} aparece después del {nivel}: los niveles deben ir en orden")
        while nivel < s:
            cerrar(nivel)
            nivel += 1
            en_nivel = set()
        if not bien_formada(e, g):
            raise InvarianteViolado(f"fórmula mal formada: {e!r}")
        if e in en_nivel:
            raise InvarianteViolado(f"fórmula repetida en el nivel {s}: {e!r}")
        en_nivel.add(e)
        generadas += 1
        restantes = total - generadas                      
        if restantes < 0:
            raise InvarianteViolado(f"se generaron más fórmulas ({generadas}) que las {total} posibles")

    while nivel <= max_tam:
        cerrar(nivel)
        nivel += 1
        en_nivel = set()
    if generadas != total:
        raise InvarianteViolado(f"potencial final {total - generadas} != 0")
    return niveles

def violaciones_dedup(firmas: Sequence[Firma | None], eps: float, K: Sequence[int]) -> dict[str, str]:
    malas: dict[str, str] = {}
    conjunto = set(K)

    if any(not (0 <= i < len(firmas)) or firmas[i] is None for i in K) or list(K) != sorted(set(K)):
        malas["orden"] = "K no es una lista creciente de índices de firmas definidas"
        return malas                                      

    for a in range(len(K)):
        for b in range(a + 1, len(K)):
            if _distancia2(firmas[K[a]], firmas[K[b]]) <= eps * eps:     
                malas["separacion"] = f"los representantes {K[a]} y {K[b]} están a distancia <= eps"
                break
        if "separacion" in malas:
            break

    for t, f in enumerate(firmas):
        if f is None or t in conjunto:
            continue
        if not any(i < t and _distancia2(f, firmas[i]) <= eps * eps for i in K):       
            malas["cobertura"] = f"la firma {t} se descartó pero ningún representante anterior la cubre"
            break
    return malas


def representante_de(t: int, firmas: Sequence[Firma | None], K: Sequence[int], eps: float) -> int | None:
    f = firmas[t]
    return next((i for i in K if i < t and f is not None and _distancia2(f, firmas[i]) <= eps * eps), None) 


def cota_de_perdida(datos: Datos, eps: float) -> float:
    if any(y == 0 for y in datos.ys):
        raise ValueError("el error relativo no está definido si algún y es 0")
    return eps * sum(1 / abs(y) for y in datos.ys) / len(datos)
