"""Módulo de consulta vehicular SUNARP por placa.

Aislado del resto del mock SAP. Expone un router FastAPI (`placas.router`) que,
por cada consulta, lanza un *worker efímero* (subproceso con Chrome propio que se
mata al timeout) que resuelve el Cloudflare Turnstile y devuelve la foto del
vehículo en base64. Ver placas/README.md.
"""
