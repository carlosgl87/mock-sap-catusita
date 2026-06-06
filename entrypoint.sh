#!/bin/bash
# Arranca una pantalla virtual X (Xvfb) y luego el servidor FastAPI.
# El click real del Turnstile (pyautogui) necesita un DISPLAY; en contenedor lo
# damos con Xvfb :99. Más fiable que `xvfb-run` (que tiende a colgarse).
set -e

rm -f /tmp/.X99-lock 2>/dev/null || true
Xvfb :99 -screen 0 1920x1080x24 -ac -nolisten tcp >/tmp/xvfb.log 2>&1 &
export DISPLAY=:99

# esperar a que el display esté listo
for i in $(seq 1 30); do
    if xdpyinfo -display :99 >/dev/null 2>&1; then
        break
    fi
    sleep 0.3
done

exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
