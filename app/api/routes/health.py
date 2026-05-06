from fastapi import APIRouter

router = APIRouter(tags=["health"])

CALCULADORES_VERSION = "1.0.0-simulado"
APP_VERSION = "0.1.0"


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": APP_VERSION,
        "calculadores_version": CALCULADORES_VERSION,
    }
