from __future__ import annotations

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class UsuarioResponse(BaseModel):
    id: str
    email: str
    nombre: str
    rol: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse