from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

import app.models as m
from app.db import Base


@pytest.fixture
def sesion():
    motor = create_engine("sqlite://")
    Base.metadata.create_all(motor)
    with sessionmaker(bind=motor)() as s:
        yield s


def lectura(dispositivo="prefrio1", id_local=1):
    return m.Lectura(
        dispositivo=dispositivo,
        id_local=id_local,
        sensor_id="28-0000007850a3",
        tipo="ds18b20",
        tunel="PREFRIO-TUNEL-1",
        posicion="A1",
        fecha_utc=datetime(2026, 11, 5, 21, 10, tzinfo=timezone.utc),
        temperatura=0.44,
    )


def test_lectura_repetida_mismo_dispositivo_e_id_local_se_rechaza(sesion):
    sesion.add(lectura())
    sesion.commit()
    sesion.add(lectura())
    with pytest.raises(IntegrityError):
        sesion.commit()


def test_mismo_id_local_en_otro_dispositivo_si_se_permite(sesion):
    sesion.add(lectura(dispositivo="prefrio1", id_local=1))
    sesion.add(lectura(dispositivo="prefrio2", id_local=1))
    sesion.commit()
    assert sesion.query(m.Lectura).count() == 2


def test_posicion_no_se_repite_dentro_del_mismo_ciclo(sesion):
    ciclo = m.Ciclo(tunel="PREFRIO-TUNEL-1")
    sesion.add(ciclo)
    sesion.commit()
    sesion.add(m.AsignacionPosicion(ciclo_id=ciclo.id, posicion="A1", folio="1001"))
    sesion.commit()
    sesion.add(m.AsignacionPosicion(ciclo_id=ciclo.id, posicion="A1", folio="1002"))
    with pytest.raises(IntegrityError):
        sesion.commit()
