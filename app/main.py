from fastapi import FastAPI

from app.api.routes import audit, autorizaciones, health

app = FastAPI(
    title="SoberanIA Health",
    description="Agente de Autorizaciones — vertical salud SoberanIA",
    version="0.1.0",
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(autorizaciones.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
