# Validación técnica de acceso — v0.4.1

Fecha local: 20/10/2026, America/Lima. Las solicitudes Python ocurrieron el 21/10/2026 a las 00:15–00:16 UTC (19:15–19:16 del día anterior en Lima).

## Resultado ejecutivo

**No hay un canal de actualización automática técnicamente confirmado en esta ejecución.** Se confirmaron declaraciones documentales oficiales mediante su contenido indexado, pero no una respuesta de datos ni un contrato API completo. Esto no demuestra inexistencia de APIs ni indisponibilidad universal.

Se leyeron `AUDITORIA_FUENTES_V04.md` y `MATRIZ_FUENTES_V04.json`. Se examinaron las dos fichas oficiales indicadas y se intentó un GET acotado al PDF de política pública identificado previamente. No se probaron rutas inventadas, endpoints internos, formularios, credenciales ni variantes de hosts para evitar bloqueos. Resultados no oficiales devueltos por el buscador, incluido un proxy de terceros, se descartaron: no fueron abiertos ni utilizados como evidencia.

Registro estructurado: [RESULTADOS_ACCESO_V041.json](RESULTADOS_ACCESO_V041.json).

## URLs y resultados de acceso

| Recurso exacto | Procedencia | Observación actual | Clasificación |
|---|---|---|---|
| [Ficha OECE Datos Abiertos](https://www.gob.pe/14272-acceder-al-portal-de-datos-abiertos-del-osce) | URL solicitada por el usuario | La herramienta web informó HTTP 418. No expuso cabeceras, tamaño ni cuerpo original. Sin reintento por otro transporte. | Acceso directo no comprobado; bloqueo observado |
| [Ficha Contrataciones Abiertas OCDS](https://www.gob.pe/52005-acceder-al-portal-de-contrataciones-abiertas-de-la-compra-publica) | URL solicitada por el usuario | La herramienta web informó HTTP 418. Sin cabeceras/tamaño disponibles. Sin reintento directo. | Acceso directo no comprobado; bloqueo observado |
| [Ficha OECE en índice oficial](https://www.gob.pe/14272-acceder-al-portal-de-datos-abiertos-del-oece) | Resultado oficial de búsqueda, misma ficha 14272 | Texto indexado recuperado; no GET a esta variante. Cambio editorial indicado: 19/05/2026. | Contenido documental confirmado en índice; acceso operativo no comprobado |
| [Política de publicación PDF](https://contratacionesabiertas.osce.gob.pe/downloads/politica_publicacion.pdf) | Evidencia E06 de v0.4; archivo documental público, no dataset | GET Python sin redirecciones: fallo DNS `getaddrinfo failed` tanto en sandbox como en repetición autorizada. No se obtuvo respuesta HTTP. | No comprobado |

El código 418 es el comunicado por la herramienta web; no se puede atribuir con certeza al servidor de origen en lugar de un intermediario. Un fallo DNS no es HTTP 403, 404 ni 502. No se trasladaron los códigos de v0.4 como resultados actuales.

**URLs exactas de archivos identificadas:** únicamente el PDF documental anterior en el ámbito revisado. **URLs exactas de datasets pequeños verificadas: ninguna. Endpoints API exactos documentados y verificables recuperados: ninguno.** La ausencia de rutas en esta revisión se debe a acceso/documentación insuficientes, no autoriza deducir `/api`, `/release`, `/record`, Swagger ni rutas de descarga.

## Protocolo y límites aplicados

- Dos intentos de lectura con la herramienta web, uno por ficha. La herramienta no ofrece una traza HTTP cruda: no se presentan como capturas de cabeceras GET.
- GET Python explícito al PDF conocido, con tiempo de espera de 15 segundos, sin almacén de cookies, sin autorización y sin seguir redirecciones. Un intento inicial y una repetición fuera del sandbox tras autorización, motivada por fallo de resolución local. Ambos fallaron antes de recibir HTTP.
- Límite previsto de archivo: 1 MiB; lectura máxima de 1 MiB + 1 byte para detectar exceso. Solo se habría guardado una respuesta 200 con MIME PDF, firma `%PDF-` y tamaño admitido. No hubo lectura de cuerpo ni descarga masiva.
- Tras los errores no se cambió de hostname, IP, agente de usuario o proxy para obtener acceso. No se utilizó el enlace CONOSCE con parámetros de credenciales identificado en v0.4.
- No se descargó archivo alguno a `data/raw/v041_prueba/`: no se obtuvo un recurso elegible. SHA-256 de muestra = null; no se creó una muestra artificial ni se sustituyó por fixture.

Trazas Python: [intento restringido](v041_get_politica.json) y [repetición autorizada](v041_get_politica_autorizado.json). Se registran solo cabeceras pertinentes, nunca cookies. Al no existir respuesta, tipo de contenido, tamaño total, `Last-Modified`, `ETag` y fecha de servidor permanecen desconocidos; cero bytes leídos no significa archivo vacío.

## Qué documentan las fichas oficiales

La [ficha OECE 14272 indexada](https://www.gob.pe/14272-acceder-al-portal-de-datos-abiertos-del-oece) declara datos desde 2018, conjuntos de PAC, convocatorias/adjudicaciones y otros registros. Indica actualización mensual dentro de los cinco primeros días y excluye procedimientos en marcha o con adjudicación incompleta. La fecha editorial de la ficha no es fecha de corte de los archivos. No se verificaron formatos concretos actuales, particiones, límites de descarga, paginación ni licencia específica.

La [ficha OCDS 52005 indexada](https://www.gob.pe/52005-acceder-al-portal-de-contrataciones-abiertas-de-la-compra-publica) anuncia descargas y documentación agrupada en **Release**, **Record** y **Files**. Son nombres de categorías, no rutas API. Describe búsquedas por palabras, entidades, periodos, etapas y procedimientos; no demuestra nombres de parámetros ni filtros incrementales de API. Señala cambio editorial 25/08/2025. No permite comprobar autenticación, cuotas, licencia exacta, tamaño, fechas de datos o paginación técnica. La frecuencia diaria citada en v0.4 procede de otra evidencia histórica y **no se revalidó** aquí.

## Aptitud por caso de uso

| Canal | Histórico | Convocatorias vigentes | Oportunidad comercial |
|---|---|---|---|
| OECE Datos Abiertos | Candidato condicionado: disponibilidad documental, sin archivo validado | Inadecuado como única fuente: la propia ficha excluye procesos en marcha | Útil potencialmente para patrones de compra, mercado y planificación PAC; no demuestra plazo abierto para ofertar |
| OCDS | Candidato condicionado por muestra, esquema, licencia y acceso | No comprobado: revisar etapas efectivas, corte, latencia, estado y cronograma en datos reales | Potencial tras comprobar fechas y cobertura; no se puede activar alertas de oportunidades con la evidencia actual |

**OCDS no equivale a cobertura completa de PLADICOP.** No se verificó inclusión de contratos menores, mapeo de `idContrato`, cobertura nacional ni equivalencia de estados. Un dato histórico o planificado no se convierte en convocatoria vigente por estar publicado en formato abierto.

## Recomendación para v0.4.2 (sin implementación)

Primer candidato: **conector de archivos oficiales OECE para histórico/PAC**, inicialmente con recepción local y manifiesto de procedencia. Es una propuesta condicionada, no un conector automatizado aprobado técnicamente. Los cortes tabulares son más adecuados para validar esquema, claves y comparación de instantáneas sin depender de un contrato API todavía inaccesible.

Antes de automatizar adquisición se requiere:

1. Un enlace exacto público de dataset pequeño y su diccionario, publicado por el editor; respuesta 200 sin credenciales, MIME/formato real y tamaño acotado.
2. Política/licencia aplicable y condiciones de acceso automatizado, sin deducirlas del nombre «datos abiertos».
3. Identificadores estables, fecha de corte, granularidad y método para detectar correcciones; decidir snapshot mensual o delta solo con evidencia.
4. Prueba aislada de idempotencia y reconciliación; hash de bytes, URL, captura, versión de parser, rechazos y cobertura. No avanzar marcas de agua con lotes incompletos.

Para OCDS, conseguir primero documentación oficial completa con URLs exactas, versiones, paginación, filtros, límites y esquema de entregas. Solo entonces ensayar un GET mínimo permitido; no implementar exploración de rutas. Mientras tanto, **ninguna de las dos fuentes queda habilitada para actualización automática**. La recomendación de recepción local permite avanzar sin sustituir esta validación pendiente.

## Pruebas y conservación

Se ejecutó:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=data/pytest-v041-temp -o cache_dir=data/pytest-v041-cache
```

Resultado y comprobaciones de hashes/SQLite constan en `RESULTADOS_ACCESO_V041.json`. Se comparan contra [v041_integridad_antes.json](v041_integridad_antes.json). SQLite se inspecciona con `mode=ro`, sin migraciones ni importaciones. Solo se añadieron documentos de auditoría y archivos temporales de pruebas dentro del proyecto. No se modificaron importadores, configuración ni bases existentes; no se publicó en GitHub.
