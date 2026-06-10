"""
Autenticación JWT para el dashboard.

POST /api/v1/auth/login  → email + password → JWT token (8h)
GET  /api/v1/auth/me     → datos del usuario (requiere token)

El token se guarda en localStorage del cliente.
El dashboard incluye el token en cada petición:
  Authorization: Bearer <token>
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.api.schemas.usuario import LoginRequest, TokenResponse, UsuarioResponse
from app.config import settings
from app.models.database import get_db
from app.models.usuario import Usuario

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def crear_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_usuario_actual(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Usuario:
    """Dependencia FastAPI para endpoints protegidos."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expirado o inválido")

    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == email, Usuario.activo == True)  # noqa: E712
        .first()
    )
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return usuario


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if not usuario or not pwd_context.verify(payload.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Usuario desactivado")

    usuario.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()

    token = crear_token({"sub": usuario.email, "rol": usuario.rol})
    return TokenResponse(
        access_token=token,
        usuario=UsuarioResponse(
            id=str(usuario.id),
            email=usuario.email,
            nombre=usuario.nombre,
            rol=usuario.rol,
        ),
    )


@router.get("/me", response_model=UsuarioResponse)
async def me(usuario: Usuario = Depends(get_usuario_actual)):
    return UsuarioResponse(
        id=str(usuario.id),
        email=usuario.email,
        nombre=usuario.nombre,
        rol=usuario.rol,
    )


def require_roles(*roles: str):
    """Dependencia FastAPI: exige que el usuario autenticado tenga uno de `roles`.

    Uso: `_usuario: Usuario = Depends(require_roles("admin", "supervisor"))`.
    Devuelve 403 si el usuario está autenticado pero no tiene el rol requerido.
    """

    def _verificar(usuario: Usuario = Depends(get_usuario_actual)) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para realizar esta operación",
            )
        return usuario

    return _verificar