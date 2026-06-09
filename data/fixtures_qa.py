"""Datos ancla deterministas para el QA del Agente Vendedores (Catu).

Se inyectan DESPUÉS de la generación Faker de `seed.py` para garantizar, con
identificadores fijos y memorables, todos los escenarios que exigen QA_agente.md,
plan_de_prueba.md y la validación de cartera de plan_de_implementacion.md.

Reglas de diseño:
- IDs fijos y memorables (RUC 201000000xx propios de V001, 209000000xx ajeno en V002).
- Fechas RELATIVAS a hoy: las letras "por vencer esta semana" / "vencida" se cumplen
  cualquier día que se ejecute el QA.
- No se toca la data Faker existente; estas fixtures se SUMAN.
- aplicar() es idempotente (se puede llamar varias veces sin duplicar).

Ver mapeo fixture -> caso de prueba en plan_de_datos.md (sección 6).
"""
from datetime import date, timedelta

HOY = date.today()


def _d(dias: int) -> str:
    """Fecha ISO relativa a hoy (dias negativos = pasado)."""
    return (HOY + timedelta(days=dias)).isoformat()


# ===========================================================================
# 1. Clientes ancla
# ===========================================================================
# 3 clientes de V001 (cartera propia) + 1 de V002 (ajeno, para el rechazo).
CLIENTES_QA = [
    {
        "ruc": "20100000001",
        "razon_social": "Transportes Andinos SAC",   # nombrado en QA_agente.md
        "tipo": "distribuidor",
        "direccion": "Av. Industrial 100, Ate",
        "telefono": "+511 900000001",
        "email": "contacto@transportesandinos.pe",
        "vendedor_id": "V001",
        "limite_credito": 50000,
        "dias_credito": 30,
        "estado": "activo",
        "fecha_registro": _d(-900),
    },
    {
        "ruc": "20100000002",
        "razon_social": "Taller Mecánico Aguilar SAC",
        "tipo": "taller",
        "direccion": "Jr. Los Mecánicos 250, San Juan de Lurigancho",
        "telefono": "+511 900000002",
        "email": "ventas@talleraguilar.pe",
        "vendedor_id": "V001",
        "limite_credito": 30000,
        "dias_credito": 30,
        "estado": "activo",
        "fecha_registro": _d(-700),
    },
    {
        "ruc": "20100000003",
        "razon_social": "Distribuidora Repuestos Lima SAC",
        "tipo": "distribuidor",
        "direccion": "Av. Argentina 1500, Callao",
        "telefono": "+511 900000003",
        "email": "compras@repuestoslima.pe",
        "vendedor_id": "V001",
        "limite_credito": 80000,
        "dias_credito": 45,
        "estado": "activo",
        "fecha_registro": _d(-1100),
    },
    {
        "ruc": "20900000009",
        "razon_social": "Importadora del Sur SAC",
        "tipo": "distribuidor",
        "direccion": "Av. Tacna 800, Cercado de Lima",
        "telefono": "+511 900000009",
        "email": "info@importadorasur.pe",
        "vendedor_id": "V002",          # <-- AJENO a V001 (cartera de V002)
        "limite_credito": 60000,
        "dias_credito": 60,
        "estado": "activo",
        "fecha_registro": _d(-800),
    },
]


# ===========================================================================
# 2. Productos ancla
# ===========================================================================
# Incluye un filtro Fram (el QA lo pide y "Fram" no está en las marcas Faker),
# un producto con stock conocido y uno AGOTADO (stock = 0). Campo `oem` para SP-5.
PRODUCTOS_QA = [
    {
        "sku": "FIL-FRA-0001",
        "nombre": "Filtro de aceite Fram",
        "categoria": "filtros",
        "marca": "Fram",
        "precio_lista": 45.0,
        "precio_neto": 32.0,
        "stock": 120,
        "stock_minimo": 10,
        "unidad": "UND",
        "compatibilidad": ["Toyota"],
        "oem": ["90915-YZZD2", "FRM-OIL-77"],
    },
    {
        "sku": "FIL-BOC-0001",
        "nombre": "Filtro de aceite Bosch",
        "categoria": "filtros",
        "marca": "Bosch",
        "precio_lista": 38.0,
        "precio_neto": 27.0,
        "stock": 85,
        "stock_minimo": 10,
        "unidad": "UND",
        "compatibilidad": ["Toyota", "Nissan"],
        "oem": ["90915-10001"],
    },
    {
        "sku": "FRE-BEN-0001",
        "nombre": "Pastilla de freno Bendix",
        "categoria": "frenos",
        "marca": "Bendix",
        "precio_lista": 180.0,
        "precio_neto": 130.0,
        "stock": 0,                      # <-- AGOTADO
        "stock_minimo": 8,
        "unidad": "UND",
        "compatibilidad": ["Toyota", "Hyundai"],
        "oem": [],
    },
]


# ===========================================================================
# 3. Vehículo ancla (Toyota Hilux, placa fija)
# ===========================================================================
VEHICULOS_QA = [
    {
        "placa": "ABC-123",
        "vin": "1HGBH41JXMN109186",       # 17 caracteres
        "marca": "Toyota",
        "modelo": "Hilux",
        "año": 2019,
        "motor": "2.4L",
        "propietario_ruc": "20100000001",  # Transportes Andinos SAC
    },
]


# ===========================================================================
# 4. Pedidos ancla (de Transportes Andinos SAC) — >= 5, con factura y guía
# ===========================================================================
def _item(sku, nombre, cantidad, precio):
    return {
        "sku": sku,
        "nombre": nombre,
        "cantidad": cantidad,
        "precio_unitario": precio,
        "subtotal": round(cantidad * precio, 2),
    }


def _pedido(pedido_id, dias_atras, estado, items, factura, guia):
    fecha = HOY - timedelta(days=dias_atras)
    estimada = fecha + timedelta(days=5)
    real = (estimada + timedelta(days=1)).isoformat() if estado == "entregado" else None
    subtotal = round(sum(i["subtotal"] for i in items), 2)
    igv = round(subtotal * 0.18, 2)
    total = round(subtotal + igv, 2)
    return {
        "pedido_id": pedido_id,
        "cliente_ruc": "20100000001",
        "fecha_pedido": fecha.isoformat(),
        "fecha_entrega_estimada": estimada.isoformat(),
        "fecha_entrega_real": real,
        "estado": estado,
        "transportista": "Olva Courier",
        "items": items,
        "subtotal": subtotal,
        "igv": igv,
        "total": total,
        "numero_factura": factura,
        "numero_guia": guia,
    }


PEDIDOS_QA = [
    _pedido("PED-000001", 30, "entregado",
            [_item("FIL-BOC-0001", "Filtro de aceite Bosch", 10, 38.0),
             _item("FIL-FRA-0001", "Filtro de aceite Fram", 5, 45.0)],
            "F001-000001", "T001-000001"),
    _pedido("PED-000002", 5, "en_transito",
            [_item("FRE-BEN-0001", "Pastilla de freno Bendix", 4, 180.0)],
            "F001-000002", "T001-000002"),
    _pedido("PED-000003", 60, "entregado",
            [_item("FIL-BOC-0001", "Filtro de aceite Bosch", 20, 38.0)],
            "F001-000003", "T001-000003"),
    _pedido("PED-000004", 3, "en_almacen",
            [_item("FIL-FRA-0001", "Filtro de aceite Fram", 8, 45.0)],
            "F001-000004", "T001-000004"),
    _pedido("PED-000005", 90, "entregado",
            [_item("FRE-BEN-0001", "Pastilla de freno Bendix", 6, 180.0),
             _item("FIL-BOC-0001", "Filtro de aceite Bosch", 12, 38.0)],
            "F001-000005", "T001-000005"),
]


# ===========================================================================
# 5. Letras / cobranzas ancla (fechas relativas a hoy)
# ===========================================================================
# Transportes Andinos (A): una VENCIDA + una por vencer en el futuro
#   -> CC-1 (disponible), CC-3 (saldo), CC-4 (deuda vencida = sí), estado "vencido".
# Taller Aguilar (B): una pendiente que vence ESTA SEMANA -> CC-2.
# Distribuidora Lima (C): sin letras -> cliente "al día".
LETRAS_QA = [
    {
        "letra_id": "LET-000001",
        "cliente_ruc": "20100000001",
        "pedido_id": "PED-000001",
        "monto": 5000.0,
        "fecha_emision": _d(-42),
        "fecha_vencimiento": _d(-12),     # vencida
        "estado": "vencida",
        "dias_mora": 12,
    },
    {
        "letra_id": "LET-000002",
        "cliente_ruc": "20100000001",
        "pedido_id": "PED-000003",
        "monto": 6000.0,
        "fecha_emision": _d(-20),
        "fecha_vencimiento": _d(40),      # futura
        "estado": "pendiente",
        "dias_mora": 0,
    },
    {
        "letra_id": "LET-000003",
        "cliente_ruc": "20100000002",
        "pedido_id": None,
        "monto": 3200.0,
        "fecha_emision": _d(-23),
        "fecha_vencimiento": _d(3),       # vence esta semana
        "estado": "pendiente",
        "dias_mora": 0,
    },
]


# ===========================================================================
# Inyección en los índices de seed (idempotente)
# ===========================================================================
_APLICADO = False


def aplicar():
    """Agrega las fixtures a las listas e índices de seed. Llamar UNA vez,
    después de que seed.py haya generado la data Faker y armado sus índices."""
    global _APLICADO
    if _APLICADO:
        return
    from data import seed

    # --- Clientes ---
    for c in CLIENTES_QA:
        if c["ruc"] in seed.CLIENTES_POR_RUC:
            continue
        seed.CLIENTES.append(c)
        seed.CLIENTES_POR_RUC[c["ruc"]] = c
        seed.CLIENTES_POR_VENDEDOR.setdefault(c["vendedor_id"], []).append(c)

    # --- Productos ---
    for p in PRODUCTOS_QA:
        if p["sku"] in seed.PRODUCTOS_POR_SKU:
            continue
        seed.PRODUCTOS.append(p)
        seed.PRODUCTOS_POR_SKU[p["sku"]] = p

    # --- Vehículos ---
    for v in VEHICULOS_QA:
        if v["placa"] in seed.VEHICULOS_POR_PLACA:
            continue
        seed.VEHICULOS.append(v)
        seed.VEHICULOS_POR_PLACA[v["placa"]] = v
        seed.VEHICULOS_POR_VIN[v["vin"]] = v

    # --- Pedidos ---
    ids_existentes = {p["pedido_id"] for p in seed.PEDIDOS}
    for ped in PEDIDOS_QA:
        if ped["pedido_id"] in ids_existentes:
            continue
        seed.PEDIDOS.append(ped)
        seed.PEDIDOS_POR_RUC.setdefault(ped["cliente_ruc"], []).append(ped)

    # --- Letras ---
    ids_letras = {l["letra_id"] for l in seed.LETRAS}
    for let in LETRAS_QA:
        if let["letra_id"] in ids_letras:
            continue
        seed.LETRAS.append(let)
        seed.LETRAS_POR_RUC.setdefault(let["cliente_ruc"], []).append(let)

    _APLICADO = True
