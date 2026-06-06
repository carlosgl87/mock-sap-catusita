# Imagen del Mock SAP Catusita + módulo de placas (Chrome + Xvfb + FastAPI).
# Se cambió de nixpacks a Dockerfile porque la consulta SUNARP necesita un Chrome
# real bajo pantalla virtual (Xvfb) para resolver el Cloudflare Turnstile.
# OJO: Chrome no tiene build oficial ARM -> usar host/Railway amd64.
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# Dependencias del sistema:
#  - runtime de Chrome (libnss3, libgbm1, libgtk-3-0, etc.)
#  - xvfb: pantalla virtual (necesaria para el click real del Turnstile)
#  - scrot + python3-tk + python3-xlib: requeridos por pyautogui en Linux
RUN apt-get update && apt-get install -y --no-install-recommends \
        wget gnupg ca-certificates \
        xvfb xauth scrot python3-tk python3-dev x11-utils \
        fonts-liberation libnss3 libxss1 libasound2 \
        libatk-bridge2.0-0 libatk1.0-0 libcups2 libdrm2 \
        libgtk-3-0 libgbm1 libx11-xcb1 libxcomposite1 libxdamage1 \
        libxrandr2 libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/*

# Google Chrome stable
RUN wget -q -O /tmp/chrome.deb \
        https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends /tmp/chrome.deb \
    && rm -f /tmp/chrome.deb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencias Python (incluye fastapi, uvicorn, seleniumbase, pyautogui)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Pre-descargar el uc_driver que coincide con el Chrome instalado
# (evita descargarlo en la primera consulta)
RUN seleniumbase get uc_driver || seleniumbase get chromedriver || true

# Código de la app
COPY . /app
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# entrypoint arranca Xvfb (pantalla virtual) y luego uvicorn.
ENTRYPOINT ["/app/entrypoint.sh"]
