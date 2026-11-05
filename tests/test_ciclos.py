import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models as m
from app.auth import hash_token
from app.db import Base, get_session
from app.main import app as aplicacion

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

    aplicacion.dependency_overrides[get_session] = sesion_de_prueba
    yield TestClient(aplicacion)
    aplicacion.dependency_overrides.clear()


def autorizado():
    return {"Authorization": f"Bearer {TOKEN}"}


def abrir(http, tunel="PREFRIO-TUNEL-1"):
    return http.post("/api/v1/ciclos", json={"tunel": tunel}, headers=autorizado())


def test_abrir_ciclo_sin_token_responde_401(cliente):
    r = cliente.post("/api/v1/ciclos", json={"tunel": "PREFRIO-TUNEL-1"})
    assert r.status_code == 401


def test_abrir_ciclo_y_no_abrir_otro_en_el_mismo_tunel(cliente):
    r = abrir(cliente)
    assert r.status_code == 201
    assert r.json()["terminado_utc"] is None
    assert abrir(cliente).status_code == 409


def test_asignar_posiciones_y_rechazar_posicion_tunel(cliente):
    ciclo = abrir(cliente).json()
    url = f"/api/v1/ciclos/{ciclo['id']}/asignaciones"
    ok = cliente.post(
        url,
        json={"asignaciones": [{"posicion": "A1", "folio": "1001"}, {"posicion": "A2", "folio": "1002"}]},
        headers=autorizado(),
    )
    assert ok.status_code == 201
    assert ok.json() == {"asignadas": 2}
    malo = cliente.post(
        url,
        json={"asignaciones": [{"posicion": "TUNEL", "folio": "1003"}]},
        headers=autorizado(),
    )
    assert malo.status_code == 422


def test_folio_o_posicion_repetida_en_el_mismo_ciclo_responde_409(cliente):
    ciclo = abrir(cliente).json()
    url = f"/api/v1/ciclos/{ciclo['id']}/asignaciones"
    cliente.post(url, json={"asignaciones": [{"posicion": "A1", "folio": "1001"}]}, headers=autorizado())
    r = cliente.post(url, json={"asignaciones": [{"posicion": "A1", "folio": "1002"}]}, headers=autorizado())
    assert r.status_code == 409


def test_ciclo_cerrado_no_acepta_asignaciones(cliente):
    ciclo = abrir(cliente).json()
    cierre = cliente.post(f"/api/v1/ciclos/{ciclo['id']}/cierre", headers=autorizado())
    assert cierre.status_code == 200
    assert cierre.json()["terminado_utc"] is not None
    r = cliente.post(
        f"/api/v1/ciclos/{ciclo['id']}/asignaciones",
        json={"asignaciones": [{"posicion": "A1", "folio": "1001"}]},
        headers=autorizado(),
    )
    assert r.status_code == 409


def test_despues_de_cerrar_se_puede_abrir_otro_ciclo(cliente):
    ciclo = abrir(cliente).json()
    cliente.post(f"/api/v1/ciclos/{ciclo['id']}/cierre", headers=autorizado())
    assert abrir(cliente).status_code == 201
