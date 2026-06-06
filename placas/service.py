"""Orquestación del worker efímero (reemplaza al orquestador.py con Docker).

En Railway no hay Docker-in-Docker, así que en vez de `docker run --rm` lanzamos
un *subproceso* worker por consulta: Chrome nuevo cada vez, matado junto a todo su
árbol de procesos al llegar al timeout (se lleva el Chrome zombie), y carpeta de
salida temporal que se borra al terminar. Mismo beneficio (Chrome limpio por
consulta) sin Docker.

Es código bloqueante a propósito; el router lo invoca con asyncio.to_thread y
serializa las consultas (el click real del Turnstile usa un único mouse/display).
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

from . import config

_IS_WIN = os.name == "nt"


def _spawn(placa, outdir):
    """Lanza el worker como subproceso en su propio grupo de procesos."""
    env = {**os.environ, config.OUTDIR_ENV: outdir}
    cmd = [sys.executable, "-m", "placas.worker", placa]
    # Capturamos stdout+stderr para volcarlos a los logs (diagnóstico del Turnstile)
    # y poder devolver una pista en el error.
    common = dict(env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                  text=True, encoding="utf-8", errors="replace")
    if _IS_WIN:
        # Grupo de procesos propio para poder matar todo el árbol (taskkill /T).
        return subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                                **common)
    # POSIX: nueva sesión -> os.killpg mata worker + Chrome hijos.
    return subprocess.Popen(cmd, start_new_session=True, **common)


def _log(placa, salida):
    """Vuelca la salida del worker a los logs del server (aparece en Railway)."""
    if not salida:
        return
    for linea in salida.rstrip().splitlines():
        print(f"[placas:{placa}] {linea}", flush=True)


def _kill_tree(proc):
    """Mata el proceso y todos sus descendientes (Chrome zombie incluido)."""
    try:
        if _IS_WIN:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.killpg(os.getpgid(proc.pid), 9)
    except Exception:
        pass
    try:
        proc.wait(timeout=10)
    except Exception:
        pass


def _leer_resultado(placa, outdir, incluir_imagen):
    """Arma el dict de respuesta leyendo los archivos que dejó el worker."""
    placa = placa.upper()
    json_path = os.path.join(outdir, f"{placa}.json")
    png_path = os.path.join(outdir, f"{placa}.png")

    meta = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, encoding="utf-8") as fh:
                meta = json.load(fh)
        except Exception:
            meta = {}

    resultado = {
        "placa": placa,
        "ok": True,
        "cod": meta.get("cod"),
        "mensaje": meta.get("mensaje"),
        "sedes": meta.get("sedes"),
    }
    if incluir_imagen and os.path.exists(png_path):
        with open(png_path, "rb") as fh:
            resultado["imagen_base64"] = base64.b64encode(fh.read()).decode("ascii")
    return resultado


def consultar(placa, incluir_imagen=True):
    """Consulta una placa con reintentos. Devuelve un dict con 'status_hint':

        ok        -> consulta exitosa (incluye imagen_base64 si incluir_imagen)
        not_found -> placa no encontrada / sin foto (worker exit 2)
        timeout   -> se agotaron los reintentos por timeout
        error     -> error inesperado del worker (exit 3) / posible bloqueo Cloudflare
    """
    placa = placa.strip().upper()
    outdir = tempfile.mkdtemp(prefix="placa_")
    ultimo = {"placa": placa, "ok": False, "status_hint": "error",
              "mensaje": "No se pudo completar la consulta."}
    try:
        for intento in range(config.RETRIES + 1):
            print(f"[placas:{placa}] intento {intento + 1}/{config.RETRIES + 1}", flush=True)
            proc = _spawn(placa, outdir)
            try:
                salida, _ = proc.communicate(timeout=config.TIMEOUT)
                code = proc.returncode
                _log(placa, salida)
            except subprocess.TimeoutExpired:
                _kill_tree(proc)
                try:
                    salida, _ = proc.communicate(timeout=10)
                    _log(placa, salida)
                except Exception:
                    pass
                print(f"[placas:{placa}] TIMEOUT {config.TIMEOUT}s", flush=True)
                ultimo = {"placa": placa, "ok": False, "status_hint": "timeout",
                          "mensaje": f"Timeout de {config.TIMEOUT}s en la consulta."}
                time.sleep(2)
                continue

            if code == 0:
                res = _leer_resultado(placa, outdir, incluir_imagen)
                res["status_hint"] = "ok"
                res["intentos"] = intento + 1
                return res

            if code == 2:
                res = _leer_resultado(placa, outdir, incluir_imagen=False)
                res["ok"] = False
                res["status_hint"] = "not_found"
                res["mensaje"] = res.get("mensaje") or "Placa no encontrada en SUNARP."
                ultimo = res
                # Un 'no encontrado' no se reintenta: es respuesta válida del sitio.
                return ultimo

            # code == 3 u otro: error inesperado -> reintentar.
            ultimo = {"placa": placa, "ok": False, "status_hint": "error",
                      "mensaje": "Error en el worker (posible bloqueo de Cloudflare)."}
            time.sleep(2)

        return ultimo
    finally:
        shutil.rmtree(outdir, ignore_errors=True)
