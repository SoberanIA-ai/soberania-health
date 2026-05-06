"""Sirve el dashboard HTML conectado a la API.

GET /dashboard → dashboard/hitl_dashboard.html
GET /logo.png  → dashboard/logo.png  (referenciado por el JSX del bundle)

Diseño bundleado por Claude Design (React + Babel standalone). El JS
de la app hace fetch a los endpoints /api/v1/* del mismo origin.

Para reconstruir el HTML tras cambios en el JS de la app:
    docker compose exec api python scripts/build_dashboard_html.py
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(tags=["dashboard"])

DASHBOARD_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "dashboard"
)
DASHBOARD_HTML = DASHBOARD_DIR / "hitl_dashboard.html"
LOGO_PNG = DASHBOARD_DIR / "logo.png"


@router.get("/dashboard", response_class=FileResponse)
async def dashboard():
    if not DASHBOARD_HTML.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Dashboard HTML no encontrado. Reconstruir con "
                "`python scripts/build_dashboard_html.py`."
            ),
        )
    return FileResponse(DASHBOARD_HTML, media_type="text/html")


@router.get("/logo.png", response_class=FileResponse)
async def logo():
    """El JSX del Header carga `logo.png` con path relativo."""
    if not LOGO_PNG.exists():
        raise HTTPException(status_code=404, detail="logo.png no encontrado")
    return FileResponse(LOGO_PNG, media_type="image/png")
