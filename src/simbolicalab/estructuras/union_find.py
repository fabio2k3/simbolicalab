from __future__ import annotations

import math

from ..nucleo.contador import Contador


class UnionFind:
    def __init__(self, n: int, por_rango: bool = True, compresion: bool = True, rango_en_empate: bool = True, contador: Contador | None = None,) -> None:
        if n < 0:
            raise ValueError("n no puede ser negativo")
        
        self.n = n
        self.padre = list(range(n))
        self.rango = [0] * n
        self.por_rango, self.compresion, self.rango_en_empate = por_rango, compresion, rango_en_empate
        self.contador = contador if contador is not None else Contador()
        self.conjuntos = n

    def find(self, x: int) -> int:
        raiz = x

        while self.padre[raiz] != raiz:
            raiz = self.padre[raiz]
            self.contador.tick(1, "paso")

        if self.compresion:                             
            while self.padre[x] != raiz:
                self.padre[x], x = raiz, self.padre[x]
        return raiz

    def union(self, a: int, b: int) -> bool:
        a, b = self.find(a), self.find(b)
        
        if a == b:
            return False
        if self.por_rango and self.rango[a] < self.rango[b]:
            a, b = b, a
        self.padre[b] = a
        if self.por_rango and self.rango[a] == self.rango[b] and self.rango_en_empate:
            self.rango[a] += 1
        self.conjuntos -= 1
        return True

    
    def _raiz_sin_comprimir(self, x: int) -> int:
        while self.padre[x] != x:
            x = self.padre[x]
        return x

    def profundidad(self, x: int) -> int:
        d = 0
        while self.padre[x] != x:
            x, d = self.padre[x], d + 1
        return d

    def altura_maxima(self) -> int:
        return max((self.profundidad(x) for x in range(self.n)), default=0)

    def clases(self) -> dict[int, list[int]]:
        grupos: dict[int, list[int]] = {}
        for x in range(self.n):
            grupos.setdefault(self._raiz_sin_comprimir(x), []).append(x)
        return grupos

    def verificar_propiedades(self) -> None:
        for x in range(self.n):
            if self.padre[x] != x:
                assert self.rango[x] < self.rango[self.padre[x]], \
                    f"P1: el nodo {x} (rango {self.rango[x]}) no tiene rango menor que su padre {self.padre[x]}"
                
        for raiz, miembros in self.clases().items():
            assert len(miembros) >= 2 ** self.rango[raiz], \
                f"P2: la raíz {raiz} tiene rango {self.rango[raiz]} pero su árbol solo tiene {len(miembros)} nodos"
            
        por_rango: dict[int, int] = {}

        for r in self.rango:
            por_rango[r] = por_rango.get(r, 0) + 1

        for r, cuantos in por_rango.items():
            assert cuantos <= self.n / 2 ** r + 1e-9, f"P3: hay {cuantos} nodos de rango {r} y el máximo es {self.n / 2 ** r}"

        if self.n > 1:
            assert max(self.rango) <= math.log2(self.n) + 1e-9, "P3: algún rango pasa de log2 n"
