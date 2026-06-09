# Cómo añadir un nuevo usuario al mock

> Guía para registrar un **nuevo número de WhatsApp** (asesor o cliente) y, si hace falta,
> sus **datos de negocio** en el Mock SAP. Qué campos crear y dónde.

---

## 1. Concepto clave: un usuario vive en 2 capas

| Capa | Dónde | Para qué | Llave |
|------|-------|----------|-------|
| **Autenticación** | `catusita-agent` → `shared/auth.py` | Decide quién eres al escribir por WhatsApp | nº de WhatsApp (asesor) / RUC (cliente) |
| **Datos de negocio** | `mock-sap-catusita` → `data/fixtures_qa.py` y/o Faker | Cartera, crédito, pedidos, cobranzas, etc. | `vendedor_id` (asesor) / `ruc` (cliente) |

> El **vínculo** entre ambas capas es el campo **`vendedor_id`** (para asesores) o el **`ruc`**
> (para clientes). Si el `vendedor_id` o el `ruc` no existe en el Mock SAP, la autenticación
> funciona pero las consultas de datos vendrán vacías o con error.

---

## 2. Recordatorio del sandbox

Hoy, en **sandbox/mock** (`USE_AUTH_MOCK=true`), **cualquier número que escriba en el canal de
vendedores se autentica automáticamente como asesor V001** (ver `shared/auth.py`,
`_asesor_sandbox`). O sea: para *probar* no necesitas registrar el número.

**Registra un número explícito solo si** quieres:
- Que ese número use una cartera distinta a V001 (ej. V002, V003…).
- Mostrar un nombre/línea específicos para ese asesor.
- Prepararte para producción (donde el sandbox por defecto se apaga).

---

## 3. Añadir un nuevo ASESOR (número de WhatsApp)

### Paso 3.1 — Registrar la autenticación

Archivo: `catusita-agent/shared/auth.py` → diccionario `_MOCK_ASESORES`.

La **llave** es el número de WhatsApp en formato `51` + número, **sin `+` ni
`@s.whatsapp.net`** (el webhook ya lo limpia). Agrega una entrada con estos campos:

```python
"51955501234": {                       # ← llave: número de WhatsApp del asesor
    "user_id": "asesor-003",           # id interno único (texto libre)
    "tipo": "asesor",                  # SIEMPRE "asesor"
    "nombre": "Carlos Rojas",          # nombre que mostrará el agente
    "linea_asignada": "frenos",        # línea comercial (texto libre)
    "nivel_acceso": "completo",        # "completo" para asesores
    "asesor_id": "ASE-003",            # id de asesor (texto libre)
    "vendedor_id": "V003",             # ← DEBE existir en el Mock SAP (V001..V010)
    "autenticado": True,               # SIEMPRE True para un usuario válido
},
```

| Campo | Obligatorio | Qué poner |
|-------|-------------|-----------|
| (llave) número WhatsApp | ✅ | `51` + celular, sin `+` ni espacios. Ej. `51955501234` |
| `user_id` | ✅ | Identificador interno único (cualquier texto) |
| `tipo` | ✅ | Literal `"asesor"` |
| `nombre` | ✅ | Nombre visible del asesor |
| `linea_asignada` | ✅ | Línea de productos (texto) |
| `nivel_acceso` | ✅ | `"completo"` |
| `asesor_id` | ✅ | Id de asesor (texto) |
| `vendedor_id` | ✅ | **Debe coincidir con un vendedor del Mock SAP** (`V001`–`V010`) |
| `autenticado` | ✅ | `True` |

### Paso 3.2 — Asegurar que el `vendedor_id` tiene datos en el Mock SAP

- Si usas un **vendedor existente** (`V001`–`V010`): ya tiene cartera Faker. ✅ No haces nada más.
  - `V001` además tiene los **datos de QA** (Transportes Andinos SAC, etc.).
- Si quieres un **vendedor nuevo** (ej. `V011`) o una cartera controlada: hay que crearlo como
  fixture en el Mock SAP (ver sección 5).

---

## 4. Añadir un nuevo CLIENTE (por RUC)

### Paso 4.1 — Registrar la autenticación (canal de clientes)

Archivo: `catusita-agent/shared/auth.py` → diccionario `_MOCK_CLIENTES_RUC`.

La **llave** es el **RUC**. Campos:

```python
"20111222333": {                       # ← llave: RUC del cliente
    "user_id": "cliente-003",          # id interno único
    "tipo": "cliente",                 # SIEMPRE "cliente"
    "nombre": "Taller El Rápido SAC",  # nombre visible
    "ruc": "20111222333",              # mismo RUC que la llave
    "nivel_acceso": "basico",          # "basico" para clientes
    "autenticado": True,               # True
},
```

| Campo | Obligatorio | Qué poner |
|-------|-------------|-----------|
| (llave) RUC | ✅ | RUC. Empresas empiezan en `20`, persona natural en `10` |
| `user_id` | ✅ | Id interno único |
| `tipo` | ✅ | Literal `"cliente"` |
| `nombre` | ✅ | Nombre visible |
| `ruc` | ✅ | Mismo valor que la llave |
| `nivel_acceso` | ✅ | `"basico"` |
| `autenticado` | ✅ | `True` |

### Paso 4.2 — Crear sus datos en el Mock SAP

Para que el cliente tenga perfil, crédito, pedidos, etc., debe existir como **fixture** en el
Mock SAP con su RUC (ver sección 5). Si solo lo registras en `auth.py` pero no en el Mock SAP,
las consultas de sus datos devolverán "no encontrado".

---

## 5. Crear datos de negocio en el Mock SAP (fixtures)

Archivo: `mock-sap-catusita/data/fixtures_qa.py`. Agrega a las listas correspondientes y la
función `aplicar()` los inyecta automáticamente al arrancar.

### 5.1 Cliente (para que el asesor lo vea en su cartera)

Agrega a `CLIENTES_QA`. **El campo `vendedor_id` decide en qué cartera aparece.**

```python
{
    "ruc": "20111222333",
    "razon_social": "Taller El Rápido SAC",
    "tipo": "taller",                      # taller | distribuidor | consumidor_final
    "direccion": "Av. Ejemplo 123, Surco", # el distrito = última parte tras la coma
    "telefono": "+511 900111222",
    "email": "contacto@elrapido.pe",
    "vendedor_id": "V003",                 # ← cartera del asesor dueño
    "limite_credito": 40000,
    "dias_credito": 30,
    "estado": "activo",                    # activo | suspendido | bloqueado
    "fecha_registro": _d(-600),            # _d(n) = fecha relativa a hoy (n días)
},
```

### 5.2 Vendedor nuevo (solo si NO usas V001–V010)

El Mock SAP ya trae `V001`–`V010`. Si necesitas uno nuevo, agrégalo en `fixtures_qa.py`
(lista nueva `VENDEDORES_QA`) y engánchalo en `aplicar()` a `seed.VENDEDORES` /
`seed.VENDEDORES_POR_ID`. Campos de un vendedor: `vendedor_id`, `nombre`, `email`,
`telefono`, `zona`, `fecha_ingreso`.

### 5.3 Productos, pedidos, letras, vehículos

Mismo patrón: añadir a `PRODUCTOS_QA`, `PEDIDOS_QA`, `LETRAS_QA`, `VEHICULOS_QA`. Ver los
ejemplos ya existentes en `fixtures_qa.py` para los nombres de campo exactos.

---

## 6. Checklist al añadir un usuario

**Asesor nuevo:**
- [ ] Entrada en `_MOCK_ASESORES` (`shared/auth.py`) con número como llave.
- [ ] `vendedor_id` existe en el Mock SAP (V001–V010) o se creó como fixture.
- [ ] (Opcional) Clientes en `CLIENTES_QA` con ese `vendedor_id` para llenar su cartera.

**Cliente nuevo:**
- [ ] Entrada en `_MOCK_CLIENTES_RUC` (`shared/auth.py`) con RUC como llave.
- [ ] Fixture en `CLIENTES_QA` (Mock SAP) con el mismo RUC y un `vendedor_id` válido.
- [ ] (Opcional) Pedidos/letras de ese RUC si quieres probar pedidos/cobranzas.

**Siempre:**
- [ ] Tras editar el Mock SAP, **push a Railway** (auto-deploy) para que los datos estén vivos.
- [ ] Verificar con `curl` (ver `datos_qa.md`, sección 7).

---

## 7. Errores comunes

| Síntoma | Causa | Solución |
|---------|-------|----------|
| "Tu número no está registrado" | Estás en modo no-sandbox y el número no está en `_MOCK_ASESORES` | Agrégalo, o usa sandbox (`USE_AUTH_MOCK=true`) |
| El asesor entra pero su cartera sale vacía | `vendedor_id` no existe en el Mock SAP | Usa V001–V010 o crea el vendedor como fixture |
| "Cliente no encontrado" al consultar datos | El RUC está en `auth.py` pero no en el Mock SAP | Crear el cliente en `CLIENTES_QA` |
| El agente "no es de tu cartera" con un cliente que sí es tuyo | El cliente tiene otro `vendedor_id` que el del asesor | Alinear el `vendedor_id` del cliente al del asesor |
</content>
