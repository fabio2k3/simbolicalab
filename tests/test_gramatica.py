"""
tests/test_gramatica.py  —  La gramática rechaza definiciones absurdas
"""
import pytest

from simbolicalab.rs import Const, Gramatica, Var


def test_terminales_en_orden_fijo():
    g = Gramatica(variables=("x", "y"), constantes=(1.0,))
    assert g.terminales == (Var("x"), Var("y"), Const(1.0))
    assert g.n_terminales == 3


@pytest.mark.parametrize("kw", [
    dict(variables=(), constantes=()),                 # sin terminales
    dict(unarios=("sqrt", "sqrt")),                    # repetido
    dict(unarios=("+",)),                              # '+' no es unario
    dict(binarios=("sqrt",)),                          # 'sqrt' no es binario
    dict(binarios=("^",)),                             # no existe
    dict(constantes=(float("nan"),)),                  # no finita
])
def test_gramaticas_invalidas(kw):
    with pytest.raises(ValueError):
        Gramatica(**kw)
