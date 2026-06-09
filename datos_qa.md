# Datos de Prueba — QA Agente Vendedores (Catu)

> **Set de datos congelado** para el QA. Generado por las fixtures de
> `data/fixtures_qa.py` (deterministas, relativas a la fecha de ejecución).
> Estos valores NO cambian entre reinicios del Mock SAP.
>
> Asesor de prueba: **Luis García** · `vendedor_id = V001`
> Mock SAP: `https://mock-sap-catusita-production.up.railway.app`
> API Key (header `X-API-Key`): `catusita-mock-key-2024`

---

## 1. Clientes

| Rol en el QA | RUC | Razón social | Vendedor | Notas |
|--------------|-----|--------------|----------|-------|
| **Cliente propio A** | `20100000001` | **Transportes Andinos SAC** | V001 | Tiene crédito, pedidos, factura/guía y deuda (1 vencida + 1 por vencer) |
| **Cliente propio B** | `20100000002` | Taller Mecánico Aguilar SAC | V001 | Tiene **una letra que vence esta semana** |
| **Cliente propio C** | `20100000003` | Distribuidora Repuestos Lima SAC | V001 | **Al día** (sin deuda) — para contraste |
| **Cliente AJENO** | `20900000009` | Importadora del Sur SAC | **V002** | NO es de V001 → el agente debe **rechazar** la consulta |
| **ID inválido** | `12345` | (no existe) | — | Para probar validación de cartera con un id desconocido |

---

## 2. Productos

| Rol en el QA | SKU | Nombre | Stock | Notas |
|--------------|-----|--------|-------|-------|
| **Producto OK** | `FIL-BOC-0001` | Filtro de aceite Bosch | 85 | Stock conocido, precio de lista S/ 38.00 |
| **Producto Fram** | `FIL-FRA-0001` | Filtro de aceite Fram | 120 | Compatible Toyota; precio de lista S/ 45.00 |
| **Producto AGOTADO** | `FRE-BEN-0001` | Pastilla de freno Bendix | **0** | Para "¿cuándo llega el reabastecimiento?" → debe derivar |
| **Códigos OEM (Fram)** | — | — | — | `90915-YZZD2`, `FRM-OIL-77` → para buscar equivalencia |

---

## 3. Vehículo

| Placa | VIN | Marca / Modelo / Año | Propietario |
|-------|-----|----------------------|-------------|
| `ABC-123` | `1HGBH41JXMN109186` | Toyota Hilux 2019 | Transportes Andinos SAC (`20100000001`) |

---

## 4. Pedidos (de Transportes Andinos SAC · `20100000001`)

| pedido_id | Estado | Nº Factura | Nº Guía |
|-----------|--------|-----------|---------|
| `PED-000001` | entregado | `F001-000001` | `T001-000001` |
| `PED-000002` | en_transito | `F001-000002` | `T001-000002` |
| `PED-000003` | entregado | `F001-000003` | `T001-000003` |
| `PED-000004` | en_almacen | `F001-000004` | `T001-000004` |
| `PED-000005` | entregado | `F001-000005` | `T001-000005` |

---

## 5. Cobranzas / Letras

| Cliente | letra_id | Monto | Vencimiento | Estado |
|---------|----------|-------|-------------|--------|
| Transportes Andinos (`...001`) | `LET-000001` | S/ 5 000 | hoy − 12 días | **vencida** |
| Transportes Andinos (`...001`) | `LET-000002` | S/ 6 000 | hoy + 40 días | pendiente |
| Taller Aguilar (`...002`) | `LET-000003` | S/ 3 200 | **hoy + 3 días** | pendiente (vence esta semana) |
| Distribuidora Lima (`...003`) | — | — | — | sin letras (al día) |

> Resumen Transportes Andinos: deuda total **S/ 11 000** · vencida **S/ 5 000** · crédito disponible **S/ 39 000** · estado **vencido**.

---

## 6. Valores para rellenar `plan_de_prueba.md`

| Variable del plan de prueba | Valor congelado |
|-----------------------------|-----------------|
| `RUC_MIO_A` | `20100000001` |
| `NOMBRE_MIO_A` | Transportes Andinos SAC |
| `RUC_MIO_B` | `20100000002` |
| `RUC_AJENO` | `20900000009` |
| `SKU_VALIDO` | `FIL-BOC-0001` |
| `SKU_AGOTADO` | `FRE-BEN-0001` |
| `PEDIDO_MIO` | `PED-000001` |
| `FACTURA_MIA` | `F001-000001` |
| Placa Toyota Hilux | `ABC-123` |
| Producto Fram | `FIL-FRA-0001` |
| Código OEM | `90915-YZZD2` |

---

## 7. Verificación rápida (curl)

```bash
KEY="catusita-mock-key-2024"
BASE="https://mock-sap-catusita-production.up.railway.app"

curl -H "X-API-Key: $KEY" "$BASE/vendedor/V001/clientes"   # debe incluir 20100000001, ...002, ...003
curl -H "X-API-Key: $KEY" "$BASE/vendedor/V002/clientes"   # debe incluir 20900000009 (NO en V001)
curl -H "X-API-Key: $KEY" "$BASE/clientes/20100000001"     # Transportes Andinos SAC
curl -H "X-API-Key: $KEY" "$BASE/stock/FRE-BEN-0001"       # stock = 0
curl -H "X-API-Key: $KEY" "$BASE/stock/FIL-FRA-0001"       # filtro Fram, stock 120
curl -H "X-API-Key: $KEY" "$BASE/credito/20100000001"      # disponible 39000, estado vencido
curl -H "X-API-Key: $KEY" "$BASE/cobranzas/20100000002"    # letra que vence esta semana
curl -H "X-API-Key: $KEY" "$BASE/pedidos/20100000001"      # 5 pedidos con factura/guía
curl -H "X-API-Key: $KEY" "$BASE/vehiculo/ABC-123"         # Toyota Hilux 2019
curl -H "X-API-Key: $KEY" "$BASE/catalogo?q=90915-YZZD2"   # equivalencia por OEM -> FIL-FRA-0001
```

> Si algún `curl` no devuelve lo esperado, el deploy del Mock SAP no tiene las fixtures
> (`data/fixtures_qa.py`) o no se reinició tras el último push.
</content>
