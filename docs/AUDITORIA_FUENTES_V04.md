# Auditoría técnica y documental de fuentes — v0.4

Fecha de revisión: **2026-10-20**, America/Lima. Alcance: preparación documental; no se implementa adquisición ni actualización incremental. Base funcional: v0.3, 18 pruebas. No se modifican importadores, configuración operativa ni bases existentes.

## Dictamen

La actualización nacional requiere canales distintos para oportunidades, planificación e histórico. Hay documentación oficial de datos abiertos PAC/procedimientos y de publicación OCDS; no se ha verificado una API pública utilizable de contratos menores ni un conjunto CMN nacional consolidado. La página CMN configurada corresponde a publicaciones del MEF y no demuestra cobertura de todas las entidades. No se puede declarar listo un recolector nacional ni garantizar actualidad de oportunidades con las descargas históricas.

El acceso web estuvo **parcialmente disponible**. Se consultaron páginas informativas y documentos públicos mediante búsqueda/lectura, sin automatizar formularios del portal ni llamar APIs de datos. No se utilizaron credenciales, cookies suministradas, tokens ni sesiones privadas. No se eludieron bloqueos. Resultados indexados pueden estar desactualizados: la fecha de consulta no equivale a fecha de actualización de datos.

## Clasificación de evidencia

- **V-DIRECTA:** contenido oficial recuperado directamente por la herramienta web. No equivale a certificar operación continua.
- **V-DOCUMENTAL-INDEXADA:** declaración de un editor oficial recuperada del índice de búsqueda; acceso directo bloqueado o no ensayado. Verifica una declaración, no un endpoint operativo.
- **V-LOCAL:** contrato de datos o comportamiento comprobable en el proyecto; no demuestra cobertura externa.
- **PENDIENTE:** no verificado. No significa que una capacidad no exista.
- **PROPUESTA:** decisión de arquitectura por validar; no es una propiedad del proveedor.

Matriz estructurada: [MATRIZ_FUENTES_V04.json](MATRIZ_FUENTES_V04.json). Los identificadores E01–E10 remiten al registro de evidencias de este documento.

## Matriz de fuentes

| Fuente y canal | Acceso y formatos | Paginación y filtros | Actualización declarada | API / reutilización / limitación |
|---|---|---|---|---|
| Contratos menores PLADICOP, OECE [E01, E02] | Buscador público sin credenciales según E01. Manual PDF publicado. JSON local confirmado; exportación JSON oficial no demostrada. | V-LOCAL: `data`, `pageable.pageNumber/pageSize/totalElements`. Base cero/uno no fijada globalmente. Filtros actuales y límites externos pendientes. | No se verificó periodicidad ni SLA. | API pública documentada no localizada. Acceso ciudadano no autoriza inferir API o descarga masiva. E01 describe uso facultativo en su texto: alcance efectivo y vigencia normativa pendientes; no presumir universo nacional completo. |
| PAC, OECE: buscador + datos abiertos [E03, E04, E06] | Consulta pública de planificación e históricos; descargas oficiales declaradas. Excel descrito en política histórica; archivo y diccionario vigentes pendientes. | Consulta: entidad, año, ubigeo; procesos por tipo y financiamiento. No se verificó paginación técnica, límites ni filtros del archivo descargable. | E03: mensual, primeros cinco días del mes, para el portal de datos abiertos; no extrapolar al buscador. | No se verificó API PAC específica. No confundir plantilla Excel de carga con exportación nacional. PAC es planificación, no convocatoria abierta. |
| CMN, MEF y publicaciones de cada entidad [E08, E09] | Índice HTML y PDF del MEF recuperados. No se verificó exportación nacional CSV/XLSX/JSON. | Índice por años 2022–2026; PDF 2026–2028 de 156 páginas. Páginas PDF no son paginación API. | Publicaciones por periodo; frecuencia de modificaciones y SLA no verificados. | No se verificó API nacional pública ni catálogo exhaustivo. El PDF examinado identifica MEF-Administración General, no todas las entidades. |
| Procedimientos: OCDS y buscador público SEACE [E05, E06, E07, E10] | OCDS: CSV/XLSX/JSON y SHA anunciados; función concreta del SHA pendiente. Buscador ciudadano sin usuario según E07. | Política: origen, identificador de entrega, OCID y expediente; buscador: entidad, año, tipo, fecha/objeto. Parámetros API, cursor y límites pendientes. | Política histórica E06: OCDS diario; cumplimiento actual no medido. Portal tabular E03: mensual y excluye procedimientos en marcha o con adjudicación incompleta. | E05 anuncia documentación API, pero especificación, autenticación, cuotas y operación no verificadas. Descargas OECE devolvieron 403. La disponibilidad histórica no prueba cobertura 2026. |

## Registro de evidencias verificables

Todas las observaciones se efectuaron el 2026-10-20. No se guardaron copias íntegras de páginas externas; se registran URL, método y hallazgo para reproducir la revisión. Las fechas editoriales siguientes proceden de las páginas/indexación, no de una medición de frescura.

| ID | URL oficial | Método y resultado | Hallazgo acotado |
|---|---|---|---|
| E01 | [Gestionar Contratos Menores](https://www.gob.pe/70088) | V-DOCUMENTAL-INDEXADA; último cambio mostrado 25/05/2026 | Distingue buscador ciudadano sin credenciales de accesos de entidades/proveedores. Describe carácter facultativo del uso bajo una condición transitoria. No se hizo interpretación legal de obligatoriedad actual. |
| E02 | [Manual ciudadano de contratos menores](https://www.gob.pe/institucion/oece/informes-publicaciones/6977065-manual-de-usuario-del-buscador-publico-de-contratos-menores-para-ciudadanos-vigente) | V-DOCUMENTAL-INDEXADA, publicación 21/07/2025; apertura directa 418 | Identifica manual v1.2 PDF. No se recuperó su contenido completo: filtros y paginación de esta versión pendientes. |
| E03 | [Datos abiertos OECE](https://www.gob.pe/es/14272-acceder-al-portal-de-datos-abiertos-del-oece) | V-DOCUMENTAL-INDEXADA, cambio 19/05/2026; apertura directa 418 | Incluye PAC y contrataciones desde 2018; declara frecuencia mensual dentro de primeros cinco días y exclusión de procedimientos en marcha/adjudicación incompleta. No se comprobaron archivos actuales. |
| E04 | [Consulta PAC](https://www.gob.pe/8190-consultar-el-plan-anual-de-contrataciones-pac-de-las-entidades-publicas) | V-DOCUMENTAL-INDEXADA, cambio 18/06/2026 | Consulta planificación actual e histórica, versiones de PAC y filtros descritos en la matriz. |
| E05 | [Servicio OCDS](https://www.gob.pe/52005-acceder-al-portal-de-contrataciones-abiertas-de-la-compra-publica) | V-DOCUMENTAL-INDEXADA; apertura directa 418 | Declara publicación OCDS y sección de documentación API. No se leyó una especificación OpenAPI ni se ensayaron endpoints. |
| E06 | [Política de publicación, dominio OSCE](https://contratacionesabiertas.osce.gob.pe/downloads/politica_publicacion.pdf) | V-DOCUMENTAL-INDEXADA; apertura directa 502 | Describe OCDS diario, información complementaria mensual en Excel, filtros y descargas CSV/XLSX/JSON/SHA. Documento de dominio anterior: vigencia y equivalencia con OECE pendientes. |
| E07 | [Buscador de procedimientos](https://www.gob.pe/8192-buscar-procedimientos-de-seleccion-de-entidades-publicas) | V-DOCUMENTAL-INDEXADA | Declara acceso público sin usuario y criterios de consulta. No se operó el buscador. |
| E08 | [Índice CMN MEF configurado](https://www.mef.gob.pe/es/tributos-sp-30710/614-home/detallpcontrataciones/7276-cuadro-multianual-de-necesidades) | V-DIRECTA | Lista años y enlaza documentos CMN. Que el host sea MEF no convierte la publicación institucional en un agregado nacional. |
| E09 | [CMN 2026–2028 MEF](https://www.mef.gob.pe/contenidos/abastecimiento/normas/CMN_2026_2028.pdf) | V-DIRECTA; texto PDF, 156 páginas | Encabezados identifican MEF-Administración General, número 46, fecha 06/01/2026. Se verificó alcance institucional; no se extrajeron filas a la base. |
| E10 | [Anuncio oficial OCDS](https://www.gob.pe/institucion/oece/noticias/884163-osce-implementa-el-estandar-de-datos-para-las-contrataciones-abiertas-ocds) | V-DOCUMENTAL-INDEXADA; anuncio histórico | Anuncia formatos y disponibilidad histórica 2004–2023. No demuestra que el corte actual llegue a 2026. |

Evidencia local adicional: `config/sources.json`, `docs/PLAN_MVP.md`, `docs/IMPORTADOR_PLADICOP.md`, `docs/COBERTURA_PLADICOP.md`, esquema y pruebas existentes. La configuración conserva estados pendientes y el README aún describe v0.1; son documentos operativos anteriores, no prueba de una verificación externa. Esta auditoría los complementa sin alterar configuración ni ejecutar `audit_sources.py` (ese script escribe en SQLite).

## Bloqueos y verificaciones pendientes

| Bloqueo | Consecuencia | Evidencia necesaria para resolverlo |
|---|---|---|
| 403 al leer `https://contratacionesabiertas.oece.gob.pe/descargas`; 418 en páginas Gob.pe indicadas; 502 en PDF OSCE | No se validó descarga actual, diccionario, licencia o contrato API completo. Los códigos corresponden a esta herramienta, no prueban caída universal ni autenticación obligatoria. | Documentación/archivos públicos accesibles o copias obtenidas manualmente con procedencia. No eludir restricciones. |
| El índice de búsqueda devolvió un enlace de CONOSCE con parámetros de usuario/contraseña | No se abrió ni se utilizó ese enlace, aunque se anunciara público; no se incluyen valores en la matriz. | Ruta documental o descarga pública que no requiera parámetros de credenciales. |
| Sin especificación API PLADICOP/PAC/CMN verificada | No diseñar llamadas a endpoints internos a partir del JSON local. | Documentación pública del editor: alcance, parámetros, autenticación, límites y política de uso. |
| Sin muestras actuales de PAC/OCDS ni licencia comprobada | Formatos anunciados no validan columnas, tipos, estabilidad de IDs o permiso concreto de redistribución. | Archivo, diccionario, licencia y corte publicados; comprobación local aislada. |
| Sin directorio CMN nacional ni denominador validado de entidades | No es medible la cobertura nacional CMN. | Catálogo oficial de entidades/unidades ejecutoras con versión y publicaciones por entidad/periodo. |
| Sin evidencia de filtros/snapshot común entre páginas | Reunir páginas puede mezclar consultas o momentos. | Manifiesto de filtros, orden y captura; límites y semántica de paginación documentados. |

No se afirma que APIs no encontradas sean inexistentes. Tampoco se aplica a la versión actual un manual de contratos menores localizado como «fase de prueba v1.0»: fue descartado para confirmar filtros vigentes.

## Arquitectura propuesta, no implementada

Flujo: **registro de fuentes → recepción de archivos autorizados → almacén original inmutable → validación y cuarentena → normalización por fuente → versiones y relaciones → vistas y alertas con cobertura/frescura**.

1. **Registro y adquisición.** Mantener por canal editor, URL documental, URL de recurso, licencia comprobada, versión de diccionario, alcance y evidencia. PLADICOP continúa con entrega manual local. PAC/OCDS priorizan descargas oficiales documentadas; una API solo se habilitaría tras verificar su contrato público. CMN comienza con inventario institucional, sin suponer repositorio nacional. No se implementan planificadores ni conectores en v0.4.
2. **Trazabilidad.** Manifiesto por adquisición: fuente, URL original, ruta, SHA-256 de bytes, tamaño, MIME observado, fecha de captura UTC y America/Lima, fecha de publicación/corte separada, filtros explícitos, páginas, totales declarados, lote, versión del parser y licencia. Preservar bytes y metadatos aun si hay rechazo. Diferenciar `observed_at`, `source_updated_at` y plazo contractual; una modificación del archivo local no prueba actualización del proveedor.
3. **Claves y deduplicación.** PLADICOP conserva `(fuente, idContrato)`. Para OCDS, evaluar `(publicador, ocid)` como proceso y `(publicador, ocid, release.id)` como entrega después de revisar el diccionario; conservar `release.date` y hash. Para PAC validar ID nativo; entidad+año+referencia de ítem es solo candidato. CMN: entidad/unidad ejecutora+periodo+documento/versión y fila/ítem, sin deduplicar solo por descripción. No equiparar RUC, pliego y unidad ejecutora. Relaciones PAC–proceso–contrato separadas, con evidencia y confianza; no fusionar por similitud textual.
4. **Cambios.** Separar hash del archivo y hash de contenido normalizado. Registrar versiones inmutables, campos cambiados, primera/última observación y procedencias múltiples. Reejecutar un lote no debe duplicar versiones. Conflictos de un mismo ID sin orden temporal demostrable permanecen en cuarentena; ninguna regla de «último nombre de archivo gana». Ausencia en una página no causa borrado; una baja exige evento explícito o reconciliación de una captura completa comparable.
5. **Incrementalidad.** Usar marca de agua de modificación del origen solo si existe y está documentada; confirmar lote y cobertura antes de avanzar. Releer una ventana solapada y reconciliar particiones históricas para correcciones tardías. Si no existe fecha de modificación fiable, comparar instantáneas completas por partición y hash. Filtros y orden determinista forman parte de la identidad de la captura. Un fallo conserva el checkpoint anterior y permite reintento idempotente.
6. **Cadencias propuestas.** PAC: revisión mensual tras la ventana declarada, con relectura del año y versiones anteriores. OCDS: evaluar recepción diaria únicamente cuando se confirme disponibilidad y permiso; reconciliación mensual de particiones antiguas. PLADICOP: lotes manuales según necesidad, sin promesa de tiempo real. CMN: revisión mensual del inventario y refuerzo durante aprobación/modificaciones, no una frecuencia atribuida al MEF. Ventanas y costes se ajustan después de medir volumen y latencia.
7. **Escala nacional.** Particionar por fuente/periodo y, donde proceda, entidad. Guardar archivos inmutables por hash; una cola con reintentos y límites documentados sería posterior. SQLite continúa para pruebas; evaluar PostgreSQL y almacenamiento de objetos con mediciones, sin migración ahora. Versionar un padrón oficial de entidades y medir por nivel de gobierno, ámbito geográfico, entidad y periodo; el domicilio de una entidad no equivale al lugar de ejecución.
8. **Calidad y publicación.** Medir filas recibidas, válidas, IDs únicos, duplicados, conflictos, páginas observadas/faltantes, cobertura de entidades con denominador versionado y latencia de publicación/captura. Separar planificación PAC/CMN de convocatorias y adjudicaciones. Horas hasta cierre se calculan a la ejecución; `cotizar=false` no se traduce en inelegibilidad. Mostrar datos incompletos/desactualizados sin inventar vigencia.

## Criterios para la siguiente implementación

- Obtener y validar una muestra oficial actual y su diccionario/licencia por canal, en base de pruebas.
- Verificar IDs, versiones, fechas, filtros, límites, formato y cobertura de periodos; documentar resultados reproducibles antes de programar un conector.
- Resolver la diferencia OSCE/OECE por enlaces oficiales, sin asumir que cambiar el hostname mantiene contratos de API.
- Definir padrón nacional y reglas de correspondencia de entidades; publicar cobertura parcial mientras falte evidencia.
- Aprobar un canal de adquisición permitido y una política de frescura por fuente. Mantener la entrada manual para cualquier canal bloqueado.

## Pruebas y preservación

Se ejecutaron las **18 pruebas existentes**, sin añadir ni modificar tests: **18 passed in 1.79s**.

```powershell
.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=data/test-cache-v04 --basetemp=data/test-tmp-v04-01
```

Los temporales y caché se escriben dentro del proyecto; para repetir, usar otro directorio temporal de pruebas. Se registraron hashes previos en [v04_integridad_antes.json](v04_integridad_antes.json) y comparación posterior en [v04_validacion.json](v04_validacion.json). El comprobante posterior enumera los archivos protegidos y el resultado de integridad SQLite en modo de solo lectura. No se ha publicado en GitHub ni se han tocado otros radares.
