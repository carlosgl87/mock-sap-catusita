"""Configuración del módulo de placas (vía variables de entorno).

Todo es configurable sin tocar código; los defaults sirven para correr local.
"""
import os

# Segundos máximos por consulta antes de matar el worker efímero (Chrome incluido).
TIMEOUT = int(os.getenv("PLACAS_TIMEOUT", "90"))

# Reintentos por placa si el worker falla o se cuelga (total intentos = RETRIES + 1).
RETRIES = int(os.getenv("PLACAS_RETRIES", "0"))

# Nombre de la variable de entorno que el worker lee para saber dónde escribir.
# El service crea una carpeta temporal por consulta y la pasa por aquí.
OUTDIR_ENV = "PLACAS_OUTDIR"
