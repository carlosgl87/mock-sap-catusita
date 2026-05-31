"""Lógica de pedidos: listado por cliente e historial de compras."""
from collections import Counter
from datetime import date, timedelta

from data import seed


def get_pedidos(cliente_ruc: str, estado: str = None, limite: int = None):
    if cliente_ruc not in seed.CLIENTES_POR_RUC:
        return None

    pedidos = list(seed.PEDIDOS_POR_RUC.get(cliente_ruc, []))
    pedidos.sort(key=lambda p: p["fecha_pedido"], reverse=True)

    if estado:
        pedidos = [p for p in pedidos if p["estado"] == estado]
    if limite:
        pedidos = pedidos[:limite]

    return {
        "cliente_ruc": cliente_ruc,
        "total_pedidos": len(pedidos),
        "pedidos": pedidos,
    }


def get_historial(cliente_ruc: str, meses: int = 18):
    if cliente_ruc not in seed.CLIENTES_POR_RUC:
        return None

    corte = date.today() - timedelta(days=int(30.44 * meses))
    pedidos = [
        p for p in seed.PEDIDOS_POR_RUC.get(cliente_ruc, [])
        if date.fromisoformat(p["fecha_pedido"]) >= corte
        and p["estado"] != "anulado"
    ]
    pedidos.sort(key=lambda p: p["fecha_pedido"], reverse=True)

    monto_total = round(sum(p["total"] for p in pedidos), 2)
    promedio_mensual = round(monto_total / meses, 2) if meses else 0.0

    # Producto más comprado por cantidad acumulada.
    contador = Counter()
    for p in pedidos:
        for item in p["items"]:
            contador[item["nombre"]] += item["cantidad"]
    producto_mas_comprado = contador.most_common(1)[0][0] if contador else None

    resumen = [
        {
            "pedido_id": p["pedido_id"],
            "fecha_pedido": p["fecha_pedido"],
            "estado": p["estado"],
            "total": p["total"],
        }
        for p in pedidos
    ]

    return {
        "cliente_ruc": cliente_ruc,
        "periodo_meses": meses,
        "total_compras": len(pedidos),
        "monto_total": monto_total,
        "promedio_mensual": promedio_mensual,
        "producto_mas_comprado": producto_mas_comprado,
        "pedidos": resumen,
    }
