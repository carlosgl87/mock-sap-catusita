# CLAUDE.md — Mock SAP Server para Catusita

## Descripción del proyecto

Crear un servidor FastAPI que simula las APIs de SAP de Grupo Catusita (distribuidora de repuestos automotrices en Perú). Este servidor es un mock de prueba — todos los datos son generados con Faker en español con semilla fija para que sean siempre consistentes. No usa base de datos.

El agente de WhatsApp de Catusita (ya deployado en Railway) llamará a este servidor para obtener datos de clientes, stock, pedidos, crédito, etc. Cuando Catusita entregue las APIs reales de SAP, solo se cambiará la variable de entorno `SAP_BASE_URL` en el agente — este servidor se apaga.

---

## Stack

- Python 3.11
- FastAPI + Uvicorn
- Faker (con locale `es_PE` para datos peruanos)
- Sin base de datos — datos en memoria generados al arrancar
- Sin ORM

Instalar con:
```
pip install fastapi uvicorn faker python-dotenv
```

---

## Estructura de carpetas a crear

```
mock-sap-catusita/
├── CLAUDE.md
├── main.py                  ← app FastAPI, todos los endpoints
├── data/
│   ├── __init__.py
│   ├── seed.py              ← genera todos los datos con Faker al arrancar
│   ├── vendedores.py        ← lógica de vendedores y su cartera
│   ├── clientes.py          ← lógica de clientes
│   ├── productos.py         ← lógica de productos, stock y precios
│   └── pedidos.py           ← lógica de pedidos, documentos, historial
├── auth.py                  ← validación del API key
├── requirements.txt
├── railway.toml             ← config de deploy
├── .env.example
└── .gitignore
```

---

## Variables de entorno

Crear `.env.example`:
```
MOCK_API_KEY=catusita-mock-key-2024
```

El servidor lee `MOCK_API_KEY` del entorno. Si no existe, usa el valor por defecto `catusita-mock-key-2024`.

---

## Autenticación

Todas las rutas (excepto `/` y `/health`) requieren el header:
```
X-API-Key: catusita-mock-key-2024
```

Si el header falta o es incorrecto, devolver `401 Unauthorized` con mensaje:
```json
{"detail": "API Key inválida o ausente"}
```

Implementar como FastAPI dependency en `auth.py`:
```python
from fastapi import Header, HTTPException
import os

async def verify_api_key(x_api_key: str = Header(...)):
    expected = os.getenv("MOCK_API_KEY", "catusita-mock-key-2024")
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="API Key inválida o ausente")
```

---

## Generación de datos con Faker

En `data/seed.py`, generar todos los datos al arrancar con semilla fija:

```python
from faker import Faker
import random

fake = Faker("es_PE")
Faker.seed(42)
random.seed(42)
```

### Datos a generar

#### Vendedores (10 vendedores)
```python
ZONAS = ["Norte Lima", "Sur Lima", "Centro Lima", "Este Lima", "Provincias Norte", "Provincias Sur"]
VENDEDORES = []
for i in range(10):
    vendedor_id = f"V{str(i+1).zfill(3)}"
    VENDEDORES.append({
        "vendedor_id": vendedor_id,
        "nombre": fake.name(),
        "email": fake.email(),
        "telefono": f"+511 9{fake.numerify('########')}",
        "zona": random.choice(ZONAS),
        "fecha_ingreso": fake.date_between(start_date="-8y", end_date="-1y").isoformat(),
    })
```

#### Clientes (200 clientes en total, 15-30 por vendedor)
Tipos de cliente: `"taller"`, `"distribuidor"`, `"consumidor_final"`

Razones sociales realistas según tipo:
- Taller: "Taller Mecánico {apellido} {sufijo}" donde sufijo es SAC, EIRL, SRL o E.I.R.L
- Distribuidor: "Distribuidora {apellido} {sufijo}" o "Repuestos {apellido} {sufijo}"
- Consumidor final: nombre de persona natural

RUC: 11 dígitos, empieza en 20 para empresas, 10 para personas naturales.

Distritos de Lima: Los Olivos, San Juan de Lurigancho, Ate, Villa El Salvador, San Martín de Porres, Comas, Independencia, El Agustino, La Victoria, Callao, Surco, Miraflores, San Isidro, Lince, Breña.

Cada cliente tiene:
```python
{
    "ruc": "20" + fake.numerify("#########"),
    "razon_social": ...,
    "tipo": random.choice(["taller", "distribuidor", "consumidor_final"]),
    "direccion": f"{fake.street_name()} {fake.building_number()}, {random.choice(DISTRITOS)}",
    "telefono": f"+511 9{fake.numerify('########')}",
    "email": fake.company_email(),
    "vendedor_id": ...,  # asignado al crear
    "limite_credito": random.choice([5000, 10000, 20000, 30000, 50000, 80000, 100000]),
    "dias_credito": random.choice([30, 45, 60, 90]),
    "estado": random.choices(["activo", "suspendido", "bloqueado"], weights=[85, 10, 5])[0],
    "fecha_registro": fake.date_between(start_date="-5y", end_date="-6m").isoformat(),
}
```

Asignar 15-30 clientes a cada vendedor de forma balanceada.

#### Productos (150 productos de repuestos automotrices)
Categorías y ejemplos de nombres:
- Filtros: "Filtro de aceite {marca}", "Filtro de aire {marca}", "Filtro de combustible {marca}"
- Frenos: "Pastilla de freno {marca}", "Disco de freno {marca}", "Zapata de freno {marca}"
- Motor: "Bujía {marca}", "Correa de distribución {marca}", "Banda alternador {marca}"
- Suspensión: "Amortiguador delantero {marca}", "Espiral de suspensión {marca}", "Rótula {marca}"
- Eléctrico: "Batería {capacidad}Ah {marca}", "Alternador {marca}", "Motor de arranque {marca}"
- Lubricantes: "Aceite de motor {viscosidad} {marca}", "Líquido de frenos {marca}"

Marcas peruanas/regionales: ACDelco, Monroe, Bosch, Gates, NGK, Mobil, Castrol, Moog, Bendix, Ferodo

SKU format: `{CATEGORIA_ABREV}-{MARCA_ABREV}-{NÚMERO_4_DIGITOS}` ej: `FIL-BOC-4521`

Cada producto:
```python
{
    "sku": ...,
    "nombre": ...,
    "categoria": ...,
    "marca": ...,
    "precio_lista": round(random.uniform(15, 850), 2),
    "precio_neto": ...,  # precio_lista * random.uniform(0.65, 0.80) redondeado a 2 decimales
    "stock": random.randint(0, 200),
    "stock_minimo": random.randint(5, 20),
    "unidad": "UND",
    "compatibilidad": [random.choice(["Toyota", "Hyundai", "Kia", "Nissan", "Chevrolet", "Ford", "Volkswagen"]) for _ in range(random.randint(1,4))],
}
```

#### Pedidos (3-8 pedidos por cliente activo, de los últimos 18 meses)
Estados posibles: `"en_almacen"`, `"en_transito"`, `"entregado"`, `"con_incidencia"`, `"anulado"`
Pesos: entregado 60%, en_almacen 15%, en_transito 15%, con_incidencia 7%, anulado 3%

Cada pedido:
```python
{
    "pedido_id": f"PED-{fake.numerify('######')}",
    "cliente_ruc": ...,
    "fecha_pedido": fake.date_between(start_date="-18m", end_date="today").isoformat(),
    "fecha_entrega_estimada": ...,  # fecha_pedido + 2-7 días
    "fecha_entrega_real": ...,  # solo si estado es entregado, fecha_estimada +/- 1-3 días
    "estado": ...,
    "transportista": random.choice(["Olva Courier", "Shalom", "Cruz del Sur", "Recojo en tienda"]),
    "items": [  # 1-5 items por pedido
        {
            "sku": ...,
            "nombre": ...,
            "cantidad": random.randint(1, 20),
            "precio_unitario": ...,
            "subtotal": ...,
        }
    ],
    "subtotal": ...,
    "igv": ...,  # subtotal * 0.18
    "total": ...,  # subtotal + igv
    "numero_factura": f"F001-{fake.numerify('######')}",
    "numero_guia": f"T001-{fake.numerify('######')}",
}
```

#### Letras / cobranzas (por cliente con crédito)
Generar 2-5 letras por cliente activo:
```python
{
    "letra_id": f"LET-{fake.numerify('######')}",
    "cliente_ruc": ...,
    "pedido_id": ...,
    "monto": round(random.uniform(500, 15000), 2),
    "fecha_emision": ...,
    "fecha_vencimiento": ...,  # fecha_emision + dias_credito del cliente
    "estado": random.choices(["pendiente", "vencida", "pagada"], weights=[50, 20, 30])[0],
    "dias_mora": ...,  # solo si vencida: random.randint(1, 90)
}
```

#### Vehículos (para el lookup de placa/VIN)
Generar 300 vehículos con placas peruanas:
- Placas formato nuevo: `ABC-123` (3 letras + 3 números)
- VIN: 17 caracteres alfanuméricos

```python
{
    "placa": f"{fake.lexify('???').upper()}-{fake.numerify('###')}",
    "vin": fake.bothify("?#?#?#?#?#?#?#?#?").upper(),
    "marca": random.choice(["Toyota", "Hyundai", "Kia", "Nissan", "Chevrolet", "Ford", "Volkswagen", "Suzuki"]),
    "modelo": ...,  # coherente con la marca
    "año": random.randint(2005, 2024),
    "motor": random.choice(["1.5L", "1.6L", "1.8L", "2.0L", "2.4L", "2.5L", "3.0L"]),
    "propietario_ruc": ...,  # RUC de un cliente existente
}
```

Modelos por marca:
- Toyota: Corolla, Hilux, RAV4, Yaris, Land Cruiser
- Hyundai: Tucson, Santa Fe, Accent, Elantra, H-1
- Kia: Sportage, Sorento, Rio, Cerato, Carnival
- Nissan: Frontier, X-Trail, Sentra, Versa, Navara
- Chevrolet: Tracker, D-Max, Sail, Spark, Captiva
- Ford: Ranger, Explorer, F-150, EcoSport, Fusion
- Volkswagen: Golf, Tiguan, Amarok, Polo, Touareg
- Suzuki: Jimny, Vitara, Swift, Grand Vitara, S-Cross

---

## Endpoints a implementar en main.py

### Rutas base (sin autenticación)
```
GET /          → {"service": "Mock SAP Catusita", "version": "1.0.0", "status": "ok"}
GET /health    → {"status": "healthy", "records": {"vendedores": N, "clientes": N, "productos": N, "pedidos": N}}
GET /docs      → Swagger UI automático de FastAPI
```

### Rutas con autenticación (todas requieren X-API-Key header)

#### 1. Stock
```
GET /stock/{sku}
```
Respuesta:
```json
{
  "sku": "FIL-BOC-4521",
  "nombre": "Filtro de aceite Bosch",
  "stock": 45,
  "stock_minimo": 10,
  "disponible": true,
  "alerta_stock_bajo": false,
  "unidad": "UND"
}
```
Si SKU no existe: 404 con `{"detail": "Producto no encontrado"}`

#### 2. Precios
```
GET /precios/{sku}
GET /precios/{sku}?tipo=neto       ← solo precio neto (para vendedores)
GET /precios/{sku}?tipo=lista      ← solo precio lista (para clientes)
```
Respuesta completa:
```json
{
  "sku": "FIL-BOC-4521",
  "nombre": "Filtro de aceite Bosch",
  "precio_lista": 45.90,
  "precio_neto": 32.50,
  "descuento_porcentaje": 29.2,
  "igv_incluido": true,
  "moneda": "PEN"
}
```

#### 3. Pedidos por cliente
```
GET /pedidos/{cliente_ruc}
GET /pedidos/{cliente_ruc}?estado=en_transito
GET /pedidos/{cliente_ruc}?limite=10
```
Respuesta:
```json
{
  "cliente_ruc": "20123456789",
  "total_pedidos": 6,
  "pedidos": [ ...lista de pedidos... ]
}
```

#### 4. Crédito
```
GET /credito/{cliente_ruc}
```
Respuesta:
```json
{
  "cliente_ruc": "20123456789",
  "razon_social": "Taller Mecánico García SAC",
  "limite_credito": 20000.00,
  "saldo_usado": 8500.00,
  "saldo_disponible": 11500.00,
  "porcentaje_usado": 42.5,
  "dias_credito": 60,
  "estado_credito": "al_dia",
  "moneda": "PEN"
}
```
`estado_credito` puede ser: `"al_dia"`, `"por_vencer"` (vence en menos de 7 días), `"vencido"`

#### 5. Cobranzas
```
GET /cobranzas/{cliente_ruc}
GET /cobranzas/{cliente_ruc}?estado=pendiente
```
Respuesta:
```json
{
  "cliente_ruc": "20123456789",
  "total_deuda": 8500.00,
  "deuda_vencida": 2000.00,
  "deuda_por_vencer": 6500.00,
  "letras": [ ...lista de letras... ]
}
```

#### 6. Documentos
```
GET /documentos/{cliente_ruc}
GET /documentos/{cliente_ruc}?tipo=factura
GET /documentos/{cliente_ruc}?tipo=guia
```
Respuesta:
```json
{
  "cliente_ruc": "20123456789",
  "documentos": [
    {
      "tipo": "factura",
      "numero": "F001-003421",
      "pedido_id": "PED-003421",
      "fecha": "2024-03-15",
      "monto": 1250.00,
      "estado": "pagada"
    }
  ]
}
```

#### 7. Perfil de cliente
```
GET /clientes/{ruc}
```
Respuesta:
```json
{
  "ruc": "20123456789",
  "razon_social": "Taller Mecánico García SAC",
  "tipo": "taller",
  "direccion": "Av. Túpac Amaru 1234, Los Olivos",
  "telefono": "+511 987654321",
  "email": "garcia.taller@gmail.com",
  "vendedor_id": "V003",
  "vendedor_nombre": "Carlos Quispe",
  "limite_credito": 20000.00,
  "dias_credito": 60,
  "estado": "activo",
  "fecha_registro": "2021-06-10"
}
```

#### 8. Historial de compras
```
GET /historial/{cliente_ruc}
GET /historial/{cliente_ruc}?meses=6    ← últimos N meses, default 18
```
Respuesta:
```json
{
  "cliente_ruc": "20123456789",
  "periodo_meses": 18,
  "total_compras": 6,
  "monto_total": 18500.00,
  "promedio_mensual": 1027.78,
  "producto_mas_comprado": "Filtro de aceite Bosch",
  "pedidos": [ ...lista resumida... ]
}
```

#### 9. Vehículo por placa o VIN
```
GET /vehiculo/{placa_o_vin}
```
El endpoint detecta automáticamente si es placa (formato ABC-123) o VIN (17 caracteres). Respuesta:
```json
{
  "placa": "ABC-123",
  "vin": "1HGBH41JXMN109186",
  "marca": "Toyota",
  "modelo": "Hilux",
  "año": 2019,
  "motor": "2.4L",
  "propietario_ruc": "20123456789",
  "propietario_nombre": "Taller Mecánico García SAC",
  "repuestos_compatibles": [
    {"sku": "FIL-BOC-4521", "nombre": "Filtro de aceite Bosch", "stock": 45}
  ]
}
```
Incluir 3-5 repuestos compatibles con esa marca/modelo del stock existente.

#### 10. Catálogo / búsqueda de productos
```
GET /catalogo
GET /catalogo?q=filtro+aceite
GET /catalogo?categoria=frenos
GET /catalogo?marca=bosch
GET /catalogo?marca=bosch&categoria=filtros
GET /catalogo?con_stock=true
```
Respuesta:
```json
{
  "total": 12,
  "productos": [ ...lista de productos... ]
}
```
La búsqueda por `q` busca en nombre y categoría (case-insensitive, sin acentos).

#### 11. Cartera de clientes por vendedor
```
GET /vendedor/{vendedor_id}/clientes
GET /vendedor/{vendedor_id}/clientes?estado=activo
GET /vendedor/{vendedor_id}/clientes?tipo=taller
```
Respuesta:
```json
{
  "vendedor_id": "V003",
  "vendedor_nombre": "Carlos Quispe",
  "zona": "Norte Lima",
  "total_clientes": 22,
  "clientes": [
    {
      "ruc": "20123456789",
      "razon_social": "Taller Mecánico García SAC",
      "tipo": "taller",
      "distrito": "Los Olivos",
      "telefono": "+511 987654321",
      "estado": "activo",
      "limite_credito": 20000.00,
      "saldo_pendiente": 8500.00,
      "ultimo_pedido": "2024-03-10",
      "monto_ultimo_pedido": 1250.00
    }
  ]
}
```

---

## Configuración Railway

Crear `railway.toml`:
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

---

## requirements.txt
```
fastapi==0.111.0
uvicorn==0.29.0
faker==24.0.0
python-dotenv==1.0.1
```

---

## .gitignore
```
.env
__pycache__/
*.pyc
.DS_Store
```

---

## Comportamiento esperado

1. Al arrancar, `seed.py` genera todos los datos en memoria (vendedores, clientes, productos, pedidos, letras, vehículos). Esto toma menos de 1 segundo.
2. Todos los datos son consistentes entre sí — los pedidos referencian RUCs de clientes existentes, los clientes tienen vendedores válidos, etc.
3. Los datos son SIEMPRE los mismos entre reinicios del servidor (semilla fija = 42).
4. FastAPI genera automáticamente `/docs` (Swagger UI) y `/redoc`.
5. Todos los endpoints devuelven JSON con Content-Type: application/json.
6. Los errores siempre devuelven `{"detail": "mensaje de error"}`.

---

## Notas importantes

- NO usar base de datos. Todo en memoria.
- NO usar archivos JSON externos. Los datos se generan con Faker al arrancar y viven en variables globales de Python.
- La semilla Faker.seed(42) y random.seed(42) deben llamarse UNA SOLA VEZ al inicio de seed.py, antes de generar cualquier dato.
- El módulo `data/seed.py` se importa una sola vez al arrancar FastAPI. Los datos generados se guardan en variables a nivel de módulo (no dentro de funciones) para que persistan durante toda la vida del proceso.
- Usar `unicodedata.normalize` para búsquedas sin acentos en el catálogo.
- En el endpoint `/vehiculo/{placa_o_vin}`, detectar placa con regex `r'^[A-Z]{3}-\d{3}$'` y VIN con longitud 17.
