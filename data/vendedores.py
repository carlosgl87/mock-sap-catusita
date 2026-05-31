"""Lógica de vendedores y su cartera de clientes."""
from datetime import date

from data import seed


def get_vendedor(vendedor_id: str):
    return seed.VENDEDORES_POR_ID.get(vendedor_id)


def _saldo_pendiente(ruc):
    return round(sum(l["monto"] for l in seed.LETRAS_POR_RUC.get(ruc, [])
                     if l["estado"] in ("pendiente", "vencida")), 2)


def _ultimo_pedido(ruc):
    pedidos = seed.PEDIDOS_POR_RUC.get(ruc, [])
    if not pedidos:
        return None, None
    ultimo = max(pedidos, key=lambda p: p["fecha_pedido"])
    return ultimo["fecha_pedido"], ultimo["total"]


def get_cartera(vendedor_id: str, estado: str = None, tipo: str = None):
    vendedor = get_vendedor(vendedor_id)
    if not vendedor:
        return None

    clientes = list(seed.CLIENTES_POR_VENDEDOR.get(vendedor_id, []))
    if estado:
        clientes = [c for c in clientes if c["estado"] == estado]
    if tipo:
        clientes = [c for c in clientes if c["tipo"] == tipo]

    cartera = []
    for c in clientes:
        # El distrito es la última parte de la dirección.
        distrito = c["direccion"].split(",")[-1].strip()
        fecha_ult, monto_ult = _ultimo_pedido(c["ruc"])
        cartera.append({
            "ruc": c["ruc"],
            "razon_social": c["razon_social"],
            "tipo": c["tipo"],
            "distrito": distrito,
            "telefono": c["telefono"],
            "estado": c["estado"],
            "limite_credito": float(c["limite_credito"]),
            "saldo_pendiente": _saldo_pendiente(c["ruc"]),
            "ultimo_pedido": fecha_ult,
            "monto_ultimo_pedido": monto_ult,
        })

    return {
        "vendedor_id": vendedor["vendedor_id"],
        "vendedor_nombre": vendedor["nombre"],
        "zona": vendedor["zona"],
        "total_clientes": len(cartera),
        "clientes": cartera,
    }
