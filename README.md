# tfg-mcp-x402

Prototipo reproducible y local para estudiar la interoperabilidad entre una capacidad MCP y un flujo x402 simulado.

## Estado

Estructura inicial implementada a partir de la arquitectura aprobada. El proyecto está diseñado para funcionar sin pagos reales, wallets, secretos, datos de usuario ni conexiones a facilitators externos.

## Arquitectura

La primera implementación usa un gateway HTTP local como middleware delante de una capacidad MCP determinista:

```text
cliente de prueba -> gateway x402 simulado -> servidor MCP -> SQLite local
                                  -> facilitator simulado
```

El gateway devuelve `402` cuando falta la prueba sintética. Solo reenvía la llamada MCP tras una verificación local válida. El estado de nonces e idempotencia se conserva en SQLite.

## Requisitos

- Python 3.11 o superior.
- `uv`.

## Ejecución

Instalar dependencias y ejecutar las pruebas:

```bash
uv sync
uv run pytest
```

Arrancar el servicio local:

```bash
uv run uvicorn tfg_mcp_x402.app:app --reload
```

La API expone `GET /health`, una frontera JSON-RPC MCP mínima en `POST /mcp` y su variante protegida en `POST /mcp/paid`. Los endpoints REST `POST /mcp/tools/echo` y `POST /mcp/tools/echo/paid` se conservan como línea base auxiliar.

## Seguridad del prototipo

Los importes, identidades, nonces y pruebas son ficticios. El endpoint de pago simulado nunca liquida fondos ni llama a una red externa. No se deben añadir credenciales ni datos personales a la configuración o a los tests.

## Límites

Este proyecto no pretende demostrar compatibilidad universal con MCP/x402, seguridad de producción, rendimiento en producción ni cumplimiento normativo. La arquitectura completa y el protocolo experimental siguen documentados en el repositorio académico de origen y deben mantenerse alineados con la aprobación del TFG.

