from fastapi.testclient import TestClient

from app.main import app


def test_health_responde_con_estado_json():
    respuesta = TestClient(app).get("/health")
    assert respuesta.status_code in (200, 503)
    assert "status" in respuesta.json()
