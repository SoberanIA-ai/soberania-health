"""Tests de autenticación JWT — Dashboard v2"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_correcto():
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "isabella.cristancho@soberania.eu", "password": "soberania2026"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["usuario"]["email"] == "isabella.cristancho@soberania.eu"
    assert data["usuario"]["rol"] == "admin"
    assert data["usuario"]["nombre"] == "Isabella Cristancho"


def test_login_password_incorrecto():
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "isabella.cristancho@soberania.eu", "password": "wrong"},
    )
    assert r.status_code == 401


def test_login_email_no_existe():
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "noexiste@test.com", "password": "algo"},
    )
    assert r.status_code == 401


def test_login_supervisor():
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "supervisor@hmhospitales.es", "password": "supervisor2026"},
    )
    assert r.status_code == 200
    assert r.json()["usuario"]["rol"] == "supervisor"


def test_login_auditor():
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "auditor@hmhospitales.es", "password": "auditor2026"},
    )
    assert r.status_code == 200
    assert r.json()["usuario"]["rol"] == "auditor"


def test_me_con_token_valido():
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "isabella.cristancho@soberania.eu", "password": "soberania2026"},
    )
    token = login.json()["access_token"]
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["nombre"] == "Isabella Cristancho"
    assert r.json()["email"] == "isabella.cristancho@soberania.eu"


def test_me_sin_token():
    r = client.get("/api/v1/auth/me")
    # HTTPBearer devuelve 403 si no hay Authorization header
    assert r.status_code == 403


def test_me_token_invalido():
    r = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer token-invalido-que-no-es-jwt"},
    )
    assert r.status_code == 401


def test_doctoris_status():
    r = client.get("/api/v1/integraciones/doctoris/status")
    assert r.status_code == 200
    assert r.json()["status"] == "STUB"


def test_doctoris_orden_stub():
    r = client.post(
        "/api/v1/integraciones/doctoris/orden",
        content=b"MSH|^~\\&|Doctoris|HM|SoberanIA|Health",
    )
    assert r.status_code == 200