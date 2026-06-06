"""Worker de UNA consulta SUNARP, pensado como subproceso efímero.

Resuelve el Cloudflare Turnstile con SeleniumBase UC (click real del SO) y guarda
la foto del vehículo en <OUTDIR>/<PLACA>.png + <OUTDIR>/<PLACA>.json.

En Linux (Railway/Docker) el DISPLAY lo provee un Xvfb arrancado por entrypoint.sh,
por eso headless=False. En Windows local usa el display real, sin Xvfb.

NO usa proxy: sale por la IP de la máquina/contenedor que lo ejecuta.

Uso:
    python -m placas.worker F9N562
    PLACAS_OUTDIR=/tmp/xyz python -m placas.worker F9N562

Variables de entorno:
    PLACAS_OUTDIR   carpeta de salida (default: ./resultados)

Códigos de salida:
    0  OK, foto guardada
    2  placa no encontrada / no se capturó la respuesta de la API
    3  error inesperado
"""
import base64
import json
import os
import sys
import time

from seleniumbase import SB

URL = "https://consultavehicular.sunarp.gob.pe/consulta-vehicular/inicio"
API_PATH = "getDatosVehiculo"
OUTDIR = os.environ.get("PLACAS_OUTDIR", os.path.join(os.getcwd(), "resultados"))

# JS que engancha fetch + XHR para capturar la respuesta de la consulta.
HOOK = r"""
window.__caps = window.__caps || [];
if (!window.__hooked) {
  window.__hooked = true;
  const of = window.fetch;
  window.fetch = async function(...a) {
    const r = await of.apply(this, a);
    try {
      const url = (a[0] && a[0].url) ? a[0].url : a[0];
      const c = r.clone(); const t = await c.text();
      window.__caps.push({type:'fetch', url:String(url), status:r.status, body:t});
    } catch(e) {}
    return r;
  };
  const oOpen = XMLHttpRequest.prototype.open;
  const oSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function(m,u){ this.__u=u; return oOpen.apply(this,arguments); };
  XMLHttpRequest.prototype.send = function(b){
    const self=this;
    this.addEventListener('load', function(){
      try { window.__caps.push({type:'xhr', url:String(self.__u), status:self.status, body:self.responseText}); } catch(e){}
    });
    return oSend.apply(this, arguments);
  };
}
return 'hooked';
"""


def _log(msg):
    print(f"[worker] {msg}", flush=True)


def run(placa):
    placa = placa.strip().upper()
    _log(f"START placa={placa} DISPLAY={os.environ.get('DISPLAY')!r}")

    # --no-sandbox es obligatorio corriendo como root en contenedor.
    _log("abriendo Chrome (SB uc)...")
    with SB(uc=True, headless=False, locale="es",
            chromium_arg="--no-sandbox,--disable-dev-shm-usage") as sb:
        _log("Chrome abierto; navegando a SUNARP...")
        sb.uc_open_with_reconnect(URL, reconnect_time=5)
        _log("pagina cargada")
        time.sleep(2)
        sb.execute_script(HOOK)

        _log("escribiendo placa...")
        sb.type("#nroPlaca", placa)

        _log("resolviendo Turnstile (click real)...")
        sb.uc_gui_click_captcha()          # click real del SO sobre el Turnstile
        time.sleep(3)
        sb.execute_script(HOOK)            # reinstalar por si el reconnect lo reseteó

        token = sb.execute_script(
            "var e=document.querySelector('[name=cf-turnstile-response]');return e?e.value:''"
        )
        print(f"[worker] token turnstile: {len(token or '')} chars", flush=True)
        if not token:
            sb.uc_gui_click_captcha()
            time.sleep(3)

        # Enviar la búsqueda (botón Angular sin type=submit).
        for sel in ("button.btn-sunarp-green", "button.ant-btn-primary",
                    "//button[contains(.,'Realizar')]"):
            try:
                sb.click(sel)
                break
            except Exception:
                continue

        # Esperar la respuesta de la API.
        data = None
        for _ in range(20):
            time.sleep(1)
            caps = sb.execute_script("return window.__caps || []")
            for c in caps:
                if API_PATH in str(c.get("url", "")):
                    try:
                        data = json.loads(c["body"])
                    except Exception:
                        pass
                    break
            if data is not None:
                break

        os.makedirs(OUTDIR, exist_ok=True)

        if data is None:
            print("[worker] no se capturó getDatosVehiculo", flush=True)
            try:
                sb.save_screenshot(os.path.join(OUTDIR, f"{placa}_error.png"))
            except Exception:
                pass
            return 2

        model = data.get("model") or {}
        imagen_b64 = model.get("imagen")

        # Guardar metadata (sin la imagen gigante) siempre que haya respuesta.
        meta = {k: v for k, v in data.items() if k != "model"}
        meta["sedes"] = model.get("sedes")
        with open(os.path.join(OUTDIR, f"{placa}.json"), "w", encoding="utf-8") as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=2)

        if imagen_b64:
            with open(os.path.join(OUTDIR, f"{placa}.png"), "wb") as fh:
                fh.write(base64.b64decode(imagen_b64))
            print(json.dumps({"placa": placa, "ok": True,
                              "cod": data.get("cod"),
                              "mensaje": data.get("mensaje")}, ensure_ascii=False), flush=True)
            return 0

        print(json.dumps({"placa": placa, "ok": False,
                          "cod": data.get("cod"),
                          "mensaje": data.get("mensaje")}, ensure_ascii=False), flush=True)
        return 2


if __name__ == "__main__":
    placa = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PLACA", "")
    if not placa:
        print("Falta la placa. Uso: python -m placas.worker PLACA", flush=True)
        sys.exit(3)
    try:
        sys.exit(run(placa))
    except Exception as e:
        print(f"[worker] ERROR: {e}", flush=True)
        sys.exit(3)
