from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_JWT_SECRET_DEFAULT = "CAMBIAR-EN-PRODUCCION-clave-secreta-soberania-health-2026"
_DATABASE_URL_DEFAULT = "postgresql://soberania:soberania@localhost:5432/health"


class Settings(BaseSettings):
    environment: str = "development"  # "production" activa validaciones de seguridad estrictas

    database_url: str = _DATABASE_URL_DEFAULT

    mistral_api_key: str = ""

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3000"

    confidence_threshold_hitl: float = 0.80
    modo_default: str = "mock"
    mock_connector_seed: int | None = None  # set para demos reproducibles

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notification_email_from: str = "health@soberania.eu"

    audit_log_enabled: bool = True
    hitl_obligatorio_modo_real: bool = True

    # Auth JWT
    jwt_secret_key: str = _JWT_SECRET_DEFAULT
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 horas — una jornada laboral completa

    # CORS — orígenes permitidos para llamadas del frontend, separados por coma
    cors_origins: str = "http://localhost:3002,http://127.0.0.1:3002"

    # Pool de conexiones DB
    db_pool_size: int = 5
    db_max_overflow: int = 10

    sanitas_portal_url: str = ""
    sanitas_user: str = ""
    sanitas_password: str = ""
    adeslas_portal_url: str = ""
    adeslas_user: str = ""
    adeslas_password: str = ""
    dkv_portal_url: str = ""
    dkv_user: str = ""
    dkv_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @model_validator(mode="after")
    def _validar_secretos_produccion(self) -> "Settings":
        """En producción, no permitimos arrancar con secretos/credenciales de demo.

        Mejor fallar al arrancar que exponer un JWT forjable o una DB con
        credenciales públicas (sec "Estado de los datos" del README).
        """
        if self.environment == "production":
            if self.jwt_secret_key == _JWT_SECRET_DEFAULT:
                raise RuntimeError(
                    "JWT_SECRET_KEY sigue en su valor por defecto inseguro. "
                    "Defínelo en el entorno antes de arrancar en producción."
                )
            if self.database_url == _DATABASE_URL_DEFAULT:
                raise RuntimeError(
                    "DATABASE_URL sigue usando las credenciales de demo. "
                    "Defínelo en el entorno antes de arrancar en producción."
                )
        return self


settings = Settings()
