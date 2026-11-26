from .media import SolverMedia
from .fuerza_bruta import SolverFuerzaBruta
from .dp import SolverDP
from .greedy import SolverGreedy
from .espectral import SolverEspectral
from .combinado import SolverCombinado
from .catalogo import solvers_por_tecnica

__all__ = ["SolverMedia", "SolverFuerzaBruta", "SolverDP", "SolverGreedy", "SolverEspectral",
           "SolverCombinado", "solvers_por_tecnica",]