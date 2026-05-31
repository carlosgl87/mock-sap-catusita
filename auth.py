"""Validación del API key para el Mock SAP de Catusita."""
from fastapi import Header, HTTPException
import os


async def verify_api_key(x_api_key: str = Header(None)):
    """Dependency de FastAPI que valida el header X-API-Key.

    Si el header falta o no coincide con MOCK_API_KEY, devuelve 401.
    """
    expected = os.getenv("MOCK_API_KEY", "catusita-mock-key-2024")
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="API Key inválida o ausente")
    return x_api_key
