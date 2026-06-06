# Módulo `placas` — Consulta Vehicular SUNARP

API que consulta la [Consulta Vehicular SUNARP](https://consultavehicular.sunarp.gob.pe)
por placa y devuelve la **foto del vehículo** en base64. Vive aislado en esta carpeta y se
monta en `main.py` con un solo `app.include_router`.

## Cómo funciona (contenedor / worker efímero)

El sitio protege la consulta con **Cloudflare Turnstile**, que solo se resuelve con un
navegador real no detectado + un **click real del SO** (SeleniumBase UC `uc_gui_click_captcha`).
Por eso cada consulta corre en un **worker efímero**:

```
GET /placas/{placa}
  → service.consultar(): subprocess  python -m placas.worker PLACA   (Chrome propio)
       · timeout → mata todo el árbol de procesos (Chrome zombie incluido)
       · escribe <PLACA>.png + <PLACA>.json en una carpeta temporal
  → lee los archivos, los pasa a base64, borra la carpeta temporal
  → 200 { placa, ok, cod, mensaje, sedes, imagen_base64 }
```

> En el proyecto original cada consulta era un **contenedor Docker** (`docker run --rm`).
> Railway corre un único contenedor sin Docker-in-Docker, así que aquí el aislamiento es
> por **subproceso efímero** dentro del contenedor de Railway: mismo Chrome-limpio-por-consulta.

## Endpoints

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/placas/status` | — | Reporta si el entorno está listo (no scrapea) |
| GET | `/placas/{placa}` | `X-API-Key` | Consulta la placa y devuelve JSON + imagen base64 |

`/placas/{placa}` acepta `?imagen=false` para devolver solo metadata (sin el base64).

**Respuesta OK (200):**
```json
{ "placa": "F9N562", "ok": true, "cod": "0", "mensaje": "...",
  "sedes": [...], "imagen_base64": "iVBORw0KGgo...", "intentos": 1 }
```

**Errores:** `404` placa no encontrada · `504` timeout agotados los reintentos ·
`502` error/bloqueo de Cloudflare · `503` entorno no listo (sin Chrome/Xvfb).

## Variables de entorno

| Var | Default | Qué hace |
|-----|---------|----------|
| `PLACAS_TIMEOUT` | `150` | Segundos máx por consulta antes de matar el worker |
| `PLACAS_RETRIES` | `2` | Reintentos por placa |

## Probar local (Windows, IP residencial — camino realista)

```powershell
pip install -r requirements.txt          # Chrome ya está en Windows; Xvfb no hace falta
uvicorn main:app --reload
# en otra terminal:
curl -H "X-API-Key: catusita-mock-key-2024" http://localhost:8000/placas/F9N562
```

## La IP y el cuelgue de carga

Cloudflare valida el token del Turnstile junto con la reputación de la IP. En las pruebas,
**la IP de datacenter de Railway SÍ resolvió el Turnstile** y devolvió la foto (KIA PICANTO,
placa F9N562) — sin proxy. No está garantizado para siempre (la reputación de IP puede
cambiar); si algún día Cloudflare bloquea, el endpoint responde `502`/`504` limpio.

**El bug real que había no era la IP, sino Selenium colgándose en `driver.get()`** esperando
que la página terminara de cargar (un recurso nunca completaba; el timeout por defecto es
300s). El arreglo: `PLACAS_PAGE_TIMEOUT` (default 35s) capea la carga y el worker continúa
igual — el DOM ya está usable. Sin esto, cada consulta se colgaba ~150s.

| Var extra | Default | Qué hace |
|-----------|---------|----------|
| `PLACAS_PAGE_TIMEOUT` | `35` | Segundos máx esperando la carga de la página antes de seguir |

## Notas

- Las consultas se **serializan** (un lock): el click real usa un único mouse/display.
- En Railway/Docker el `DISPLAY` lo provee un **Xvfb** que arranca `entrypoint.sh`; por eso
  el build pasó de nixpacks a **Dockerfile** (Chrome + Xvfb + la app).
- `--shm-size=2g` recomendado al correr el contenedor (evita crashes de Chrome).
