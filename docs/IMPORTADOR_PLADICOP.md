# Importador local PLADICOP

Ejecutar desde `C:\radar-contrataciones-peru`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\import_pladicop.py data\archivo_manual.json
.\.venv\Scripts\python.exe -m pytest -q
```

El archivo debe haberse obtenido manualmente. No se consulta el portal ni se utilizan sesiones o credenciales. La CLI usa la base existente `data/radar_contrataciones.sqlite3`; admite `--db`, `--report-dir` y `--upcoming-hours` (72 por defecto). Devuelve 0 al importar sin rechazos, 1 para archivo inválido o rechazos parciales, y 2 para errores de argumentos o lectura.

Prueba con datos sintéticos, en base separada:

```powershell
.\.venv\Scripts\python.exe scripts\import_pladicop.py tests\fixtures\pladicop_five.json --db data\pladicop_demo.sqlite3 --report-dir data\processed\pladicop_demo
```

Las tablas nuevas se crean de forma aditiva: `pladicop_contracts` mantiene una fila por `(source, contract_id)`; `pladicop_history` guarda cada versión aceptada, incluida una reversión a una versión anterior; `pladicop_imports` conserva ruta absoluta, SHA-256, bytes originales completos, fecha de ejecución y reporte; `pladicop_rejections` registra posición (desde 1), motivo y contenido rechazado. Los registros sin cambios actualizan la última procedencia sin añadir versiones. Las tablas anteriores no se modifican. Cada importación de datos es transaccional.

Se exige la presencia de los 22 campos confirmados, pero se conservan sus valores nulos (excepto la clave obligatoria). Los campos adicionales se conservan. `idContrato` acepta entero o cadena; su representación textual identifica el contrato. Duplicados dentro de un archivo se rechazan después de la primera aparición válida. Se validan fechas y tipo booleano/null de `cotizar`; no se inventan catálogos ni tipos para otros campos cuya especificación no está documentada.

Las cuatro fechas se convierten a ISO 8601 con zona IANA `America/Lima`, usando `tzdata` en Windows. Se rechazan fechas imposibles, formatos distintos y horas históricas ambiguas o inexistentes. El JSON de cada registro conserva sus valores originales; los bytes del documento permiten recuperar también su formato original.

Los reportes JSON y Markdown tienen un UUID por ejecución en `data/processed`. Los próximos vencimientos corresponden únicamente a filas válidas del archivo y a cierres futuros dentro de la ventana; no prueban vigencia, etapa habilitada ni elegibilidad. El JSON incluye horas negativas para plazos vencidos y null para fechas ausentes. `cotizar=false` no excluye un registro del cálculo. `pageable` se conserva sin confundir el total remoto con la cantidad leída del archivo; no se descargan otras páginas ni se eliminan contratos ausentes de una página.

Un JSON malformado se registra como error de archivo con cero filas leídas/rechazadas, porque no se puede conocer su cantidad. Si la lista es legible pero la paginación es inválida, se rechazan todas sus filas. Los motivos están disponibles en SQLite. Los reportes incluyen verificación de integridad y claves foráneas. Los temporales de pytest permanecen dentro del proyecto.
