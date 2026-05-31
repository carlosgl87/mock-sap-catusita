"""Mock SAP Server para Grupo Catusita.

Servidor FastAPI que simula las APIs de SAP. Todos los datos son generados con
Faker (semilla fija = 42) al arrancar y viven en memoria. No usa base de datos.

Arrancar con:
    uvicorn main:app --reload
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from dotenv import load_dotenv

load_dotenv()

from auth import verify_api_key
from data import seed
from data import productos as productos_logic
from data import clientes as clientes_logic
from data import pedidos as pedidos_logic
from data import vendedores as vendedores_logic

app = FastAPI(
    title="Mock SAP Catusita",
    description="Servidor mock que simula las APIs de SAP de Grupo Catusita.",
    version="1.0.0",
)


# ===========================================================================
# Rutas base (sin autenticación)
# ===========================================================================
@app.get("/")
async def root():
    return {"service": "Mock SAP Catusita", "version": "1.0.0", "status": "ok"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "records": {
            "vendedores": len(seed.VENDEDORES),
            "clientes": len(seed.CLIENTES),
            "productos": len(seed.PRODUCTOS),
            "pedidos": len(seed.PEDIDOS),
        },
    }


# ===========================================================================
# 1. Stock
# ===========================================================================
@app.get("/stock/{sku}", dependencies=[Depends(verify_api_key)])
async def stock(sku: str):
    resultado = productos_logic.get_stock(sku)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return resultado


# ===========================================================================
# 2. Precios
# ===========================================================================
@app.get("/precios/{sku}", dependencies=[Depends(verify_api_key)])
async def precios(sku: str, tipo: str = Query(None, regex="^(neto|lista)$")):
    resultado = productos_logic.get_precio(sku, tipo)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return resultado


# ===========================================================================
# 3. Pedidos por cliente
# ===========================================================================
@app.get("/pedidos/{cliente_ruc}", dependencies=[Depends(verify_api_key)])
async def pedidos(cliente_ruc: str, estado: str = None, limite: int = None):
    resultado = pedidos_logic.get_pedidos(cliente_ruc, estado, limite)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return resultado


# ===========================================================================
# 4. Crédito
# ===========================================================================
@app.get("/credito/{cliente_ruc}", dependencies=[Depends(verify_api_key)])
async def credito(cliente_ruc: str):
    resultado = clientes_logic.get_credito(cliente_ruc)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return resultado


# ===========================================================================
# 5. Cobranzas
# ===========================================================================
@app.get("/cobranzas/{cliente_ruc}", dependencies=[Depends(verify_api_key)])
async def cobranzas(cliente_ruc: str, estado: str = None):
    resultado = clientes_logic.get_cobranzas(cliente_ruc, estado)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return resultado


# ===========================================================================
# 6. Documentos
# ===========================================================================
@app.get("/documentos/{cliente_ruc}", dependencies=[Depends(verify_api_key)])
async def documentos(cliente_ruc: str,
                     tipo: str = Query(None, regex="^(factura|guia)$")):
    resultado = clientes_logic.get_documentos(cliente_ruc, tipo)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return resultado


# ===========================================================================
# 7. Perfil de cliente
# ===========================================================================
@app.get("/clientes/{ruc}", dependencies=[Depends(verify_api_key)])
async def cliente(ruc: str):
    resultado = clientes_logic.get_perfil(ruc)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return resultado


# ===========================================================================
# 8. Historial de compras
# ===========================================================================
@app.get("/historial/{cliente_ruc}", dependencies=[Depends(verify_api_key)])
async def historial(cliente_ruc: str, meses: int = 18):
    resultado = pedidos_logic.get_historial(cliente_ruc, meses)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return resultado


# ===========================================================================
# 9. Vehículo por placa o VIN
# ===========================================================================
@app.get("/vehiculo/{placa_o_vin}", dependencies=[Depends(verify_api_key)])
async def vehiculo(placa_o_vin: str):
    resultado = productos_logic.buscar_vehiculo(placa_o_vin)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return resultado


# ===========================================================================
# 10. Catálogo / búsqueda de productos
# ===========================================================================
@app.get("/catalogo", dependencies=[Depends(verify_api_key)])
async def catalogo(q: str = None, categoria: str = None,
                   marca: str = None, con_stock: bool = False):
    return productos_logic.buscar_catalogo(q, categoria, marca, con_stock)


# ===========================================================================
# 11. Cartera de clientes por vendedor
# ===========================================================================
@app.get("/vendedor/{vendedor_id}/clientes",
         dependencies=[Depends(verify_api_key)])
async def cartera_vendedor(vendedor_id: str, estado: str = None,
                           tipo: str = None):
    resultado = vendedores_logic.get_cartera(vendedor_id, estado, tipo)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Vendedor no encontrado")
    return resultado
