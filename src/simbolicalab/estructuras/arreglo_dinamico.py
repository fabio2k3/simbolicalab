from __future__ import annotations

import math
from typing import Any

from ..nucleo.amortizado import LibroAmortizado
from ..nucleo.contador import Contador

class ArregloDinamico:
    def __init__(self, factor: float = 2.0, reduccion: str = "nunca", contador: Contador | None = None, libro: LibroAmortizado | None = None, ) -> None:
        if factor <= 1:
            raise ValueError("el factor de crecimiento debe ser mayor que 1")
        if reduccion not in ("nunca", "cuarto", "mitad"):
            raise ValueError("reduccion debe ser 'nunca', 'cuarto' o 'mitad'")

        self.factor, self.reduccion = factor, reduccion
        self.contador = contador if contador is not None else Contador()
        self.libro = libro
        self._bloque: list[Any] = []
        self._tamano = 0
        self._cobrado = 0
        self._gastado = 0

    def __len__(self) -> int:
                return self._tamano
    
    @property
    def capacidad(self) -> int:
        return len(self._bloque)
    
    def __getitem__(self, i:int) -> Any:
        if not 0 <= i  < self._tamano:
            raise IndexError(i)
        return self._bloque[i]
    
    def a_lista(self) -> list[Any]:
        return self._bloque[: self._tamano]
            
    def potencial(self) -> float:
        t, c = self._tamano , self.potencial
        return 2 * t - c if 2 * t >= c else c / 2 - t
    
    def credito(self) -> int:
         return self._cobrado - self._gastado

    def _redimensionar(self, nueva_capacidad: int) -> None:
        self.contador.tick(self._tamano, "copia")
        nuevo = [None] * nueva_capacidad
        nuevo[: self._tamano] = self._bloque[: self._tamano]
        self._bloque = nuevo

    def _cerrar_operacion(self, antes: int, tarifa: int) -> None:
        real = self.contador.total - antes
        self._gastado += real
        self._cobrado += tarifa
        if self.libro is not None:
            self.libro.registrar(real, self.potencial())

    def append(self, x: Any) -> None:
        antes = self.contador.total
        if self._tamano == self.capacidad:
            self._redimensionar(max(self.capacidad + 1, math.ceil(self.capacidad * self.factor)))
        self.contador.tick(1, "escritura")
        self._bloque[self._tamano] = x
        self._tamano += 1
        self._cerrar_operacion(antes, 3)

    def pop(self) -> Any:
        if self._tamano == 0:
            raise IndexError("pop de un arreglo vacío")
        antes = self.contador.total
        self.contador.tick(1, "pop")
        self._tamano -= 1
        x = self._bloque[self._tamano]
        self._bloque[self._tamano] = None
        c = self.capacidad
        if self.reduccion == "cuarto" and c >= 4 and self._tamano * 4 <= c:
            self._redimensionar(c // 2)
        elif self.reduccion == "mitad" and c >= 2 and self._tamano * 2 <= c:
            self._redimensionar(c // 2)
        self._cerrar_operacion(antes, 0)
        return x
