from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models as m
from app.auth import hash_token
from app.db import Base, get_session
from app.main import app

TOKEN = "token-de-prueba"


@pytest.fixture
def cliente():
    motor = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(motor)
    fabrica = sessionmaker(bind=motor)
    with fabrica() as s:
        s.add(m.Dispositivo(nombre="prefrio1", token_hash=hash_token(TOKEN)))
        s.commit()

    def sesion_de_prueba():
        with fabrica() as s:
            yield s

    app.dependency_overrides[get_session] = sesion_de_prueba
    yield TestClient(app), fabrica
    app.dependency_overrides.clear()


def lectura(id_local, posicion="A1", sensor="28-0000007850a3"):
    return {
        "id_local": id_local,
        "fecha_utc": "2026-11-05T21:10:49+00:00",
        "sensor_id": sensor,
        "tipo": "ds18b20",
        "posicion": posicion,
        "temperatura": 0.44,
        "humedad": None,
    }


def lote(lecturas, dispositivo="prefrio1"):
    return {"dispositivo": dispositivo, "tunel": "PREFRIO-TUNEL-1", "lecturas": lecturas}


def autorizado():
    return {"Authorization": f"Bearer {TOKEN}"}


def test_sin_token_responde_401(cliente):
    http, _ = cliente
    r = http.post("/api/v1/lecturas", json=lote([lectura(1)]))
    assert r.status_code == 401


def test_token_revocado_responde_401(cliente):
    http, fabrica = cliente
    with fabrica() as s:
        s.scalar(select(m.Dispositivo)).revocado_utc = datetime.now(timezone.utc)
        s.commit()
    r = http.post("/api/v1/lecturas", json=lote([lectura(1)]), headers=autorizado())
    assert r.status_code == 401


def test_dispositivo_distinto_al_token_responde_403(cliente):
    http, _ = cliente
    r = http.post("/api/v1/lecturas", json=lote([lectura(1)], dispositivo="otro"), headers=autorizado())
    assert r.status_code == 403


def test_lote_acepta_valida_y_rechaza_posicion_invalida(cliente):
    http, _ = cliente
    r = http.post(
        "/api/v1/lecturas",
        json=lote([lectura(1, "A1"), lectura(2, "Z9")]),
        headers=autorizado(),
    )
    assert r.status_code == 200
    assert r.json() == {
        "aceptadas": [1],
        "duplicadas": [],
        "rechazadas": [{"id_local": 2, "motivo": "posicion no valida"}],
    }


def test_reenvio_del_mismo_lote_marca_duplicadas(cliente):
    http, fabrica = cliente
    http.post("/api/v1/lecturas", json=lote([lectura(1)]), headers=autorizado())
    r = http.post("/api/v1/lecturas", json=lote([lectura(1)]), headers=autorizado())
    assert r.json()["duplicadas"] == [1]
    with fabrica() as s:
        assert s.query(m.Lectura).count() == 1


def test_lote_mayor_a_500_responde_422(cliente):
    http, _ = cliente
    r = http.post(
        "/api/v1/lecturas",
        json=lote([lectura(i) for i in range(501)]),
        headers=autorizado(),
    )
    assert r.status_code == 422
