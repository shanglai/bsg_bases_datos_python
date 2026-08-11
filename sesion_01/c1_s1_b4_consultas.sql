-- =====================================================================
-- c1_s1_b4_consultas.sql
-- Sesion 1.1: primeras consultas sobre el caso de estudio
--
-- Motor:  SQLite
-- Base:   pagos.db, tabla unica llamada movimientos
-- Uso:    sqlite3 pagos.db < c1_s1_b4_consultas.sql
--         o bien copiar cada bloque en el cliente SQL
-- =====================================================================

.headers on
.mode column

-- ---------------------------------------------------------------------
-- Bloque A. Reconocer la tabla antes de consultarla
-- ---------------------------------------------------------------------

-- A1. Estructura de la tabla: nombre y tipo de cada columna.
PRAGMA table_info(movimientos);

-- A2. Volumen total.
SELECT COUNT(*) AS total_movimientos
FROM movimientos;

-- A3. Una muestra, para entender que contiene cada columna.
SELECT *
FROM movimientos
LIMIT 5;


-- ---------------------------------------------------------------------
-- Bloque B. Seleccion, filtrado y ordenamiento
-- ---------------------------------------------------------------------

-- B1. Proyeccion: solo las columnas de interes.
SELECT id_transaccion, fecha_hora, comercio, monto
FROM movimientos
LIMIT 10;

-- B2. Filtro por un valor exacto.
SELECT id_transaccion, comercio, monto, estatus
FROM movimientos
WHERE estatus = 'RECHAZADA'
LIMIT 10;

-- B3. Filtro por rango y ordenamiento descendente.
SELECT id_transaccion, ciudad_comercio, monto
FROM movimientos
WHERE monto BETWEEN 10000 AND 30000
ORDER BY monto DESC
LIMIT 10;

-- B4. Varias condiciones combinadas.
SELECT id_transaccion, comercio, metodo_captura, monto
FROM movimientos
WHERE ciudad_comercio = 'Monterrey'
  AND metodo_captura IN ('QR', 'CONTACTLESS')
  AND estatus = 'APROBADA'
ORDER BY monto DESC
LIMIT 10;


-- ---------------------------------------------------------------------
-- Bloque C. Agregaciones
-- ---------------------------------------------------------------------

-- C1. Totales generales.
SELECT COUNT(*)            AS operaciones,
       ROUND(SUM(monto),2) AS importe_total,
       ROUND(AVG(monto),2) AS ticket_promedio,
       MIN(monto)          AS ticket_minimo,
       MAX(monto)          AS ticket_maximo
FROM movimientos
WHERE estatus = 'APROBADA';

-- C2. Agrupacion por ciudad.
SELECT ciudad_comercio,
       COUNT(*)            AS operaciones,
       ROUND(SUM(monto),2) AS importe_total
FROM movimientos
WHERE estatus = 'APROBADA'
GROUP BY ciudad_comercio
ORDER BY importe_total DESC;

-- C3. Agrupacion con filtro posterior a la agregacion.
SELECT metodo_captura,
       COUNT(*)            AS operaciones,
       ROUND(AVG(monto),2) AS ticket_promedio
FROM movimientos
GROUP BY metodo_captura
HAVING COUNT(*) > 800
ORDER BY ticket_promedio DESC;

-- C4. Tasa de rechazo por marca de tarjeta.
SELECT marca_tarjeta,
       COUNT(*)                                                      AS total,
       SUM(CASE WHEN estatus = 'RECHAZADA' THEN 1 ELSE 0 END)         AS rechazadas,
       ROUND(100.0 * SUM(CASE WHEN estatus = 'RECHAZADA' THEN 1 ELSE 0 END)
             / COUNT(*), 2)                                           AS porcentaje_rechazo
FROM movimientos
GROUP BY marca_tarjeta
ORDER BY porcentaje_rechazo DESC;


-- ---------------------------------------------------------------------
-- Bloque D. La evidencia que abre la sesion 1.2
--
-- Las consultas anteriores funcionan porque agrupan por columnas limpias.
-- Al agrupar por comercio o por categoria, el resultado deja de ser confiable.
-- ---------------------------------------------------------------------

-- D1. Cuantos valores distintos hay en las columnas de negocio.
SELECT COUNT(DISTINCT comercio)           AS variantes_de_comercio,
       COUNT(DISTINCT categoria_comercio) AS variantes_de_categoria,
       COUNT(DISTINCT cliente)            AS variantes_de_cliente
FROM movimientos;

-- D2. El volumen por comercio queda repartido entre variantes de escritura.
SELECT comercio,
       COUNT(*)            AS operaciones,
       ROUND(SUM(monto),2) AS importe_total
FROM movimientos
GROUP BY comercio
ORDER BY operaciones DESC;

-- D3. Un intento manual de corregirlo. Funciona hoy y se rompe manana,
--     cuando aparezca una variante nueva de escritura.
SELECT UPPER(TRIM(comercio)) AS comercio_normalizado,
       COUNT(*)              AS operaciones
FROM movimientos
GROUP BY comercio_normalizado
ORDER BY operaciones DESC;

-- D4. El mismo dato de contacto se repite en cada fila del cliente.
--     Actualizar un correo implicaria modificar cientos de filas.
SELECT cliente, correo_cliente, COUNT(*) AS filas_que_repiten_el_dato
FROM movimientos
GROUP BY cliente, correo_cliente
ORDER BY filas_que_repiten_el_dato DESC
LIMIT 10;

-- Pregunta de cierre de la sesion:
-- que estructura evitaria que el nombre de un comercio pueda escribirse
-- de tres formas distintas dentro de la misma base.
