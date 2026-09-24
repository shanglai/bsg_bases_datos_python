-- =====================================================================
-- c4_final_b5_bigquery.sql
-- Sesion final: BigQuery
--
-- Se ejecuta en BigQuery Studio, bloque por bloque.
-- Sustituir PROYECTO por el identificador del proyecto de la clase.
--
-- ADVERTENCIA DE COSTO
--   BigQuery cobra por bytes LEIDOS, no por tiempo ni por filas
--   devueltas. Antes de ejecutar cualquier consulta, el editor muestra
--   arriba a la derecha cuantos bytes va a procesar. Conviene mirarlo
--   siempre: es el precio de esa consulta.
--
--   La tabla de esta clase es pequena (unos 5 MB), de modo que ninguna
--   consulta de aqui cuesta de forma apreciable. La disciplina de mirar
--   el estimado es lo que se esta enseñando.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Bloque A. Que es distinto aqui
-- ---------------------------------------------------------------------

-- A1. La tabla y su forma.
SELECT
  table_name,
  ddl
FROM `PROYECTO.pagos.INFORMATION_SCHEMA.TABLES`
WHERE table_name = 'operaciones';

-- A2. Las columnas, incluidas las anidadas.
--     Notese la notacion de punto en column_name para las subcolumnas.
SELECT
  field_path,
  data_type
FROM `PROYECTO.pagos.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
WHERE table_name = 'operaciones'
ORDER BY field_path;

-- A3. Tamano y numero de filas, sin leer la tabla.
--     Estos metadatos no cuestan: BigQuery los tiene aparte.
SELECT
  table_name,
  row_count,
  ROUND(size_bytes / 1024 / 1024, 2) AS mb
FROM `PROYECTO.pagos.__TABLES__`
WHERE table_id = 'operaciones';


-- ---------------------------------------------------------------------
-- Bloque B. El costo se paga por columna leida
--
-- Es la diferencia mas practica contra PostgreSQL. BigQuery almacena
-- por columnas: leer una columna no lee las demas.
-- ---------------------------------------------------------------------

-- B1. Una sola columna.
--     Mirar el estimado de bytes antes de ejecutar.
SELECT COUNT(*) AS operaciones
FROM `PROYECTO.pagos.operaciones`;

-- B2. Dos columnas.
SELECT estatus, COUNT(*) AS operaciones
FROM `PROYECTO.pagos.operaciones`
GROUP BY estatus;

-- B3. Todas las columnas. Comparar el estimado con B2.
SELECT *
FROM `PROYECTO.pagos.operaciones`
LIMIT 10;

-- Observacion que conviene registrar:
--   SELECT * es caro en BigQuery aunque lleve LIMIT. El LIMIT recorta
--   lo que se devuelve, NO lo que se lee. En PostgreSQL, un LIMIT sobre
--   un indice si evita leer.
--
--   Regla que se llevan: en BigQuery se nombran las columnas, siempre.


-- ---------------------------------------------------------------------
-- Bloque C. Columnas con subcolumnas
--
-- Lo que en el modelo relacional serian tablas separadas, aqui vive
-- dentro de la fila. Se accede con notacion de punto.
-- ---------------------------------------------------------------------

-- C1. Acceso a subcolumnas.
SELECT
  id_transaccion,
  comercio.nombre,
  comercio.ciudad,
  tarjeta.marca
FROM `PROYECTO.pagos.operaciones`
LIMIT 10;

-- C2. Agrupacion sobre una subcolumna, sin combinar nada.
--     En PostgreSQL esto necesitaba dos JOIN.
SELECT
  comercio.nombre AS comercio,
  COUNT(*) AS operaciones,
  SUM(monto) AS importe
FROM `PROYECTO.pagos.operaciones`
WHERE estatus = 'APROBADA'
GROUP BY comercio
ORDER BY importe DESC;

-- C3. Anidamiento de tres niveles.
SELECT
  autorizacion.emisor.nombre AS emisor,
  COUNT(*) AS operaciones,
  ROUND(AVG(autorizacion.emisor.tiempo_respuesta_ms), 0) AS respuesta_ms
FROM `PROYECTO.pagos.operaciones`
GROUP BY emisor
ORDER BY operaciones DESC;

-- C4. Construir una subcolumna al vuelo, con STRUCT.
SELECT
  id_transaccion,
  STRUCT(comercio.nombre AS nombre, comercio.ciudad AS ciudad) AS lugar
FROM `PROYECTO.pagos.operaciones`
LIMIT 5;


-- ---------------------------------------------------------------------
-- Bloque D. Columnas repetidas
--
-- autorizacion.riesgo.senales es un ARRAY: varios valores en una sola
-- columna. En el modelo relacional habria sido una tabla de detalle.
-- ---------------------------------------------------------------------

-- D1. El arreglo, tal como esta.
SELECT
  id_transaccion,
  autorizacion.riesgo.senales
FROM `PROYECTO.pagos.operaciones`
WHERE ARRAY_LENGTH(autorizacion.riesgo.senales) > 0
LIMIT 5;

-- D2. Expandir el arreglo a filas, con UNNEST.
--     Es el equivalente de $unwind de MongoDB y de
--     jsonb_array_elements de PostgreSQL.
SELECT
  senal,
  COUNT(*) AS veces
FROM `PROYECTO.pagos.operaciones`,
     UNNEST(autorizacion.riesgo.senales) AS senal
GROUP BY senal
ORDER BY veces DESC;

-- D3. La trampa: UNNEST descarta las filas con arreglo vacio.
--     Es el mismo comportamiento de $unwind de la sesion 3.2.
SELECT
  (SELECT COUNT(*) FROM `PROYECTO.pagos.operaciones`) AS filas_totales,
  (SELECT COUNT(*) FROM `PROYECTO.pagos.operaciones`,
          UNNEST(autorizacion.riesgo.senales) AS s) AS tras_unnest;

-- D4. Conservar las filas sin senales, con LEFT JOIN UNNEST.
SELECT COUNT(*) AS conservando_vacios
FROM `PROYECTO.pagos.operaciones`
LEFT JOIN UNNEST(autorizacion.riesgo.senales) AS senal;

-- D5. Trabajar sobre el arreglo sin expandirlo.
SELECT
  id_transaccion,
  ARRAY_LENGTH(autorizacion.riesgo.senales) AS cuantas_senales
FROM `PROYECTO.pagos.operaciones`
WHERE ARRAY_LENGTH(autorizacion.riesgo.senales) >= 3
ORDER BY cuantas_senales DESC
LIMIT 10;

-- D6. Filtrar por pertenencia, sin expandir.
SELECT COUNT(*) AS con_geo_inusual
FROM `PROYECTO.pagos.operaciones`
WHERE 'geo_inusual' IN UNNEST(autorizacion.riesgo.senales);


-- ---------------------------------------------------------------------
-- Bloque E. Particiones
--
-- La tabla esta particionada por dia sobre fecha_hora. Filtrar por esa
-- columna hace que BigQuery lea SOLO las particiones necesarias, y eso
-- se refleja de forma directa en el costo.
-- ---------------------------------------------------------------------

-- E1. Sin filtro de fecha: lee todas las particiones.
SELECT COUNT(*) AS operaciones, SUM(monto) AS importe
FROM `PROYECTO.pagos.operaciones`
WHERE estatus = 'APROBADA';

-- E2. Con filtro de fecha: lee un mes.
--     Comparar el estimado de bytes con E1.
SELECT COUNT(*) AS operaciones, SUM(monto) AS importe
FROM `PROYECTO.pagos.operaciones`
WHERE estatus = 'APROBADA'
  AND fecha_hora >= '2026-03-01'
  AND fecha_hora <  '2026-04-01';

-- E3. El error que anula la particion: aplicar una funcion a la columna.
--     Es exactamente el mismo fenomeno de la sesion 2.5 con DATE().
SELECT COUNT(*) AS operaciones
FROM `PROYECTO.pagos.operaciones`
WHERE DATE(fecha_hora) BETWEEN '2026-03-01' AND '2026-03-31';

-- E4. La version que si aprovecha la particion.
SELECT COUNT(*) AS operaciones
FROM `PROYECTO.pagos.operaciones`
WHERE fecha_hora >= '2026-03-01'
  AND fecha_hora <  '2026-04-01';

-- E5. Que particiones existen y cuanto ocupa cada una.
SELECT
  partition_id,
  total_rows,
  ROUND(total_logical_bytes / 1024, 1) AS kb
FROM `PROYECTO.pagos.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'operaciones'
ORDER BY partition_id
LIMIT 20;


-- ---------------------------------------------------------------------
-- Bloque F. Agrupamiento
--
-- La tabla esta agrupada por estatus y metodo_captura. El agrupamiento
-- ordena los datos dentro de cada particion, de modo que filtrar por
-- esas columnas permite saltar bloques.
--
-- Diferencia con la particion: el estimado previo NO refleja el ahorro
-- del agrupamiento, porque se decide al ejecutar. El ahorro aparece en
-- los bytes realmente procesados, que se ven despues.
-- ---------------------------------------------------------------------

-- F1. Filtro sobre las columnas de agrupamiento.
SELECT COUNT(*) AS operaciones
FROM `PROYECTO.pagos.operaciones`
WHERE estatus = 'APROBADA' AND metodo_captura = 'QR';

-- F2. Consultar lo que costo de verdad, despues de ejecutar.
--     Esta vista es la herramienta de control de costo del dia a dia.
SELECT
  creation_time,
  ROUND(total_bytes_processed / 1024 / 1024, 2) AS mb_procesados,
  ROUND(total_bytes_billed / 1024 / 1024, 2)    AS mb_cobrados,
  cache_hit,
  SUBSTR(query, 1, 60) AS consulta
FROM `PROYECTO.region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
  AND job_type = 'QUERY'
ORDER BY creation_time DESC
LIMIT 20;

-- Observacion: cache_hit indica que BigQuery devolvio un resultado
-- guardado y NO cobro. La cache dura 24 horas y se invalida si la tabla
-- cambia. Es gratuita y automatica, a diferencia de la de la sesion
-- anterior con Redis.


-- ---------------------------------------------------------------------
-- Bloque G. Analitica que el curso ya conoce
--
-- Las funciones de ventana de la sesion 2.3 funcionan igual.
-- ---------------------------------------------------------------------

-- G1. Participacion de cada comercio, con ventana.
SELECT
  comercio.nombre AS comercio,
  SUM(monto) AS importe,
  ROUND(100 * SUM(monto) / SUM(SUM(monto)) OVER (), 2) AS pct
FROM `PROYECTO.pagos.operaciones`
WHERE estatus = 'APROBADA'
GROUP BY comercio
ORDER BY importe DESC;

-- G2. Acumulado por dia.
SELECT
  DATE(fecha_hora) AS dia,
  SUM(monto) AS importe_dia,
  SUM(SUM(monto)) OVER (ORDER BY DATE(fecha_hora)) AS acumulado
FROM `PROYECTO.pagos.operaciones`
WHERE estatus = 'APROBADA'
  AND fecha_hora >= '2026-01-01'
  AND fecha_hora <  '2026-02-01'
GROUP BY dia
ORDER BY dia;

-- G3. Expresion de tabla comun, como en la sesion 2.3.
WITH por_comercio AS (
  SELECT comercio.nombre AS comercio, SUM(monto) AS importe
  FROM `PROYECTO.pagos.operaciones`
  WHERE estatus = 'APROBADA'
  GROUP BY comercio
),
estadisticas AS (
  SELECT AVG(importe) AS media, STDDEV(importe) AS desviacion
  FROM por_comercio
)
SELECT p.comercio, p.importe, ROUND(e.media, 2) AS media
FROM por_comercio p CROSS JOIN estadisticas e
WHERE p.importe > e.media
ORDER BY p.importe DESC;


-- ---------------------------------------------------------------------
-- Bloque H. Crear una tabla derivada
--
-- Es lo que Dataform va a programar.
-- ---------------------------------------------------------------------

-- H1. Tabla de resumen diario por comercio.
CREATE OR REPLACE TABLE `PROYECTO.pagos.resumen_diario`
PARTITION BY dia
CLUSTER BY comercio
AS
SELECT
  DATE(fecha_hora)                                        AS dia,
  comercio.nombre                                         AS comercio,
  comercio.ciudad                                         AS ciudad,
  COUNT(*)                                                AS operaciones,
  COUNTIF(estatus = 'APROBADA')                           AS aprobadas,
  COUNTIF(estatus = 'RECHAZADA')                          AS rechazadas,
  SUM(IF(estatus = 'APROBADA', monto, 0))                 AS importe,
  COUNTIF(tiene_contracargo)                              AS contracargos
FROM `PROYECTO.pagos.operaciones`
GROUP BY dia, comercio, ciudad;

-- H2. Consultar la tabla derivada cuesta una fraccion del original.
SELECT comercio, SUM(importe) AS importe
FROM `PROYECTO.pagos.resumen_diario`
GROUP BY comercio
ORDER BY importe DESC;

-- Comparar el estimado de H2 contra el de C2. Es el argumento entero de
-- un almacen analitico: se calcula una vez y se consulta muchas.


-- ---------------------------------------------------------------------
-- Bloque I. Lo que BigQuery NO hace
--
-- Importa tanto como lo que si hace.
-- ---------------------------------------------------------------------

-- I1. No hay llaves foraneas que el motor aplique.
--     Se pueden DECLARAR desde 2023, y sirven al optimizador, pero no
--     se verifican: son restricciones "no aplicadas".

-- I2. No hay indices como los de PostgreSQL. La particion y el
--     agrupamiento cumplen un papel parecido, y se declaran al crear
--     la tabla, no despues.

-- I3. Las modificaciones fila por fila son caras y estan limitadas.
--     BigQuery esta hecho para cargar y consultar, no para actualizar
--     registros de forma transaccional.
--
--     Este UPDATE funciona, y en un sistema transaccional seria un
--     error de diseno usarlo asi:
-- UPDATE `PROYECTO.pagos.operaciones`
-- SET estatus = 'REVERSADA'
-- WHERE id_transaccion = 'TRX0000001';

-- I4. No conviene como sistema de registro de una operacion en curso.
--     La autorizacion de un pago necesita responder en milisegundos y
--     escribir de forma transaccional. Eso es PostgreSQL.

-- Criterio que cierra el curso:
--   PostgreSQL registra la operacion.
--   Redis responde durante la autorizacion.
--   BigQuery responde sobre el historico.
--   Ninguno sustituye a los otros.
