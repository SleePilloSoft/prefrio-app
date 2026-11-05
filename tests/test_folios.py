from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models as m
from app.db import Base
from app.folios import folio_para


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture
def sesion():
    motor = create_engine("sqlite://")
    Base.metadata.create_all(motor)
    with sessionmaker(bind=motor)() as s:
        yield s


def ciclo_con_asignacion(sesion, tunel="PREFRIO-TUNEL-1", inicio=utc(2026, 11, 5, 12), fin=None):
    ciclo = m.Ciclo(tunel=tunel, iniciado_utc=inicio, terminado_utc=fin)
    sesion.add(ciclo)
    sesion.commit()
    sesion.add(m.AsignacionPosicion(ciclo_id=ciclo.id, posicion="A1", folio="1001"))
    sesion.commit()
    return ciclo


def test_resuelve_folio_dentro_del_ciclo_activo(sesion):
    ciclo_con_asignacion(sesion)
    assert folio_para(sesion, "PREFRIO-TUNEL-1", "A1", utc(2026, 11, 5, 21)) == "1001"


def test_lectura_anterior_al_inicio_del_ciclo_no_tiene_folio(sesion):
    ciclo_con_asignacion(sesion, inicio=utc(2026, 11, 5, 12))
    assert folio_para(sesion, "PREFRIO-TUNEL-1", "A1", utc(2026, 11, 5, 11)) is None


def test_lectura_posterior_al_cierre_no_tiene_folio(sesion):
    ciclo_con_asignacion(sesion, fin=utc(2026, 11, 5, 20))
    assert folio_para(sesion, "PREFRIO-TUNEL-1", "A1", utc(2026, 11, 5, 21)) is None


def test_posicion_sin_pallet_o_sin_asignacion_no_tiene_folio(sesion):
    ciclo_con_asignacion(sesion)
    assert folio_para(sesion, "PREFRIO-TUNEL-1", "TUNEL", utc(2026, 11, 5, 21)) is None
    assert folio_para(sesion, "PREFRIO-TUNEL-1", None, utc(2026, 11, 5, 21)) is None
    assert folio_para(sesion, "PREFRIO-TUNEL-1", "B5", utc(2026, 11, 5, 21)) is None


def test_ciclo_de_otro_tunel_no_aplica(sesion):
    ciclo_con_asignacion(sesion, tunel="PREFRIO-TUNEL-1")
    assert folio_para(sesion, "PREFRIO-TUNEL-2", "A1", utc(2026, 11, 5, 21)) is None
