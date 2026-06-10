"""Fixtures compartidos — autenticación simulada para tests de integración.

Desde que los endpoints de autorizaciones/audit requieren JWT
(Depends(get_usuario_actual)), los tests de integración necesitan
overridear esa dependencia para no tener que loguearse de verdad.

`auth_admin` da acceso total (rol admin pasa cualquier check de rol).
`client_as` permite simular un usuario con un rol concreto, útil para
tests de RBAC.
"""
import pytest

from app.api.routes.auth import get_usuario_actual
from app.main import app
from app.models.usuario import Usuario


def usuario_fake(rol: str = "admin") -> Usuario:
    """Usuario en memoria (no persistido) para overridear get_usuario_actual."""
    return Usuario(
        email=f"{rol}@test.soberania.eu",
        nombre=f"Test {rol.title()}",
        rol=rol,
        password_hash="x",
    )


@pytest.fixture
def auth_admin():
    """Override get_usuario_actual → usuario admin (acceso total)."""
    app.dependency_overrides[get_usuario_actual] = lambda: usuario_fake("admin")
    yield
    app.dependency_overrides.pop(get_usuario_actual, None)


@pytest.fixture
def client_as():
    """Factory: client_as("recepcionista") → TestClient autenticado con ese rol."""
    from fastapi.testclient import TestClient

    def _make(rol: str):
        app.dependency_overrides[get_usuario_actual] = lambda: usuario_fake(rol)
        return TestClient(app)

    yield _make
    app.dependency_overrides.pop(get_usuario_actual, None)
