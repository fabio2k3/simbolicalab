from __future__ import annotations

import math
from typing import Any

from ..nucleo.contador import Contador


class _Nodo:
    __slots__ = ("clave", "valor", "izq", "der", "padre")

    def __init__(self, clave: Any, valor: Any) -> None:
        self.clave, self.valor = clave, valor
        self.izq = self.der = self.padre = None


class ArbolSplay:
    def __init__(self, heuristica: str = "splay", contador: Contador | None = None) -> None:
        if heuristica not in ("splay", "raiz"):
            raise ValueError("heuristica debe ser 'splay' o 'raiz'")
        self.heuristica = heuristica
        self.contador = contador if contador is not None else Contador()
        self.raiz: _Nodo | None = None
        self._n = 0

    def __len__(self) -> int:
        return self._n


    def _rotar(self, x: _Nodo) -> None:
        p = x.padre
        g = p.padre

        if p.izq is x:
            p.izq = x.der
            if x.der is not None:
                x.der.padre = p
            x.der = p
        else:
            p.der = x.izq
            if x.izq is not None:
                x.izq.padre = p
            x.izq = p

        p.padre, x.padre = x, g

        if g is None:
            self.raiz = x
        elif g.izq is p:
            g.izq = x
        else:
            g.der = x
        self.contador.tick(1, "rotacion")


    def _splay(self, x: _Nodo) -> int:
        rotaciones = 0
        while x.padre is not None:
            p, g = x.padre, x.padre.padre
            if g is None:                                        
                self._rotar(x)
                rotaciones += 1
            elif (g.izq is p) == (p.izq is x):                       
                self._rotar(p)
                self._rotar(x)
                rotaciones += 2
            else:                                                    
                self._rotar(x)
                self._rotar(x)
                rotaciones += 2
        return rotaciones

    def _subir_a_la_raiz(self, x: _Nodo) -> int:
        rotaciones = 0
        while x.padre is not None:
            self._rotar(x)
            rotaciones += 1
        return rotaciones

    def _subir(self, x: _Nodo) -> int:
        return self._splay(x) if self.heuristica == "splay" else self._subir_a_la_raiz(x)

    def _bajar(self, clave: Any) -> tuple[_Nodo | None, _Nodo | None]:
        x, ultimo = self.raiz, None
        while x is not None:
            ultimo = x
            self.contador.tick(1, "comparacion")
            if clave == x.clave:
                return x, ultimo
            x = x.izq if clave < x.clave else x.der

        return None, ultimo

    def buscar(self, clave: Any) -> Any:
        x, ultimo = self._bajar(clave)
        objetivo = x if x is not None else ultimo

        if objetivo is not None:
            self._subir(objetivo)
        return None if x is None else x.valor

    def insertar(self, clave: Any, valor: Any = None) -> bool:
        x, ultimo = self._bajar(clave)
        if x is not None:
            x.valor = valor
            self._subir(x)
            return False
        nuevo = _Nodo(clave, valor)

        if ultimo is None:
            self.raiz = nuevo
        else:
            nuevo.padre = ultimo
            if clave < ultimo.clave:
                ultimo.izq = nuevo
            else:
                ultimo.der = nuevo

        self._n += 1
        self._subir(nuevo)
        return True


    def en_orden(self) -> list[tuple[Any, Any]]:
        salida, pila, x = [], [], self.raiz

        while pila or x is not None:
            while x is not None:
                pila.append(x)
                x = x.izq
            x = pila.pop()
            salida.append((x.clave, x.valor))
            x = x.der

        return salida

    def altura(self) -> int:
        if self.raiz is None:
            return 0
        pila, mejor = [(self.raiz, 1)], 0

        while pila:
            x, d = pila.pop()
            mejor = max(mejor, d)
            for h in (x.izq, x.der):
                if h is not None:
                    pila.append((h, d + 1))
        return mejor

    def _tamanos(self) -> dict[_Nodo, int]:
        tam: dict[_Nodo, int] = {}
        if self.raiz is None:
            return tam
        pila = [(self.raiz, False)]

        while pila:
            x, listo = pila.pop()
            if listo:
                tam[x] = 1 + (tam[x.izq] if x.izq else 0) + (tam[x.der] if x.der else 0)
            else:
                pila.append((x, True))
                for h in (x.izq, x.der):
                    if h is not None:
                        pila.append((h, False))
        return tam

    def potencial(self) -> float:
        return sum(math.log2(s) for s in self._tamanos().values())

    def verificar(self) -> None:
        orden = [k for k, _ in self.en_orden()]

        assert all(a < b for a, b in zip(orden, orden[1:])), "el recorrido en orden no es creciente"
        assert len(orden) == self._n, f"hay {len(orden)} nodos y se contaron {self._n}"
        assert self.raiz is None or self.raiz.padre is None, "la raíz tiene padre"
        
        for x in self._tamanos():
            for h in (x.izq, x.der):
                assert h is None or h.padre is x, "un hijo no apunta a su padre"

    def acceso_instrumentado(self, clave: Any) -> dict[str, float] | None:
        x, _ = self._bajar(clave)

        if x is None:
            return None
        
        tam = self._tamanos()
        phi_antes = sum(math.log2(s) for s in tam.values())
        rango_x = math.log2(tam[x])
        rotaciones = self._subir(x)

        return {
            "rotaciones": rotaciones,
            "costo": max(rotaciones, 1),                      
            "rango_x": rango_x,
            "n": self._n,
            "phi_antes": phi_antes,
            "phi_despues": self.potencial(),
        }


def verificar_lema_de_acceso(arbol: ArbolSplay, claves: list[Any], tolerancia: float = 1e-9) -> list[dict[str, float]]:
    violaciones = []

    for clave in claves:
        a = arbol.acceso_instrumentado(clave)
        if a is None:
            continue
        amortizado = a["costo"] + a["phi_despues"] - a["phi_antes"]
        cota = 3 * (math.log2(a["n"]) - a["rango_x"]) + 1
        if amortizado > cota + tolerancia:
            violaciones.append({"clave": clave, "amortizado": amortizado, "cota": cota, "exceso": amortizado - cota})

    return violaciones
