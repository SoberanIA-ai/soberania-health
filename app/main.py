from fastapi import FastAPI

from app.api.routes import health

app = FastAPI(
    title="SoberanIA Health",
    description="Agente de Autorizaciones — vertical salud SoberanIA",
    version="0.1.0",
)

app.include_router(health.router, prefix="/api/v1")
