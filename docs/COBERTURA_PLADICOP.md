# Auditoría y consolidación local multipágina

Desde `C:\radar-contrataciones-peru`:

```powershell
.\.venv\Scripts\python.exe scripts\import_pladicop_folder.py tests\fixtures\pladicop_pages\missing_duplicates --db data\pladicop_cobertura_demo.sqlite3 --report-dir data\processed\cobertura_demo
.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=data/test-cache-batch --basetemp=data/test-tmp-batch
```

Para archivos obtenidos manualmente, sustituir la carpeta del ejemplo por una carpeta exclusiva de respuestas de la misma consulta. Se leen únicamente los archivos `.json` del nivel inmediato, incluidos nombres con extensión en mayúsculas. No hay solicitudes HTTP ni navegación. La CLI anterior de un solo archivo conserva su comportamiento.

`--db` es obligatorio: debe apuntar a una base de desarrollo o pruebas, nunca a producción. La base principal `data/radar_contrataciones.sqlite3` y sus alias físicos se rechazan. No es posible identificar automáticamente todas las bases de producción con otros nombres; el operador debe elegir una base separada. Todas las rutas deben permanecer dentro del proyecto. Los reportes no pueden escribirse en la propia carpeta de entrada.

## Métricas e incertidumbre

- `registros_recibidos`: suma de elementos de las listas `data` legibles, incluidos duplicados y filas rechazadas. Un JSON ilegible no aporta una cantidad inventada.
- `ids_unicos`: identificadores enteros/cadenas no vacías observados, incluso si otros campos de esas filas son inválidos. `ids_consolidados` cuenta solamente los contratos válidos y sin conflicto aceptados en el lote.
- `paginas_observadas`, `paginas_repetidas`, `ids_repetidos` y `ids_en_conflicto` describen la evidencia disponible. Las repeticiones incluyen ubicaciones por archivo y fila.
- `total_consistente` existe solo si todos los archivos tienen metadatos válidos y coinciden en `totalElements`. No se confunde con filas recibidas.
- Cobertura estimada: `100 * ids_unicos / total_consistente`, solo con total positivo y sin excederlo. Total cero produce null, no una afirmación de 100%. Es una razón de IDs recibidos, no una validación de contratos ni exhaustividad.
- Los huecos entre páginas observadas se informan incluso con totales contradictorios. Los intervalos son inclusivos y compactos para evitar listas gigantes.
- Se infiere base cero únicamente si se observa página cero. Su ausencia no prueba base uno: se muestran hipótesis cero/uno y sus páginas fuera de rango. No se infiere base uno a partir de una página vacía o una captura potencialmente fuera de rango.
- Solo se calculan páginas esperadas y faltantes respecto del total cuando `totalElements` y `pageSize` son consistentes. Se usa `ceil(totalElements/pageSize)`. Una contradicción de tamaño no impide la razón de IDs si el total sí es consistente.

Los archivos no prueban que compartan filtros, ordenamiento o instante de captura. Incluso 100% puede contener solapamientos, omisiones compensadas por IDs de otras capturas o datos antiguos. No se declara cobertura completa ni se deduce vigencia o elegibilidad.

## Consolidación, trazabilidad y errores

Se reutilizan las tablas v0.2 y sus reglas de validación. Las tablas adicionales `pladicop_batches` y `pladicop_batch_files` vinculan cada lote con los archivos, sus ejecuciones y `pageable` completo. Cada archivo conserva ruta absoluta, hash SHA-256 y bytes originales en `pladicop_imports`; el reporte persistido incluye sus metadatos y errores. Ningún dato ausente de una página provoca borrados.

Los duplicados con el mismo contenido se aplican una sola vez. Si un ID tiene contenidos distintos dentro del lote, todas sus versiones se excluyen y sus filas válidas se registran como rechazos: no se elige una versión por orden, nombre o fecha del archivo. Los contratos existentes quedan intactos para ese ID. Para aplicar una actualización, debe proporcionarse un lote sin versiones contradictorias de ese ID. Repetir el mismo lote no añade versiones al historial; se conserva una nueva observación de procedencia por archivo.

Toda la escritura del lote se realiza en una transacción, incluidas procedencias y rechazos. Un fallo SQLite revierte esos cambios; la creación aditiva de tablas puede permanecer. Los reportes JSON y Markdown se escriben después del commit y también se conserva el reporte JSON en SQLite. Si falla la escritura del reporte externo, los datos ya confirmados siguen disponibles en `pladicop_batches`.

Salida CLI: 0 si no hay errores de archivo ni filas rechazadas (puede haber advertencias de cobertura); 1 si los hay; 2 por errores de rutas o argumentos. Las advertencias siempre deben revisarse.

## Fixtures y resultado de referencia

`tests/fixtures/pladicop_pages/` contiene cinco escenarios sintéticos: `complete`, `missing_duplicates`, `inconsistent`, `ambiguous` y `conflict`. Sus nombres de archivo deliberadamente no siguen el orden de página.

Para `missing_duplicates`: 6 filas recibidas, 4 IDs únicos, páginas `[0, 2]`, página 0 repetida, hueco `[1, 1]`, total declarado 6 y cobertura estimada 66.67%. Primera ejecución: 4 insertados y 2 duplicados omitidos. Segunda: 4 sin cambios y 2 duplicados omitidos, sin nuevas versiones.
