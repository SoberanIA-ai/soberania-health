from fastapi import FastAPI

from app.api.routes import audit, autorizaciones, auth, dashboard, health, notificaciones
from app.integrations import doctoris_webhook

app = FastAPI(
    title="SoberanIA Health",
    description="Agente de Autorizaciones — vertical salud SoberanIA",
    version="0.2.0",
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(autorizaciones.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(notificaciones.router, prefix="/api/v1")
app.include_router(doctoris_webhook.router, prefix="/api/v1")
app.include_router(dashboard.router)  # GET /dashboard (sin prefijo /api/v1)
