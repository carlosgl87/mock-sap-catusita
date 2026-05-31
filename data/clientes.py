"""Lógica de clientes: perfil, crédito, cobranzas y documentos."""
from datetime import date

from data import seed


def get_cliente(ruc: str):
    return seed.CLIENTES_POR_RUC.get(ruc)


def get_perfil(ruc: str):
    cliente = get_cliente(ruc)
    if not cliente:
        return None
    vendedor = seed.VENDEDORES_POR_ID.get(cliente["vendedor_id"])
    return {
        "ruc": cliente["ruc"],
        "razon_social": cliente["razon_social"],
        "tipo": cliente["tipo"],
        "direccion": cliente["direccion"],
        "telefono": cliente["telefono"],
        "email": cliente["email"],
        "vendedor_id": cliente["vendedor_id"],
        "vendedor_nombre": vendedor["nombre"] if vendedor else None,
        "limite_credito": float(cliente["limite_credito"]),
        "dias_credito": cliente["dias_credito"],
        "estado": cliente["estado"],
        "fecha_registro": cliente["fecha_registro"],
    }


def _letras_pendientes(ruc):
    """Letras que representan deuda viva (pendientes + vencidas)."""
    return [l for l in seed.LETRAS_POR_RUC.get(ruc, [])
            if l["estado"] in ("pendiente", "vencida")]


def get_credito(ruc: str):
    cliente = get_cliente(ruc)
    if not cliente:
        return None

    letras = _letras_pendientes(ruc)
    saldo_usado = round(sum(l["monto"] for l in letras), 2)
    limite = float(cliente["limite_credito"])
    saldo_disponible = round(limite - saldo_usado, 2)
    porcentaje_usado = round(saldo_usado / limite * 100, 1) if limite else 0.0

    hoy = date.today()
    estado_credito = "al_dia"
    if any(l["estado"] == "vencida" for l in letras):
        estado_credito = "vencido"
    else:
        for l in letras:
            dias = (date.fromisoformat(l["fecha_vencimiento"]) - hoy).days
            if 0 <= dias < 7:
                estado_credito = "por_vencer"
                break

    return {
        "cliente_ruc": ruc,
        "razon_social": cliente["razon_social"],
        "limite_credito": limite,
        "saldo_usado": saldo_usado,
        "saldo_disponible": saldo_disponible,
        "porcentaje_usado": porcentaje_usado,
        "dias_credito": cliente["dias_credito"],
        "estado_credito": estado_credito,
        "moneda": "PEN",
    }


def get_cobranzas(ruc: str, estado: str = None):
    cliente = get_cliente(ruc)
    if not cliente:
        return None

    letras = list(seed.LETRAS_POR_RUC.get(ruc, []))

    deuda_vencida = round(sum(l["monto"] for l in letras
                              if l["estado"] == "vencida"), 2)
    deuda_por_vencer = round(sum(l["monto"] for l in letras
                                 if l["estado"] == "pendiente"), 2)
    total_deuda = round(deuda_vencida + deuda_por_vencer, 2)

    if estado:
        letras = [l for l in letras if l["estado"] == estado]

    return {
        "cliente_ruc": ruc,
        "total_deuda": total_deuda,
        "deuda_vencida": deuda_vencida,
        "deuda_por_vencer": deuda_por_vencer,
        "letras": letras,
    }


def get_documentos(ruc: str, tipo: str = None):
    cliente = get_cliente(ruc)
    if not cliente:
        return None

    documentos = []
    for p in seed.PEDIDOS_POR_RUC.get(ruc, []):
        estado_factura = "pagada" if p["estado"] == "entregado" else "pendiente"
        if tipo in (None, "factura"):
            documentos.append({
                "tipo": "factura",
                "numero": p["numero_factura"],
                "pedido_id": p["pedido_id"],
                "fecha": p["fecha_pedido"],
                "monto": p["total"],
                "estado": estado_factura,
            })
        if tipo in (None, "guia"):
            documentos.append({
                "tipo": "guia",
                "numero": p["numero_guia"],
                "pedido_id": p["pedido_id"],
                "fecha": p["fecha_pedido"],
                "monto": p["total"],
                "estado": "emitida",
            })

    documentos.sort(key=lambda d: d["fecha"], reverse=True)
    return {"cliente_ruc": ruc, "documentos": documentos}
