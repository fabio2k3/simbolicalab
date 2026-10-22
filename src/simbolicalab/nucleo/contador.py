from __future__ import annotations

from collections import Counter
from typing import Any, Callable

class PresupuestoAgotado(Exception):
    def __init__(self, limite: int, gastado: int) -> None:
        super().__init__(f"presupuesto agotado: {gastado} > {limite} operaciones")
        self.limite = limite
        self.gastado = gastado

class Contador:
    def __init__(self, limite: int | None = None) -> None:
        if limite is not None and limite < 0:
            raise ValueError("el  limite no puede ser negativo")
        self.limite = limite
        self._total = 0
        self._por_categoria: Counter[str] = Counter()

    def tick(self, n: int = 1, categoria: str = "op") -> None:
        if n < 0:
            raise ValueError("no se puede contar operaciones negativas")

        self._total += n
        self._por_categoria[categoria] += n

        if self.limite is not None and self._total > self.limite:
            raise PresupuestoAgotado(self.limite, self._total)

    @property
    def total(self) -> int:
        return self._total

    @property
    def por_categoria(self) -> dict[str, int]:
        return dict(self._por_categoria)

    @property
    def restatne(self) -> int | None:
        return None if self.limite is None else max(self.limite - self._total, 0)

    def __repr__(self) -> str:
        lim = "sin limite" if self.limite is None else f"limite {self.limite}"
        return f"Contador(total = {self._total}, {lim})"

def medir(algoritmo: Callable[..., Any], *args: Any, limite: int | None = None, **kwargs: Any) -> tuple[Any, Contador]:
    c = Contador(limite) 
    resultado = algoritmo(*args, Contador = c, **kwargs) 
    return resultado, c