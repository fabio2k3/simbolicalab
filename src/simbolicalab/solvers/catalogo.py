from __future__ import annotations

from .combinado import SolverCombinado
from .espectral import SolverEspectral
from .fuerza_bruta import SolverFuerzaBruta
from .greedy import SolverGreedy
from .media import SolverMedia
from .dp import SolverDP


def solvers_del_tema2(max_tam: int = 4, k_goloso: int = 2, m_frecuencias: int = 2, k_max: int = 5) -> dict:
    return {
        "media": SolverMedia(),
        "fuerza_bruta": SolverFuerzaBruta(max_tam),
        "dp": SolverDP(max_tam),
        "greedy": SolverGreedy(k_goloso, max_tam),
        "espectral": SolverEspectral(m_frecuencias),
        "combinado": SolverCombinado(max_tam, k_max, m_frecuencias=m_frecuencias),
    }