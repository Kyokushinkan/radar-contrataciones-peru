# Panel privado v1.4 — Paso 42

Desde PowerShell, en `C:\radar-contrataciones-peru`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dashboard-v14.txt
.\.venv\Scripts\python.exe -m streamlit run app/dashboard_v14.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

Abrir http://127.0.0.1:8501 en el navegador. Detener con Ctrl+C en la consola.
La instalación requiere descargar paquetes; la consulta del panel no requiere
internet. No instalar globalmente ni desplegar en Community Cloud.

`.streamlit/config.toml` fija loopback, desactiva estadísticas y archivos
estáticos, mantiene protección CORS/XSRF y desactiva el observador de archivos.
Ejecutar desde la raíz para cargar esta configuración. La interfaz rechaza una
dirección distinta de 127.0.0.1 o estadísticas activas. No cambiar estas opciones,
no usar túneles ni proxies públicos. No hay autenticación: el acceso es local.

Solo lee `data/processed/evaluacion_oportunidades_v13.csv`; no conecta a SQLite,
PLADICOP, APIs, recursos gráficos remotos ni proveedores de autenticación.
Las descargas se generan en memoria con los registros filtrados y todas las
columnas originales. El navegador decide dónde guardar el archivo descargado.
Los identificadores se leen como texto, y no se recalculan fechas ni decisiones.

Filtros: Y entre campos y O entre valores de un mismo campo. Búsqueda literal
por código, descripción, entidad o ID; ignora mayúsculas y tildes. La ficha se
limita a los resultados filtrados. El resumen ejecutivo siempre cubre el lote
completo. La revisión documental incluye SENASA revisado con limitaciones.

Los estados sin datos se muestran explícitamente, sin convertirlos en ceros ni
incumplimientos. La afinidad es orientativa. Vigente y ventana_abierta se
presentan únicamente como valores registrados en la captura histórica.

Pruebas: usar una ruta nueva de `--basetemp` dentro del proyecto (pytest limpia
la ruta indicada si ya existe). Se comprueban filtros, descargas, integridad,
interacción Streamlit y ejecución con sockets externos bloqueados durante las
pruebas. Esto no sustituye un cortafuegos del sistema operativo.
