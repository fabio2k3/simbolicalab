from __future__ import annotations
from ..nucleo.contador import Contador

def suma_contada(A: list[float], contador: Contador, fusionar_acceso_y_suma: bool = False) -> float:
    contador.tick(1, "asignacion")
    
    s = 0
    n = len(A)

    for i in range(n):
        contador.tick(1, "comparacion")
        if fusionar_acceso_y_suma:
            contador.tick(1, "acceso+suma")
        else:
            contador.tick(1, "acceso")
            contador.tick(1, "suma")
        contador.tick(1, "asignacion")
        contador.tick(1, "incremento")
        s = s + A[i]

    contador.tick(1, "comparacion")
    contador.tick(1, "retorno")

    return s