"""
Notificaciones en tiempo real via SSE (Server-Sent Events).

GET /api/v1/notificaciones/stream → stream de eventos

El cliente JS hace:
  const sse = new EventSource('/api/v1/notificaciones/stream?token=<jwt>');
  sse.onmessage = (e) => mostrar_toast(JSON.parse(e.data));

Tipos de eventos:
  autorizacion_procesada  → nueva autorización en el sistema
  estado_cambiado         → una autorización cambió de estado
  hitl_pendiente          → hay casos nuevos en cola HITL
  hitl_resuelto           → un supervisor tomó una decisión

Bus interno: lista en memoria de queues asyncio por cliente conectado.
En producción con múltiples instancias → sustituir por Redis pub/sub.
"""
import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt

from app.config import settings

router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])

# Bus de eventos en memoria: {client_id: asyncio.Queue}
_clientes: dict[str, asyncio.Queue] = {}


async def _event_stream(queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    yield 'data: {"tipo": "conectado", "mensaje": "Stream activo"}\n\n'
    while True:
        try:
            evento = await asyncio.wait_for(queue.get(), timeout=30)
            yield f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"
        except asyncio.TimeoutError:
            yield ": ping\n\n"  # keepalive


@router.get("/stream")
async def stream_notificaciones(token: str = Query(...)):
    """SSE endpoint. El token JWT va en query param porque EventSource no permite headers."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        client_id = payload.get("sub", "anon")
    except JWTError:
        client_id = "anon"

    queue: asyncio.Queue = asyncio.Queue(maxsize=50)
    _clientes[client_id] = queue

    return StreamingResponse(
        _event_stream(queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


async def emitir_evento(tipo: str, datos: dict) -> None:
    """Llamado desde autorizacion_service cuando cambia un estado."""
    evento = {"tipo": tipo, **datos}
    dead = []
    for client_id, queue in _clientes.items():
        try:
            queue.put_nowait(evento)
        except asyncio.QueueFull:
            dead.append(client_id)
    for d in dead:
        _clientes.pop(d, None)