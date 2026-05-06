"""Sirve el dashboard HTML conectado a la API.

GET /dashboard → dashboard/hitl_dashboard.html

Diseño bundleado por Claude Design (React + Babel standalone). El JS
de la app hace fetch a los endpoints /api/v1/* del mismo origin.

Para reconstruir el HTML tras cambios en el JS de la app:
    docker compose exec api python scripts/build_dashboard_html.py
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(tags=["dashboard"])

DASHBOARD_HTML = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "dashboard"
    / "hitl_dashboard.html"
)


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
