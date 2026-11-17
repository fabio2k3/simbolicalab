from __future__ import annotations
from typing import Sequence
from .matroides import Oraculo, norma, producto


def independencia_por_pares(columnas: Sequence[Sequence[float]], tol: float = 1e-9) -> Oraculo:
    def indep(S: frozenset) -> bool:
        idx = sorted(S)
        for i in idx:
            if norma(columnas[i]) == 0.0:
                return False
            
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                u, v = columnas[idx[a]], columnas[idx[b]]
                if abs(producto(u, v)) >= (1 - tol) * norma(u) * norma(v):
                    return False
                
        return True
    
    
    return indep