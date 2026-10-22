import json
import pytest

from simbolicalab.nucleo import Contador, PresupuestoAgotado, TRAZA_NULA, Traza


def test_contador_suma_y_categorias():
    c = Contador()
    c.tick()
    c.tick(5, "comparacion")
    assert c.total == 6
    assert c.por_categoria == {"op": 1, "comparacion": 5}


def test_contador_rechaza_negativos():
    with pytest.raises(ValueError):
        Contador().tick(-1)


def test_presupuesto_se_agota():
    c = Contador(limite=3)
    c.tick(3)                      
    assert c.restante == 0
    with pytest.raises(PresupuestoAgotado) as info:
        c.tick()                    
    assert info.value.limite == 3 and info.value.gastado == 4


def test_por_categoria_devuelve_copia():
    c = Contador()
    c.tick(2, "a")
    c.por_categoria["a"] = 999     
    assert c.por_categoria["a"] == 2


def test_traza_serializa_a_json():
    t = Traza()
    t.emitir("paso", i=1, valores=[1, 2, 3])
    datos = json.loads(t.a_json())
    assert datos["eventos"] == [{"tipo": "paso", "i": 1, "valores": [1, 2, 3]}]
    assert datos["truncada"] is False


def test_traza_se_trunca():
    t = Traza(maximo=2)
    for i in range(5):
        t.emitir("x", i=i)
    assert len(t) == 2 and t.truncada


def test_traza_reserva_la_palabra_tipo():
    with pytest.raises(ValueError):
        Traza().emitir("x", tipo="malo")


def test_traza_vacia_no_se_descarta_con_or():
    t = Traza()                 
    assert (t or TRAZA_NULA) is t
    assert (None or TRAZA_NULA) is TRAZA_NULA


def test_traza_nula_no_guarda_nada():
    TRAZA_NULA.emitir("x", a=1)
    assert len(TRAZA_NULA) == 0 and TRAZA_NULA.a_lista() == []
