from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import audit, autorizaciones, auth, health, notificaciones
from app.config import settings
from app.integrations import doctoris_webhook

app = FastAPI(
    title="SoberanIA Health",
    description="Agente de Autorizaciones — vertical salud SoberanIA",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(autorizaciones.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(notificaciones.router, prefix="/api/v1")
app.include_router(doctoris_webhook.router, prefix="/api/v1")
