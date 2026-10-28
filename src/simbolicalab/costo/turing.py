from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..nucleo.contador import Contador, PresupuestoAgotado
from ..nucleo.traza import TRAZA_NULA, Traza

_MOVIMIENTO = {"L": -1, "R": 1, "S": 0}

Transiciones = Mapping[tuple[str, str], tuple[str, str, str]]


@dataclass(frozen=True)
class ResultadoMT:
    aceptada: bool
    pasos: int
    cinta: str        
    cabezal: int      


class MaquinaTuring:
    def __init__(self, transiciones: Transiciones, inicial: str, finales: frozenset[str], 
                    aceptan: frozenset[str], blanco: str = "_",) -> None:
        
        if not aceptan <= finales:
            raise ValueError("los estados de aceptación deben ser estados finales")
        for (_, leido), (escribe, mueve, _) in transiciones.items():
            if mueve not in _MOVIMIENTO:
                raise ValueError(f"movimiento inválido: {mueve!r}")
            if len(leido) != 1 or len(escribe) != 1:
                raise ValueError("los símbolos deben ser de un carácter")
        self.transiciones = dict(transiciones)
        self.inicial = inicial
        self.finales = finales
        self.aceptan = aceptan
        self.blanco = blanco

    def ejecutar(self, entrada: str, cabezal: int = 0, *, contador: Contador | None = None, 
                 traza: Traza | None = None, limite_pasos: int = 10_000_000,) -> ResultadoMT:
        
        traza = traza or TRAZA_NULA
        cinta = {i: s for i, s in enumerate(entrada) if s != self.blanco}
        estado, pasos = self.inicial, 0

        while estado not in self.finales:
            leido = cinta.get(cabezal, self.blanco)
            try:
                escribe, mueve, nuevo = self.transiciones[(estado, leido)]
            except KeyError:
                raise ValueError(f"sin transición para (estado={estado!r}, símbolo={leido!r})") from None
            if pasos >= limite_pasos:
                raise PresupuestoAgotado(limite_pasos, pasos + 1)
            pasos += 1
            if contador is not None:
                contador.tick(1, "paso")
            traza.emitir("paso", estado=estado, posicion=cabezal, leido=leido, escrito=escribe, mueve=mueve)
            if escribe == self.blanco:
                cinta.pop(cabezal, None)
            else:
                cinta[cabezal] = escribe
            cabezal += _MOVIMIENTO[mueve]
            estado = nuevo

        if not cinta:
            return ResultadoMT(estado in self.aceptan, pasos, "", cabezal)
        primero, ultimo = min(cinta), max(cinta)
        texto = "".join(cinta.get(i, self.blanco) for i in range(primero, ultimo + 1))
        return ResultadoMT(estado in self.aceptan, pasos, texto, cabezal - primero)


def maquina_palindromo() -> MaquinaTuring:
    t: dict[tuple[str, str], tuple[str, str, str]] = {("inicio", "_"): ("_", "S", "acepta")}
    for c in "01":
        t[("inicio", c)] = ("_", "R", f"lleva{c}")        
        for otro in "01":
            t[(f"lleva{c}", otro)] = (otro, "R", f"lleva{c}")  
        t[(f"lleva{c}", "_")] = ("_", "L", f"compara{c}")      
        t[(f"compara{c}", c)] = ("_", "L", "regresa")         
        t[(f"compara{c}", "_")] = ("_", "S", "acepta")     
        t[(f"compara{c}", "1" if c == "0" else "0")] = ("_", "S", "rechaza")
    for otro in "01":
        t[("regresa", otro)] = (otro, "L", "regresa")         
    t[("regresa", "_")] = ("_", "R", "inicio")
    return MaquinaTuring(t, "inicio", frozenset({"acepta", "rechaza"}), frozenset({"acepta"}))


def maquina_incremento() -> MaquinaTuring:
    t = {
        ("suma", "1"): ("0", "L", "suma"),
        ("suma", "0"): ("1", "R", "vuelve"),
        ("suma", "_"): ("1", "R", "vuelve"),
        ("vuelve", "0"): ("0", "R", "vuelve"),
        ("vuelve", "1"): ("1", "R", "vuelve"),
        ("vuelve", "_"): ("_", "L", "fin"),
    }
    return MaquinaTuring(t, "suma", frozenset({"fin"}), frozenset({"fin"}))


def incrementar_k_veces(k: int, contador: Contador | None = None) -> int:
    maquina = maquina_incremento()
    cinta, cabezal, total = "0", 0, 0
    for _ in range(k):
        r = maquina.ejecutar(cinta, cabezal, contador=contador)
        cinta, cabezal, total = r.cinta, r.cabezal, total + r.pasos
    return total


def palindromo_ram(s: str, contador: Contador) -> bool:
    n = len(s)
    for i in range(n // 2):
        contador.tick(1, "comparacion")
        if s[i] != s[n - 1 - i]:
            return False
    return True
