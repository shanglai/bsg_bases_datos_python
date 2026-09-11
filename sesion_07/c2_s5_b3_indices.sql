-- =====================================================================
-- c2_s5_b3_indices.sql
-- Sesion 2.5: rendimiento, indices y planes de ejecucion
--
-- Motor: PostgreSQL
-- Base:  pagos, con la tabla transacciones_volumen creada por
--        c2_s5_b2_volumen.py (2 millones de filas, sin indices)
-- Uso:   se ejecuta desde DBeaver, bloque por bloque y EN ORDEN
--
-- El orden importa: varios bloques crean o eliminan indices y el
-- siguiente depende del estado que dejo el anterior.
-- =====================================================================

SET search_path TO pagos;


-- ---------------------------------------------------------------------
-- Bloque A. Punto de partida
-- ---------------------------------------------------------------------

-- A1. Volumen y tamano.
SELECT COUNT(*)                                                     AS filas,
       pg_size_pretty(pg_total_relation_size('transacciones_volumen')) AS tamano
FROM transacciones_volumen;

-- A2. Ningun indice todavia.
SELECT indexname FROM pg_indexes
WHERE schemaname = 'pagos' AND tablename = 'transacciones_volumen';

-- A3. La consulta de trabajo: el historial de una tarjeta en un mes.
--     Es la consulta mas comun de un sistema de pagos.
SELECT COUNT(*), SUM(monto)
FROM transacciones_volumen
WHERE id_tarjeta = 42
  AND fecha_hora BETWEEN '2026-03-01' AND '2026-03-31';


-- ---------------------------------------------------------------------
-- Bloque B. Leer un plan de ejecucion
--
--   EXPLAIN          muestra el plan estimado, sin ejecutar
--   EXPLAIN ANALYZE  ejecuta y muestra lo estimado junto a lo real
--
-- Advertencia: EXPLAIN ANALYZE EJECUTA la consulta. Sobre un INSERT,
-- un UPDATE o un DELETE, el cambio ocurre. Para inspeccionarlos sin
-- efecto, hay que envolverlos en una transaccion y revertirla.
-- ---------------------------------------------------------------------

-- B1. El plan estimado.
EXPLAIN
SELECT COUNT(*), SUM(monto)
FROM transacciones_volumen
WHERE id_tarjeta = 42
  AND fecha_hora BETWEEN '2026-03-01' AND '2026-03-31';

-- B2. El plan real, con tiempos.
EXPLAIN ANALYZE
SELECT COUNT(*), SUM(monto)
FROM transacciones_volumen
WHERE id_tarjeta = 42
  AND fecha_hora BETWEEN '2026-03-01' AND '2026-03-31';

-- Como se lee un plan:
--
--   Se lee de adentro hacia afuera y de abajo hacia arriba.
--   El nodo mas anidado se ejecuta primero.
--
--   cost=0.00..31287.33   costo estimado de inicio y de finalizacion,
--                         en unidades arbitrarias, no en milisegundos
--   rows=634              filas que el motor ESTIMA que devolvera
--   actual time=1.6..157  milisegundos reales de inicio y de fin
--   rows=541 loops=3      filas reales por vuelta, y numero de vueltas
--
--   La comparacion entre rows estimado y rows real es el diagnostico
--   mas util: una diferencia de un orden de magnitud indica
--   estadisticas desactualizadas o un predicado que el motor no supo
--   estimar.

-- B3. Version con detalle de lectura de bloques.
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*), SUM(monto)
FROM transacciones_volumen
WHERE id_tarjeta = 42
  AND fecha_hora BETWEEN '2026-03-01' AND '2026-03-31';

-- shared hit    bloques encontrados en memoria
-- shared read   bloques leidos de disco
-- La proporcion entre ambos dice si el problema es de plan o de memoria.


-- ---------------------------------------------------------------------
-- Bloque C. El efecto del indice
-- ---------------------------------------------------------------------

-- C1. Indice compuesto sobre las dos columnas del filtro.
--     El orden de las columnas importa y se estudia en el bloque D.
CREATE INDEX idx_vol_tarjeta_fecha
    ON transacciones_volumen (id_tarjeta, fecha_hora);

ANALYZE transacciones_volumen;

-- C2. La misma consulta, con el indice ya creado.
EXPLAIN ANALYZE
SELECT COUNT(*), SUM(monto)
FROM transacciones_volumen
WHERE id_tarjeta = 42
  AND fecha_hora BETWEEN '2026-03-01' AND '2026-03-31';

-- El plan cambia de Parallel Seq Scan a Bitmap Index Scan.
-- El tiempo pasa de un orden de cien milisegundos a uno de diez.

-- C3. Tamano del indice frente al de la tabla.
SELECT pg_size_pretty(pg_relation_size('transacciones_volumen')) AS tabla,
       pg_size_pretty(pg_relation_size('idx_vol_tarjeta_fecha'))  AS indice;


-- ---------------------------------------------------------------------
-- Bloque D. El orden de las columnas del indice
--
-- Un indice compuesto se recorre por su primera columna. Sirve para
-- filtros sobre (a), sobre (a, b), y no sirve para un filtro solo
-- sobre (b).
-- ---------------------------------------------------------------------

-- D1. Filtro solo por la primera columna. Usa el indice.
EXPLAIN ANALYZE
SELECT COUNT(*) FROM transacciones_volumen WHERE id_tarjeta = 42;

-- D2. Filtro solo por la segunda columna. NO usa el indice compuesto:
--     el motor no puede recorrerlo sin conocer la primera columna.
--     El plan vuelve a ser un recorrido secuencial.
--
--     Nota de version: PostgreSQL 18 incorporo el recorrido con salto,
--     que permite aprovechar el indice en algunos de estos casos. En
--     las versiones anteriores, que son las que la mayoria opera hoy,
--     el comportamiento es el que se observa aqui.
EXPLAIN ANALYZE
SELECT COUNT(*) FROM transacciones_volumen
WHERE fecha_hora BETWEEN '2026-03-01' AND '2026-03-02';

-- D3. Indice sobre la fecha sola, para comparar.
CREATE INDEX idx_vol_fecha ON transacciones_volumen (fecha_hora);
ANALYZE transacciones_volumen;

EXPLAIN ANALYZE
SELECT COUNT(*) FROM transacciones_volumen
WHERE fecha_hora BETWEEN '2026-03-01' AND '2026-03-02';

-- Criterio: la columna mas selectiva, o la que aparece en mas
-- consultas, va primero.


-- ---------------------------------------------------------------------
-- Bloque E. Cuando el indice no se usa
--
-- Un indice existente no garantiza que se use. Tres casos frecuentes.
-- ---------------------------------------------------------------------

-- E1. Predicado poco selectivo. El motor prefiere recorrer la tabla.
EXPLAIN ANALYZE
SELECT COUNT(*) FROM transacciones_volumen WHERE estatus = 'APROBADA';

-- E2. Funcion aplicada a la columna indexada.
--     El indice esta sobre fecha_hora, no sobre DATE(fecha_hora).
CREATE INDEX IF NOT EXISTS idx_vol_fecha2 ON transacciones_volumen (fecha_hora);
ANALYZE transacciones_volumen;

EXPLAIN ANALYZE
SELECT COUNT(*) FROM transacciones_volumen
WHERE DATE(fecha_hora) = '2026-03-15';

-- E3. La misma consulta reescrita como rango. Ahora si usa el indice.
EXPLAIN ANALYZE
SELECT COUNT(*) FROM transacciones_volumen
WHERE fecha_hora >= '2026-03-15' AND fecha_hora < '2026-03-16';

-- Regla practica: envolver la columna en una funcion inutiliza el
-- indice. Se reescribe como rango, o se crea un indice de expresion.

-- E4. Estadisticas desactualizadas. Sin ANALYZE tras una carga masiva,
--     el motor estima con datos viejos y puede elegir mal.
SELECT relname, n_live_tup, last_analyze, last_autoanalyze
FROM pg_stat_user_tables
WHERE relname = 'transacciones_volumen';


-- ---------------------------------------------------------------------
-- Bloque F. El costo de escritura
--
-- Cada indice se actualiza en cada insercion, actualizacion y borrado.
-- Es el precio de la lectura rapida.
-- ---------------------------------------------------------------------

-- F1. Tabla de prueba sin indices.
DROP TABLE IF EXISTS prueba_escritura;
CREATE TABLE prueba_escritura (
    id BIGINT, fecha TIMESTAMP, terminal INT, monto NUMERIC(12,2));

\timing on

INSERT INTO prueba_escritura
SELECT g, TIMESTAMP '2026-01-01' + (random()*180) * INTERVAL '1 day',
       1 + floor(random()*30)::INT, round((random()*5000)::NUMERIC, 2)
FROM generate_series(1, 500000) g;

-- F2. La misma insercion, ahora con tres indices.
DROP TABLE IF EXISTS prueba_escritura;
CREATE TABLE prueba_escritura (
    id BIGINT, fecha TIMESTAMP, terminal INT, monto NUMERIC(12,2));
CREATE INDEX i1 ON prueba_escritura (terminal);
CREATE INDEX i2 ON prueba_escritura (fecha);
CREATE INDEX i3 ON prueba_escritura (terminal, fecha);

INSERT INTO prueba_escritura
SELECT g, TIMESTAMP '2026-01-01' + (random()*180) * INTERVAL '1 day',
       1 + floor(random()*30)::INT, round((random()*5000)::NUMERIC, 2)
FROM generate_series(1, 500000) g;

\timing off

DROP TABLE IF EXISTS prueba_escritura;

-- Resultado tipico: la insercion con tres indices tarda entre cuatro y
-- cinco veces mas.
--
-- Consecuencia: un indice que no se usa no es neutro. Cuesta espacio y
-- cuesta en cada escritura.


-- ---------------------------------------------------------------------
-- Bloque G. Indices que no habiamos visto
-- ---------------------------------------------------------------------

-- G1. Indice parcial. Solo indexa las filas que cumplen la condicion.
--     Util cuando las consultas siempre filtran por lo mismo.
CREATE INDEX idx_vol_rechazadas ON transacciones_volumen (id_tarjeta)
    WHERE estatus = 'RECHAZADA';
ANALYZE transacciones_volumen;

SELECT pg_size_pretty(pg_relation_size('idx_vol_rechazadas')) AS parcial,
       pg_size_pretty(pg_relation_size('idx_vol_tarjeta_fecha')) AS completo;

EXPLAIN ANALYZE
SELECT COUNT(*) FROM transacciones_volumen
WHERE estatus = 'RECHAZADA' AND id_tarjeta = 42;

-- G2. Indice de cobertura. INCLUDE agrega columnas al indice sin que
--     formen parte de la clave, de modo que la consulta se resuelve
--     sin visitar la tabla.
CREATE INDEX idx_vol_cobertura
    ON transacciones_volumen (id_tarjeta, fecha_hora) INCLUDE (monto);

-- VACUUM, y no solo ANALYZE. El Index Only Scan requiere que el mapa de
-- visibilidad este actualizado: sin el, el motor debe visitar la tabla
-- para comprobar que cada fila es visible, y el plan degrada a Bitmap
-- Heap Scan aunque el indice tenga todas las columnas necesarias.
VACUUM ANALYZE transacciones_volumen;

EXPLAIN ANALYZE
SELECT SUM(monto) FROM transacciones_volumen
WHERE id_tarjeta = 42 AND fecha_hora BETWEEN '2026-03-01' AND '2026-03-31';

-- Un Index Only Scan indica que la tabla no se visito. El contador
-- Heap Fetches del plan debe ser cero; si no lo es, falta VACUUM.

-- G3. Inventario de indices y su uso real.
--     idx_scan cuenta cuantas veces se ha usado cada indice. Un indice
--     con cero lecturas es candidato a eliminarse.
SELECT indexrelname AS indice,
       idx_scan     AS veces_usado,
       pg_size_pretty(pg_relation_size(indexrelid)) AS tamano
FROM pg_stat_user_indexes
WHERE relname = 'transacciones_volumen'
ORDER BY idx_scan;


-- ---------------------------------------------------------------------
-- Bloque H. Transacciones
-- ---------------------------------------------------------------------

-- H1. Una transaccion agrupa operaciones que se aplican todas o ninguna.
BEGIN;
    UPDATE transacciones_volumen SET monto = monto * 2 WHERE id_tarjeta = 42;
    SELECT COUNT(*), SUM(monto) FROM transacciones_volumen WHERE id_tarjeta = 42;
ROLLBACK;

-- H2. Despues del ROLLBACK, nada cambio.
SELECT COUNT(*), SUM(monto) FROM transacciones_volumen WHERE id_tarjeta = 42;

-- H3. Punto de guardado. Permite revertir una parte sin perder el resto.
BEGIN;
    UPDATE transacciones_volumen SET estatus = 'REVERSADA' WHERE id_tarjeta = 7;
    SAVEPOINT despues_del_primero;
    UPDATE transacciones_volumen SET estatus = 'REVERSADA' WHERE id_tarjeta = 8;
    ROLLBACK TO SAVEPOINT despues_del_primero;
    -- La tarjeta 7 quedo modificada, la 8 no.
    SELECT id_tarjeta, COUNT(*) FROM transacciones_volumen
    WHERE estatus = 'REVERSADA' GROUP BY id_tarjeta ORDER BY id_tarjeta;
ROLLBACK;

-- H4. Inspeccionar el plan de una modificacion sin aplicarla.
BEGIN;
    EXPLAIN ANALYZE
    UPDATE transacciones_volumen SET monto = monto + 1 WHERE id_tarjeta = 99;
ROLLBACK;


-- ---------------------------------------------------------------------
-- Bloque I. Niveles de aislamiento
--
-- Contenido de lectura complementaria. Se enuncia en clase y se
-- desarrolla fuera de sesion.
-- ---------------------------------------------------------------------

-- I1. El nivel predeterminado de PostgreSQL.
SHOW default_transaction_isolation;

-- I2. Los tres niveles que PostgreSQL implementa.
--
--   READ COMMITTED    predeterminado. Cada sentencia ve los datos
--                     confirmados al momento de iniciar ella misma.
--   REPEATABLE READ   todas las sentencias ven la misma imagen, la del
--                     inicio de la transaccion.
--   SERIALIZABLE      ademas garantiza que el resultado equivale a
--                     alguna ejecucion secuencial de las transacciones.
--
-- PostgreSQL no implementa READ UNCOMMITTED: lo acepta como sintaxis y
-- lo trata como READ COMMITTED.

-- I3. Declarar el nivel de una transaccion.
BEGIN ISOLATION LEVEL REPEATABLE READ;
    SELECT COUNT(*) FROM transacciones_volumen;
COMMIT;


-- Pregunta de cierre de la sesion:
-- el capitulo 2 llevo el modelo relacional hasta el volumen y la
-- concurrencia. Que ocurre cuando el dato que llega no tiene una
-- estructura estable, y por que existe un motor construido alrededor
-- de esa suposicion. Se responde en el capitulo 3.
