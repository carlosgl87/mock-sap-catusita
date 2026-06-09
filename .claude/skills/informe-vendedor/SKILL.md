---
name: informe-vendedor
description: Genera un informe claro y entendible para un asesor de ventas (vendedor) de Catusita, explicando qué puede preguntarle al agente Catu, con ejemplos reales, un resumen de SU data (su cartera de clientes, productos disponibles) y qué cosas el agente NO hace (deriva). Usar cuando el usuario pida un "informe para el vendedor", "qué puede preguntar el asesor", "guía para el vendedor", "reporte de capacidades", o quiera entregarle a un asesor una explicación amigable de Catu y sus datos.
---

# Informe para el Vendedor (asesor de ventas)

Genera un documento **amigable y no técnico** que se le entrega a un asesor de ventas para
que sepa: (1) qué puede preguntarle a Catu, (2) cuál es su data disponible, y (3) qué no hace.

## Entrada

- Argumento opcional: `vendedor_id` (ej. `V001`, `V002`) **o** número de WhatsApp del asesor.
  - Si te dan un número de WhatsApp, mapéalo con `catusita-agent/shared/auth.py` (`_MOCK_ASESORES`).
    Si el número no está registrado, en sandbox equivale a **V001**.
  - Si no te dan nada, usa **V001** (la cartera con datos de QA) y avísalo.

## Configuración del Mock SAP (para traer la data real)

```
BASE = https://mock-sap-catusita-production.up.railway.app
HEADER = X-API-Key: catusita-mock-key-2024
```

## Pasos

1. **Trae la cartera del asesor** para resumir SU data:
   `curl -s -H "X-API-Key: catusita-mock-key-2024" "$BASE/vendedor/{vendedor_id}/clientes"`
   - De ahí saca: total de clientes, cuántos por estado (activo/suspendido/bloqueado),
     cuántos por tipo (taller/distribuidor/consumidor_final), y 2-3 nombres de ejemplo
     (razón social) con su RUC para usarlos en los ejemplos de preguntas.

2. **Trae una muestra de productos** para ejemplos de stock/precio:
   `curl -s -H "X-API-Key: catusita-mock-key-2024" "$BASE/catalogo?q=filtro"`
   - Toma 1-2 SKUs reales para los ejemplos.

3. **Construye el informe** con la plantilla de abajo, rellenando los ejemplos con los
   nombres/RUCs/SKUs **reales** que trajiste (no inventes). Si el Mock SAP no responde,
   genera el informe igual pero con ejemplos genéricos y nota que la data en vivo no se pudo cargar.

4. Entrega el informe como **Markdown legible**. Si el usuario lo pide como archivo,
   guárdalo (ej. `informe_vendedor_{vendedor_id}.md`).

## Reglas

- Lenguaje **simple, de negocio**, sin jerga técnica (nada de "tool", "endpoint", "JSON", "API").
- Usa los **datos reales** del asesor para que el informe se sienta suyo.
- Sé honesto sobre los límites: lo que el agente NO hace debe quedar claro.
- Conciso pero completo. Emojis con moderación para legibilidad.

## Plantilla del informe

```markdown
# 📱 Guía de Catu para {NOMBRE_ASESOR}

Catu es tu asistente de WhatsApp. Le escribes como a un compañero y te responde al toque.
Aquí tienes todo lo que le puedes pedir.

## ✅ Lo que le puedes preguntar

### 📦 Stock y productos
- "¿Hay stock del {SKU_EJEMPLO}?"
- "Búscame filtros de aceite para Toyota Hilux"
- "¿Tienen algún equivalente al filtro [código del fabricante]?"

### 💰 Precios
- "¿Cuál es el precio de lista del {SKU_EJEMPLO}?"
> Catu solo maneja **precio de lista**. Descuentos o precios especiales los coordinas con tu jefe de línea.

### 👥 Tu cartera de clientes
- "¿Qué clientes tengo asignados?"
- "¿Cuántos clientes activos tengo?"
- "Dame el perfil de {CLIENTE_EJEMPLO}"

### 💳 Crédito y cobranzas (solo de TUS clientes)
- "¿Cuánto crédito disponible tiene {CLIENTE_EJEMPLO}?"
- "¿{CLIENTE_EJEMPLO} tiene deuda vencida?"
- "¿Qué clientes míos tienen letras por vencer esta semana?"

### 🛒 Pedidos y entregas
- "¿Cuáles son los últimos pedidos de {CLIENTE_EJEMPLO}?"
- "¿En qué estado está el pedido [número]?"
- "¿Cuándo llega el pedido [número]?"

### 💵 Pagos y documentos
- "¿La factura [número] está pagada?"
- "Pásame la factura del pedido [número]"
- "¿Dónde está la guía de remisión del pedido [número]?"

### 🚗 Vehículos
- "¿Qué repuestos sirven para la placa ABC-123?"

## 📊 Tu data hoy
- **Clientes asignados:** {TOTAL_CLIENTES} (activos: {N_ACTIVOS}, suspendidos: {N_SUSP}, bloqueados: {N_BLOQ})
- **Tipos:** {N_TALLER} talleres · {N_DISTRIB} distribuidores · {N_CONSUMIDOR} consumidor final
- **Algunos de tus clientes:** {CLIENTE_1}, {CLIENTE_2}, {CLIENTE_3}

## ⚠️ Lo que Catu NO hace (te deriva)
- ❌ No da precios netos, descuentos por volumen ni precios especiales → tu jefe de línea
- ❌ No aprueba excepciones de crédito → área de créditos
- ❌ No te dice en qué almacén/local está el producto ni la hora de reparto → logística
- ❌ No te da fecha de reposición de productos agotados (aún) → tu jefe de línea
- ❌ No te da información de clientes que no son de tu cartera
- ❌ Nunca inventa datos: si no lo sabe, te lo dice

## 💡 Tips
- Puedes nombrar al cliente por su nombre (no necesitas el RUC): "el crédito de {CLIENTE_EJEMPLO}".
- Si pides un reclamo, Catu toma los datos y lo deriva a atención al cliente.
```
