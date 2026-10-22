import math
import pytest

from simbolicalab.nucleo import Presupuesto, Solver, Traza
from simbolicalab.solvers import SolverMedia


DATOS = [(0, 1.0), (1, 2.0), (2, 3.0), (3, 4.0)]    


def test_solver_media_cumple_el_protocolo():
    assert isinstance(SolverMedia(), Solver)


def test_solver_media_resuelve_y_cuenta():
    r = SolverMedia().resolver(DATOS, None, Presupuesto())
    assert r.expresion == pytest.approx(2.5)
    assert r.error == pytest.approx(1.25)
    assert r.operaciones == 2 * len(DATOS)           
    assert not r.agotado


def test_solver_media_respeta_el_presupuesto():
    r = SolverMedia().resolver(DATOS, None, Presupuesto(operaciones=3))
    assert r.agotado and r.expresion is None and math.isinf(r.error)


def test_solver_media_emite_traza():
    t = Traza()
    SolverMedia().resolver(DATOS, None, Presupuesto(), traza=t)
    assert [e.tipo for e in t.eventos] == ["media_calculada", "error_calculado"]
