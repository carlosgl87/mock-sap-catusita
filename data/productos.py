"""Lógica de productos: stock, precios, catálogo y lookup de vehículos."""
import unicodedata

from data import seed


def _normalizar(texto: str) -> str:
    """Minúsculas y sin acentos para búsquedas case-insensitive."""
    if texto is None:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    sin_acentos = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sin_acentos.lower().strip()


def get_producto(sku: str):
    return seed.PRODUCTOS_POR_SKU.get(sku)


def get_stock(sku: str):
    prod = get_producto(sku)
    if not prod:
        return None
    return {
        "sku": prod["sku"],
        "nombre": prod["nombre"],
        "stock": prod["stock"],
        "stock_minimo": prod["stock_minimo"],
        "disponible": prod["stock"] > 0,
        "alerta_stock_bajo": prod["stock"] <= prod["stock_minimo"],
        "unidad": prod["unidad"],
    }


def get_precio(sku: str, tipo: str = None):
    prod = get_producto(sku)
    if not prod:
        return None
    precio_lista = prod["precio_lista"]
    precio_neto = prod["precio_neto"]
    descuento = round((1 - precio_neto / precio_lista) * 100, 1) \
        if precio_lista else 0.0

    if tipo == "neto":
        return {"sku": prod["sku"], "nombre": prod["nombre"],
                "precio_neto": precio_neto, "moneda": "PEN"}
    if tipo == "lista":
        return {"sku": prod["sku"], "nombre": prod["nombre"],
                "precio_lista": precio_lista, "moneda": "PEN"}

    return {
        "sku": prod["sku"],
        "nombre": prod["nombre"],
        "precio_lista": precio_lista,
        "precio_neto": precio_neto,
        "descuento_porcentaje": descuento,
        "igv_incluido": True,
        "moneda": "PEN",
    }


def buscar_catalogo(q: str = None, categoria: str = None,
                    marca: str = None, con_stock: bool = False):
    resultados = seed.PRODUCTOS

    if q:
        q_norm = _normalizar(q)
        terminos = q_norm.split()
        resultados = [
            p for p in resultados
            if all(t in _normalizar(p["nombre"]) or t in _normalizar(p["categoria"])
                   or any(t in _normalizar(o) for o in p.get("oem", []))
                   for t in terminos)
        ]

    if categoria:
        cat_norm = _normalizar(categoria)
        resultados = [p for p in resultados
                      if _normalizar(p["categoria"]) == cat_norm]

    if marca:
        marca_norm = _normalizar(marca)
        resultados = [p for p in resultados
                      if _normalizar(p["marca"]) == marca_norm]

    if con_stock:
        resultados = [p for p in resultados if p["stock"] > 0]

    return {"total": len(resultados), "productos": resultados}


def buscar_vehiculo(placa_o_vin: str):
    """Detecta placa (ABC-123) o VIN (17 caracteres) y devuelve el vehículo."""
    import re

    valor = placa_o_vin.strip().upper()
    veh = None
    if re.match(r"^[A-Z]{3}-\d{3}$", valor):
        veh = seed.VEHICULOS_POR_PLACA.get(valor)
    elif len(valor) == 17:
        veh = seed.VEHICULOS_POR_VIN.get(valor)

    if not veh:
        return None

    propietario = seed.CLIENTES_POR_RUC.get(veh["propietario_ruc"])
    propietario_nombre = propietario["razon_social"] if propietario else None

    # 3-5 repuestos compatibles con la marca del vehículo, del stock existente.
    compatibles = [p for p in seed.PRODUCTOS
                   if veh["marca"] in p["compatibilidad"]]
    repuestos = [
        {"sku": p["sku"], "nombre": p["nombre"], "stock": p["stock"]}
        for p in compatibles[:5]
    ]

    return {
        "placa": veh["placa"],
        "vin": veh["vin"],
        "marca": veh["marca"],
        "modelo": veh["modelo"],
        "año": veh["año"],
        "motor": veh["motor"],
        "propietario_ruc": veh["propietario_ruc"],
        "propietario_nombre": propietario_nombre,
        "repuestos_compatibles": repuestos,
    }
