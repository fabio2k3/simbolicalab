import pytest

from simbolicalab.rs import Const, Gramatica, Var


def test_terminales_en_orden_fijo():
    g = Gramatica(variables=("x", "y"), constants=(1.0,))
    assert g.terminales == (Var("x"), Var("y"), Const(1.0))
    assert g.n_terminales == 3


@pytest.mark.parametrize("kw", [
    dict(variables=(), constants=()),                 
    dict(unarios=("sqrt", "sqrt")),                    
    dict(unarios=("+",)),                              
    dict(binarios=("sqrt",)),                          
    dict(binarios=("^",)),                         
    dict(constants=(float("nan"),)),                  
])
def test_gramaticas_invalidas(kw):
    with pytest.raises(ValueError):
        Gramatica(**kw)
