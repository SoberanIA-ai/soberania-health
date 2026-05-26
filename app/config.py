from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://soberania:soberania@localhost:5432/health"

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
    jwt_secret_key: str = "CAMBIAR-EN-PRODUCCION-clave-secreta-soberania-health-2026"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 horas — una jornada laboral completa

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


settings = Settings()
