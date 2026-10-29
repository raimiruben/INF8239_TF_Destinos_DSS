# Datos · mecanismo de obtención

**Fuente:** Huda, C. (2023). *Tourism Dataset* (Version 1). Mendeley Data. https://doi.org/10.17632/h58s544674.1
Página: https://data.mendeley.com/datasets/h58s544674/1

**Licencia / condiciones:** el autor lo publica para investigación (turismo y soft computing) y **no para fines
comerciales**. Por eso los archivos crudos **no se versionan** en este repositorio (`.gitignore`), se citan y se
descargan desde la fuente.

## Pasos

1. Descargar las 9 tablas desde la página de Mendeley.
2. Copiarlas a `data/raw/` con estos nombres exactos:
   `City.xlsx, Continent.xlsx, Country.xlsx, Item.xlsx, Mode.xlsx, Region.xlsx, Transaction.xlsx, Type.xlsx, User.xlsx`
3. Ejecutar `uv run python scripts/prepare_data.py`. Si el contrato falla, el script se detiene con la lista de problemas.

## Huellas de la versión usada (SHA-256, primeros 16 caracteres)

| Tabla | SHA-256 |
|---|---|
| Transaction.xlsx | cf4d4f49402d9528 |
| Item.xlsx | 3cfbd728c8660e87 |
| User.xlsx | 5aebe6b97555657c |
| Type.xlsx | 3e1888d2df751921 |
| Mode.xlsx | c33a3ad697ba3462 |
| Continent.xlsx | 9c0ac1969bb6cb8a |
| Region.xlsx | ba41584a40c0fdbd |
| Country.xlsx | 14fcf2afb03b865c |
| City.xlsx | 44db59401944ffb6 |

`reports/data_audit.json` registra estas huellas en cada ejecución: si cambian, la versión de los datos cambió.

## Hallazgo del contrato

`Item.AttractionCityId` toma los valores 1, 2 y 3, pero **no es llave de la tabla `City`** (allí `CityId = 1` es
Douala, Camerún). Por los nombres y direcciones de las atracciones se mapea 1 = Bali, 2 = Malang, 3 = Yogyakarta
(`ATTRACTION_CITY_MAP` en `src/tourism_dss/data.py`), y la prueba `test_contract_accepts_valid_data_and_maps_cities`
lo protege.
