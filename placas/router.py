"""Router FastAPI del módulo de placas (montado bajo /placas en main.py).

- GET /placas/status         público; reporta si el entorno está listo (sin scrapear).
- GET /placas/{placa}        protegido; dispara una consulta efímera y devuelve
                             JSON + imagen del vehículo en base64.

Las consultas se serializan con un lock: el bypass del Turnstile usa un click real
sobre un único display, así que dos consultas en paralelo se pisarían.
"""
import asyncio
import os

from fastapi import APIRouter, Depends, HTTPException, Query

from auth import verify_api_key
from . import config, service

router = APIRouter(prefix="/placas", tags=["placas"])

# Single-flight: una consulta a la vez (mouse/display compartido).
_lock = asyncio.Lock()

# Mapeo de status_hint del service -> código HTTP de error.
_HTTP_ERROR = {"not_found": 404, "timeout": 504, "error": 502}


def _entorno_listo():
    """¿Está el entorno preparado para consultar? (seleniumbase + display en Linux)."""
    try:
        import seleniumbase  # noqa: F401
    except Exception as e:
        return False, f"seleniumbase no disponible: {e}"
    if os.name != "nt" and not os.environ.get("DISPLAY"):
        return False, "Sin DISPLAY (Xvfb no arrancó)."
    return True, "ok"


@router.get("/status")
async def status():
    listo, detalle = _entorno_listo()
    return {
        "modulo": "placas",
        "listo": listo,
        "detalle": detalle,
        "timeout_s": config.TIMEOUT,
        "reintentos": config.RETRIES,
        "consulta_en_curso": _lock.locked(),
    }


@router.get("/{placa}", dependencies=[Depends(verify_api_key)])
async def consultar_placa(placa: str, imagen: bool = Query(True),
                          debug: bool = Query(False)):
    listo, detalle = _entorno_listo()
    if not listo:
        raise HTTPException(status_code=503, detail=detalle)

    async with _lock:
        resultado = await asyncio.to_thread(service.consultar, placa, imagen, debug)

    # En modo debug devolvemos 200 con el dict completo (incluye screenshots)
    # aunque la consulta falle, para poder inspeccionar qué pasó.
    if debug:
        return resultado

    if resultado.get("status_hint") == "ok":
        resultado.pop("status_hint", None)
        return resultado

    hint = resultado.get("status_hint", "error")
    raise HTTPException(
        status_code=_HTTP_ERROR.get(hint, 502),
        detail=resultado.get("mensaje", "No se pudo completar la consulta."),
    )
