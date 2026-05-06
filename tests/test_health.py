from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_responde_200():
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_payload():
    response = client.get("/api/v1/health")
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "calculadores_version" in data
