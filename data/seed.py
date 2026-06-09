"""Generación de todos los datos del Mock SAP con Faker (semilla fija = 42).

Este módulo se importa UNA sola vez al arrancar FastAPI. Todos los datos se
generan en variables a nivel de módulo, por lo que persisten durante toda la
vida del proceso. No se usa base de datos ni archivos externos.
"""
from faker import Faker
from datetime import date, timedelta
import random

# ---------------------------------------------------------------------------
# Semilla fija — debe llamarse UNA sola vez, antes de generar cualquier dato.
# ---------------------------------------------------------------------------
# Locale peruano. Faker NO incluye "es_PE" en ninguna versión (la última,
# 40.19.1, solo trae es, es_AR, es_CA, es_CL, es_CO, es_ES, es_MX). Pedimos
# "es_PE" para que funcione automáticamente si algún día se agrega, y caemos a
# "es_MX" (español latinoamericano, lo más cercano al sabor peruano). Los datos
# típicamente peruanos (RUC, distritos, teléfonos +511, razones sociales
# SAC/EIRL) se generan de forma explícita más abajo, independientes del locale.
try:
    fake = Faker("es_PE")
except AttributeError:
    fake = Faker("es_MX")
Faker.seed(42)
random.seed(42)

HOY = date.today()


def _meses_atras(m: int) -> date:
    return HOY - timedelta(days=int(30.44 * m))


def _anios_atras(y: int) -> date:
    return HOY - timedelta(days=int(365.25 * y))


# ---------------------------------------------------------------------------
# Catálogos base
# ---------------------------------------------------------------------------
ZONAS = ["Norte Lima", "Sur Lima", "Centro Lima", "Este Lima",
         "Provincias Norte", "Provincias Sur"]

DISTRITOS = ["Los Olivos", "San Juan de Lurigancho", "Ate", "Villa El Salvador",
             "San Martín de Porres", "Comas", "Independencia", "El Agustino",
             "La Victoria", "Callao", "Surco", "Miraflores", "San Isidro",
             "Lince", "Breña"]

TIPOS_CLIENTE = ["taller", "distribuidor", "consumidor_final"]

SUFIJOS = ["SAC", "EIRL", "SRL", "E.I.R.L"]

MARCAS = ["ACDelco", "Monroe", "Bosch", "Gates", "NGK", "Mobil",
          "Castrol", "Moog", "Bendix", "Ferodo"]

MARCA_ABREV = {
    "ACDelco": "ACD", "Monroe": "MON", "Bosch": "BOC", "Gates": "GAT",
    "NGK": "NGK", "Mobil": "MOB", "Castrol": "CAS", "Moog": "MOG",
    "Bendix": "BEN", "Ferodo": "FER",
}

CATEGORIAS = {
    "filtros": {
        "abrev": "FIL",
        "plantillas": ["Filtro de aceite {marca}", "Filtro de aire {marca}",
                       "Filtro de combustible {marca}"],
    },
    "frenos": {
        "abrev": "FRE",
        "plantillas": ["Pastilla de freno {marca}", "Disco de freno {marca}",
                       "Zapata de freno {marca}"],
    },
    "motor": {
        "abrev": "MOT",
        "plantillas": ["Bujía {marca}", "Correa de distribución {marca}",
                       "Banda alternador {marca}"],
    },
    "suspension": {
        "abrev": "SUS",
        "plantillas": ["Amortiguador delantero {marca}",
                       "Espiral de suspensión {marca}", "Rótula {marca}"],
    },
    "electrico": {
        "abrev": "ELE",
        "plantillas": ["Batería {capacidad}Ah {marca}", "Alternador {marca}",
                       "Motor de arranque {marca}"],
    },
    "lubricantes": {
        "abrev": "LUB",
        "plantillas": ["Aceite de motor {viscosidad} {marca}",
                       "Líquido de frenos {marca}"],
    },
}

CAPACIDADES = [45, 55, 60, 75, 90, 100]
VISCOSIDADES = ["5W-30", "10W-40", "15W-40", "20W-50", "25W-60"]

MARCAS_VEHICULO = ["Toyota", "Hyundai", "Kia", "Nissan", "Chevrolet",
                   "Ford", "Volkswagen", "Suzuki"]

MODELOS = {
    "Toyota": ["Corolla", "Hilux", "RAV4", "Yaris", "Land Cruiser"],
    "Hyundai": ["Tucson", "Santa Fe", "Accent", "Elantra", "H-1"],
    "Kia": ["Sportage", "Sorento", "Rio", "Cerato", "Carnival"],
    "Nissan": ["Frontier", "X-Trail", "Sentra", "Versa", "Navara"],
    "Chevrolet": ["Tracker", "D-Max", "Sail", "Spark", "Captiva"],
    "Ford": ["Ranger", "Explorer", "F-150", "EcoSport", "Fusion"],
    "Volkswagen": ["Golf", "Tiguan", "Amarok", "Polo", "Touareg"],
    "Suzuki": ["Jimny", "Vitara", "Swift", "Grand Vitara", "S-Cross"],
}

TRANSPORTISTAS = ["Olva Courier", "Shalom", "Cruz del Sur", "Recojo en tienda"]
COMPAT_MARCAS = ["Toyota", "Hyundai", "Kia", "Nissan", "Chevrolet",
                 "Ford", "Volkswagen", "Suzuki"]

ESTADOS_PEDIDO = ["en_almacen", "en_transito", "entregado",
                  "con_incidencia", "anulado"]
PESOS_PEDIDO = [15, 15, 60, 7, 3]


# ===========================================================================
# 1. VENDEDORES (10)
# ===========================================================================
VENDEDORES = []
for i in range(10):
    vendedor_id = f"V{str(i + 1).zfill(3)}"
    VENDEDORES.append({
        "vendedor_id": vendedor_id,
        "nombre": fake.name(),
        "email": fake.email(),
        "telefono": f"+511 9{fake.numerify('########')}",
        "zona": random.choice(ZONAS),
        "fecha_ingreso": fake.date_between(start_date=_anios_atras(8),
                                           end_date=_anios_atras(1)).isoformat(),
    })


# ===========================================================================
# 2. CLIENTES (200, distribuidos 15-30 por vendedor)
# ===========================================================================
def _distribuir_clientes(total=200, n_vendedores=10, minimo=15, maximo=30):
    counts = [total // n_vendedores] * n_vendedores
    for _ in range(40):
        a = random.randint(0, n_vendedores - 1)
        b = random.randint(0, n_vendedores - 1)
        if counts[a] > minimo and counts[b] < maximo:
            counts[a] -= 1
            counts[b] += 1
    return counts


def _razon_social(tipo):
    apellido = fake.last_name()
    if tipo == "taller":
        return f"Taller Mecánico {apellido} {random.choice(SUFIJOS)}"
    if tipo == "distribuidor":
        prefijo = random.choice(["Distribuidora", "Repuestos"])
        return f"{prefijo} {apellido} {random.choice(SUFIJOS)}"
    return fake.name()  # consumidor_final: persona natural


CLIENTES = []
_counts = _distribuir_clientes()
for v_index, cantidad in enumerate(_counts):
    vendedor_id = VENDEDORES[v_index]["vendedor_id"]
    for _ in range(cantidad):
        tipo = random.choice(TIPOS_CLIENTE)
        # RUC: empresas empiezan en 20, personas naturales en 10.
        prefijo_ruc = "10" if tipo == "consumidor_final" else "20"
        CLIENTES.append({
            "ruc": prefijo_ruc + fake.numerify("#########"),
            "razon_social": _razon_social(tipo),
            "tipo": tipo,
            "direccion": f"{fake.street_name()} {fake.building_number()}, "
                         f"{random.choice(DISTRITOS)}",
            "telefono": f"+511 9{fake.numerify('########')}",
            "email": fake.company_email(),
            "vendedor_id": vendedor_id,
            "limite_credito": random.choice(
                [5000, 10000, 20000, 30000, 50000, 80000, 100000]),
            "dias_credito": random.choice([30, 45, 60, 90]),
            "estado": random.choices(
                ["activo", "suspendido", "bloqueado"], weights=[85, 10, 5])[0],
            "fecha_registro": fake.date_between(
                start_date=_anios_atras(5), end_date=_meses_atras(6)).isoformat(),
        })


# ===========================================================================
# 3. PRODUCTOS (150)
# ===========================================================================
PRODUCTOS = []
_skus_usados = set()
_cat_keys = list(CATEGORIAS.keys())
for _ in range(150):
    categoria = random.choice(_cat_keys)
    info = CATEGORIAS[categoria]
    plantilla = random.choice(info["plantillas"])
    marca = random.choice(MARCAS)
    nombre = plantilla.format(
        marca=marca,
        capacidad=random.choice(CAPACIDADES),
        viscosidad=random.choice(VISCOSIDADES),
    )
    # SKU único: CATEGORIA_ABREV-MARCA_ABREV-NUMERO_4_DIGITOS
    while True:
        sku = f"{info['abrev']}-{MARCA_ABREV[marca]}-{random.randint(1000, 9999)}"
        if sku not in _skus_usados:
            _skus_usados.add(sku)
            break
    precio_lista = round(random.uniform(15, 850), 2)
    precio_neto = round(precio_lista * random.uniform(0.65, 0.80), 2)
    PRODUCTOS.append({
        "sku": sku,
        "nombre": nombre,
        "categoria": categoria,
        "marca": marca,
        "precio_lista": precio_lista,
        "precio_neto": precio_neto,
        "stock": random.randint(0, 200),
        "stock_minimo": random.randint(5, 20),
        "unidad": "UND",
        "compatibilidad": list({random.choice(COMPAT_MARCAS)
                                for _ in range(random.randint(1, 4))}),
    })


# ===========================================================================
# 4. PEDIDOS (3-8 por cliente activo, últimos 18 meses)
# ===========================================================================
PEDIDOS = []
for cliente in CLIENTES:
    if cliente["estado"] != "activo":
        continue
    n_pedidos = random.randint(3, 8)
    for _ in range(n_pedidos):
        fecha_pedido = fake.date_between(start_date=_meses_atras(18),
                                         end_date=HOY)
        fecha_estimada = fecha_pedido + timedelta(days=random.randint(2, 7))
        estado = random.choices(ESTADOS_PEDIDO, weights=PESOS_PEDIDO)[0]
        if estado == "entregado":
            fecha_real = fecha_estimada + timedelta(days=random.randint(-3, 3))
            fecha_real_iso = fecha_real.isoformat()
        else:
            fecha_real_iso = None

        n_items = random.randint(1, 5)
        items = []
        subtotal = 0.0
        for _ in range(n_items):
            prod = random.choice(PRODUCTOS)
            cantidad = random.randint(1, 20)
            precio_unitario = prod["precio_lista"]
            sub = round(cantidad * precio_unitario, 2)
            subtotal += sub
            items.append({
                "sku": prod["sku"],
                "nombre": prod["nombre"],
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "subtotal": sub,
            })
        subtotal = round(subtotal, 2)
        igv = round(subtotal * 0.18, 2)
        total = round(subtotal + igv, 2)

        PEDIDOS.append({
            "pedido_id": f"PED-{fake.numerify('######')}",
            "cliente_ruc": cliente["ruc"],
            "fecha_pedido": fecha_pedido.isoformat(),
            "fecha_entrega_estimada": fecha_estimada.isoformat(),
            "fecha_entrega_real": fecha_real_iso,
            "estado": estado,
            "transportista": random.choice(TRANSPORTISTAS),
            "items": items,
            "subtotal": subtotal,
            "igv": igv,
            "total": total,
            "numero_factura": f"F001-{fake.numerify('######')}",
            "numero_guia": f"T001-{fake.numerify('######')}",
        })


# ===========================================================================
# 5. LETRAS / COBRANZAS (2-5 por cliente activo con crédito)
# ===========================================================================
LETRAS = []
_pedidos_por_ruc = {}
for p in PEDIDOS:
    _pedidos_por_ruc.setdefault(p["cliente_ruc"], []).append(p)

for cliente in CLIENTES:
    if cliente["estado"] != "activo":
        continue
    pedidos_cliente = _pedidos_por_ruc.get(cliente["ruc"], [])
    for _ in range(random.randint(2, 5)):
        fecha_emision = fake.date_between(start_date=_meses_atras(12),
                                          end_date=HOY)
        fecha_vencimiento = fecha_emision + timedelta(
            days=cliente["dias_credito"])
        estado = random.choices(["pendiente", "vencida", "pagada"],
                                weights=[50, 20, 30])[0]
        dias_mora = random.randint(1, 90) if estado == "vencida" else 0
        pedido_ref = (random.choice(pedidos_cliente)["pedido_id"]
                      if pedidos_cliente else None)
        LETRAS.append({
            "letra_id": f"LET-{fake.numerify('######')}",
            "cliente_ruc": cliente["ruc"],
            "pedido_id": pedido_ref,
            "monto": round(random.uniform(500, 15000), 2),
            "fecha_emision": fecha_emision.isoformat(),
            "fecha_vencimiento": fecha_vencimiento.isoformat(),
            "estado": estado,
            "dias_mora": dias_mora,
        })


# ===========================================================================
# 6. VEHÍCULOS (300)
# ===========================================================================
VEHICULOS = []
_rucs = [c["ruc"] for c in CLIENTES]
for _ in range(300):
    marca = random.choice(MARCAS_VEHICULO)
    VEHICULOS.append({
        "placa": f"{fake.lexify('???').upper()}-{fake.numerify('###')}",
        "vin": fake.bothify("?#?#?#?#?#?#?#?#?").upper(),
        "marca": marca,
        "modelo": random.choice(MODELOS[marca]),
        "año": random.randint(2005, 2024),
        "motor": random.choice(["1.5L", "1.6L", "1.8L", "2.0L",
                                "2.4L", "2.5L", "3.0L"]),
        "propietario_ruc": random.choice(_rucs),
    })


# ===========================================================================
# Índices para búsqueda rápida (O(1)) por clave
# ===========================================================================
VENDEDORES_POR_ID = {v["vendedor_id"]: v for v in VENDEDORES}
CLIENTES_POR_RUC = {c["ruc"]: c for c in CLIENTES}
PRODUCTOS_POR_SKU = {p["sku"]: p for p in PRODUCTOS}

PEDIDOS_POR_RUC = {}
for p in PEDIDOS:
    PEDIDOS_POR_RUC.setdefault(p["cliente_ruc"], []).append(p)

LETRAS_POR_RUC = {}
for l in LETRAS:
    LETRAS_POR_RUC.setdefault(l["cliente_ruc"], []).append(l)

CLIENTES_POR_VENDEDOR = {}
for c in CLIENTES:
    CLIENTES_POR_VENDEDOR.setdefault(c["vendedor_id"], []).append(c)

VEHICULOS_POR_PLACA = {v["placa"]: v for v in VEHICULOS}
VEHICULOS_POR_VIN = {v["vin"]: v for v in VEHICULOS}


# ===========================================================================
# Datos ancla del QA — se inyectan al final, después de armar los índices.
# Ver data/fixtures_qa.py y plan_de_datos.md.
# ===========================================================================
from data import fixtures_qa  # noqa: E402
fixtures_qa.aplicar()
