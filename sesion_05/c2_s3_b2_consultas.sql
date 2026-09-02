-- =====================================================================
-- c2_s3_b2_consultas.sql
-- Sesion 2.3: SQL analitico
--
-- Motor: PostgreSQL
-- Base:  pagos, esquema pagos
-- Uso:   se ejecuta desde DBeaver, bloque por bloque
-- =====================================================================

SET search_path TO pagos;


-- ---------------------------------------------------------------------
-- Bloque A. El problema que abre la sesion
--
-- GROUP BY colapsa el grupo en una sola fila. Sirve para responder
-- cuanto sumo cada tarjeta, y no sirve para responder como fue
-- acumulandose ese total operacion por operacion.
-- ---------------------------------------------------------------------

-- A1. Lo que si resuelve GROUP BY: una fila por tarjeta.
SELECT ta.id_tarjeta,
       COUNT(*)     AS operaciones,
       SUM(t.monto) AS gasto_total
FROM transacciones t
JOIN tarjetas ta ON ta.id_tarjeta = t.id_tarjeta
WHERE t.estatus = 'APROBADA'
GROUP BY ta.id_tarjeta
ORDER BY gasto_total DESC
LIMIT 5;

-- A2. Lo que no resuelve: el detalle desaparecio.
--     Esta consulta es invalida. El motor la rechaza porque
--     id_transaccion no esta en el GROUP BY ni dentro de una funcion
--     de agregacion.
-- SELECT ta.id_tarjeta, t.id_transaccion, SUM(t.monto)
-- FROM transacciones t
-- JOIN tarjetas ta ON ta.id_tarjeta = t.id_tarjeta
-- GROUP BY ta.id_tarjeta;

-- A3. El intento de resolverlo con subconsulta correlacionada.
--     Funciona, y se evalua una vez por cada fila del resultado.
SELECT t.id_transaccion,
       t.id_tarjeta,
       t.monto,
       (SELECT SUM(t2.monto)
        FROM transacciones t2
        WHERE t2.id_tarjeta = t.id_tarjeta
          AND t2.fecha_hora <= t.fecha_hora
          AND t2.estatus = 'APROBADA') AS acumulado
FROM transacciones t
WHERE t.estatus = 'APROBADA' AND t.id_tarjeta = 1
ORDER BY t.fecha_hora;


-- ---------------------------------------------------------------------
-- Bloque B. Funciones de ventana
--
-- Una funcion de ventana calcula sobre un conjunto de filas
-- relacionadas con la fila actual, y devuelve un valor POR CADA FILA.
-- El detalle se conserva.
-- ---------------------------------------------------------------------

-- B1. La misma pregunta del A3, resuelta con una ventana.
SELECT id_transaccion,
       id_tarjeta,
       fecha_hora,
       monto,
       SUM(monto) OVER (PARTITION BY id_tarjeta ORDER BY fecha_hora) AS acumulado
FROM transacciones
WHERE estatus = 'APROBADA' AND id_tarjeta = 1
ORDER BY fecha_hora;

-- B2. Las tres piezas de OVER.
--     PARTITION BY  define el grupo de la ventana
--     ORDER BY      define el orden dentro del grupo
--     el marco      define que filas del grupo entran en el calculo
SELECT id_transaccion,
       id_tarjeta,
       monto,
       SUM(monto)   OVER (PARTITION BY id_tarjeta)                    AS total_tarjeta,
       SUM(monto)   OVER (PARTITION BY id_tarjeta ORDER BY fecha_hora) AS acumulado,
       ROUND(AVG(monto) OVER (PARTITION BY id_tarjeta), 2)             AS promedio_tarjeta,
       COUNT(*)     OVER (PARTITION BY id_tarjeta)                     AS operaciones
FROM transacciones
WHERE estatus = 'APROBADA' AND id_tarjeta IN (1, 2)
ORDER BY id_tarjeta, fecha_hora;

-- B3. Sin PARTITION BY, la ventana es toda la tabla.
SELECT id_transaccion, monto,
       ROUND(100.0 * monto / SUM(monto) OVER (), 4) AS pct_del_total
FROM transacciones
WHERE estatus = 'APROBADA'
ORDER BY monto DESC
LIMIT 5;


-- ---------------------------------------------------------------------
-- Bloque C. Funciones de ordenamiento
-- ---------------------------------------------------------------------

-- C1. Las tres funciones de rango y su diferencia ante empates.
--     Se usa el conteo de operaciones por cliente, donde los empates
--     abundan. Con importes monetarios no habria empates y las tres
--     columnas saldrian identicas, de modo que la diferencia no se
--     apreciaria.
SELECT cl.nombre,
       COUNT(*)                                        AS operaciones,
       ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC)      AS row_number,
       RANK()       OVER (ORDER BY COUNT(*) DESC)      AS rank,
       DENSE_RANK() OVER (ORDER BY COUNT(*) DESC)      AS dense_rank
FROM transacciones t
JOIN tarjetas ta ON ta.id_tarjeta = t.id_tarjeta
JOIN clientes cl ON cl.id_cliente = ta.id_cliente
WHERE t.estatus = 'APROBADA'
GROUP BY cl.id_cliente, cl.nombre
ORDER BY operaciones DESC
LIMIT 12;

-- Lectura del resultado:
--   ROW_NUMBER  numera sin considerar empates. Dos clientes con 32
--               operaciones reciben 3 y 4. El desempate es arbitrario.
--   RANK        asigna el mismo numero a los empatados y luego salta.
--               Tras dos terceros lugares, el siguiente es el quinto.
--   DENSE_RANK  asigna el mismo numero y no salta. Tras dos terceros,
--               el siguiente es el cuarto.
--
-- Criterio: ROW_NUMBER para elegir una fila por grupo, RANK para un
-- ranking publicable, DENSE_RANK para contar niveles distintos.

-- C2. Ranking dentro de cada grupo: el comercio lider de cada ciudad.
SELECT ciudad, nombre, importe
FROM (
    SELECT c.ciudad, c.nombre, SUM(t.monto) AS importe,
           ROW_NUMBER() OVER (PARTITION BY c.ciudad
                              ORDER BY SUM(t.monto) DESC) AS posicion
    FROM transacciones t
    JOIN terminales te ON te.id_terminal = t.id_terminal
    JOIN comercios  c  ON c.id_comercio  = te.id_comercio
    WHERE t.estatus = 'APROBADA'
    GROUP BY c.ciudad, c.nombre
) AS ranking
WHERE posicion = 1
ORDER BY importe DESC;

-- C3. Por que hace falta la subconsulta.
--     Esta version es invalida: una funcion de ventana no puede
--     usarse en WHERE, porque WHERE se evalua antes que SELECT.
-- SELECT c.ciudad, c.nombre, SUM(t.monto) AS importe
-- FROM ...
-- WHERE ROW_NUMBER() OVER (...) = 1
-- GROUP BY c.ciudad, c.nombre;

-- C4. NTILE reparte las filas en grupos de tamano similar.
SELECT id_transaccion, monto,
       NTILE(4) OVER (ORDER BY monto) AS cuartil
FROM transacciones
WHERE estatus = 'APROBADA' AND id_tarjeta = 1
ORDER BY monto;


-- ---------------------------------------------------------------------
-- Bloque D. Funciones de desplazamiento
--
-- Comparar cada fila contra la anterior o la siguiente de su grupo.
-- ---------------------------------------------------------------------

-- D1. LAG y LEAD: el monto anterior y el siguiente de la misma tarjeta.
SELECT id_transaccion, fecha_hora, monto,
       LAG(monto)  OVER (PARTITION BY id_tarjeta ORDER BY fecha_hora) AS monto_anterior,
       LEAD(monto) OVER (PARTITION BY id_tarjeta ORDER BY fecha_hora) AS monto_siguiente
FROM transacciones
WHERE estatus = 'APROBADA' AND id_tarjeta = 1
ORDER BY fecha_hora;

-- D2. Uso practico: dias transcurridos desde la operacion anterior.
SELECT id_transaccion, fecha_hora,
       fecha_hora - LAG(fecha_hora) OVER (PARTITION BY id_tarjeta
                                          ORDER BY fecha_hora) AS desde_la_anterior
FROM transacciones
WHERE estatus = 'APROBADA' AND id_tarjeta = 1
ORDER BY fecha_hora;

-- D3. Variacion mensual del importe.
WITH por_mes AS (
    SELECT DATE_TRUNC('month', fecha_hora)::DATE AS mes,
           SUM(monto)                            AS importe
    FROM transacciones
    WHERE estatus = 'APROBADA'
    GROUP BY mes
)
SELECT mes, importe,
       LAG(importe) OVER (ORDER BY mes)                                AS mes_anterior,
       ROUND(100.0 * (importe - LAG(importe) OVER (ORDER BY mes))
             / LAG(importe) OVER (ORDER BY mes), 2)                    AS variacion_pct
FROM por_mes
ORDER BY mes;

-- D4. FIRST_VALUE y LAST_VALUE.
--     LAST_VALUE requiere marco explicito, por el motivo del bloque E.
SELECT id_transaccion, fecha_hora, monto,
       FIRST_VALUE(monto) OVER (PARTITION BY id_tarjeta ORDER BY fecha_hora) AS primera,
       LAST_VALUE(monto)  OVER (PARTITION BY id_tarjeta ORDER BY fecha_hora
                                ROWS BETWEEN UNBOUNDED PRECEDING
                                         AND UNBOUNDED FOLLOWING)            AS ultima
FROM transacciones
WHERE estatus = 'APROBADA' AND id_tarjeta = 1
ORDER BY fecha_hora;


-- ---------------------------------------------------------------------
-- Bloque E. El marco de la ventana
--
-- Al escribir ORDER BY dentro de OVER, el marco predeterminado es
-- RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW, es decir, desde
-- el inicio del grupo hasta la fila actual. Eso es lo que produce el
-- acumulado.
--
-- Sin ORDER BY, el marco abarca el grupo completo.
-- ---------------------------------------------------------------------

-- E1. La misma funcion con tres marcos distintos.
SELECT id_transaccion, fecha_hora, monto,
       SUM(monto) OVER (PARTITION BY id_tarjeta)                        AS total_grupo,
       SUM(monto) OVER (PARTITION BY id_tarjeta ORDER BY fecha_hora)    AS acumulado,
       SUM(monto) OVER (PARTITION BY id_tarjeta ORDER BY fecha_hora
                        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)       AS ultimas_tres
FROM transacciones
WHERE estatus = 'APROBADA' AND id_tarjeta = 1
ORDER BY fecha_hora;

-- E2. Promedio movil de tres operaciones.
SELECT id_transaccion, fecha_hora, monto,
       ROUND(AVG(monto) OVER (PARTITION BY id_tarjeta ORDER BY fecha_hora
                              ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2)
           AS promedio_movil_3
FROM transacciones
WHERE estatus = 'APROBADA' AND id_tarjeta = 1
ORDER BY fecha_hora;

-- E3. La trampa de RANGE frente a ROWS.
--     RANGE agrupa las filas con el mismo valor de ORDER BY.
--     ROWS cuenta filas fisicas.
--     Con fechas repetidas, los dos marcos difieren.
SELECT metodo_captura, monto,
       SUM(monto) OVER (ORDER BY metodo_captura
                        RANGE BETWEEN UNBOUNDED PRECEDING
                                  AND CURRENT ROW) AS con_range,
       SUM(monto) OVER (ORDER BY metodo_captura
                        ROWS  BETWEEN UNBOUNDED PRECEDING
                                  AND CURRENT ROW) AS con_rows
FROM transacciones
WHERE estatus = 'APROBADA' AND id_tarjeta = 1
ORDER BY metodo_captura
LIMIT 10;


-- ---------------------------------------------------------------------
-- Bloque F. Expresiones de tabla comunes
--
-- WITH nombra un resultado intermedio y permite reutilizarlo. Su valor
-- principal es de legibilidad: convierte una consulta anidada en una
-- secuencia de pasos con nombre.
-- ---------------------------------------------------------------------

-- F1. La consulta C2, reescrita con CTE.
WITH importe_por_comercio AS (
    SELECT c.ciudad, c.nombre, SUM(t.monto) AS importe
    FROM transacciones t
    JOIN terminales te ON te.id_terminal = t.id_terminal
    JOIN comercios  c  ON c.id_comercio  = te.id_comercio
    WHERE t.estatus = 'APROBADA'
    GROUP BY c.ciudad, c.nombre
),
ranking AS (
    SELECT ciudad, nombre, importe,
           ROW_NUMBER() OVER (PARTITION BY ciudad ORDER BY importe DESC) AS posicion
    FROM importe_por_comercio
)
SELECT ciudad, nombre, importe
FROM ranking
WHERE posicion = 1
ORDER BY importe DESC;

-- F2. Una CTE puede referenciar a la anterior. Se leen de arriba abajo.
WITH aprobadas AS (
    SELECT * FROM transacciones WHERE estatus = 'APROBADA'
),
por_cliente AS (
    SELECT cl.id_cliente, cl.nombre, SUM(a.monto) AS gasto
    FROM aprobadas a
    JOIN tarjetas ta ON ta.id_tarjeta = a.id_tarjeta
    JOIN clientes cl ON cl.id_cliente = ta.id_cliente
    GROUP BY cl.id_cliente, cl.nombre
),
estadisticas AS (
    SELECT AVG(gasto) AS gasto_promedio, STDDEV(gasto) AS desviacion
    FROM por_cliente
)
SELECT p.nombre, p.gasto,
       ROUND((p.gasto - e.gasto_promedio) / e.desviacion, 2) AS desviaciones
FROM por_cliente p
CROSS JOIN estadisticas e
ORDER BY p.gasto DESC
LIMIT 10;

-- F3. Una misma CTE usada dos veces. Con subconsulta habria que
--     escribirla dos veces.
WITH por_comercio AS (
    SELECT c.nombre, SUM(t.monto) AS importe
    FROM transacciones t
    JOIN terminales te ON te.id_terminal = t.id_terminal
    JOIN comercios  c  ON c.id_comercio  = te.id_comercio
    WHERE t.estatus = 'APROBADA'
    GROUP BY c.nombre
)
SELECT p.nombre, p.importe,
       ROUND(100.0 * p.importe / (SELECT SUM(importe) FROM por_comercio), 2) AS pct
FROM por_comercio p
ORDER BY p.importe DESC;


-- ---------------------------------------------------------------------
-- Bloque G. CTE recursiva
--
-- Una CTE recursiva se define en dos partes unidas por UNION ALL:
-- el caso base, y el paso que se apoya en el resultado anterior.
-- Sirve para jerarquias y para generar series.
-- ---------------------------------------------------------------------

-- G1. Generar la serie de meses del periodo, incluidos los vacios.
WITH RECURSIVE calendario AS (
    SELECT DATE '2026-01-01' AS mes            -- caso base
    UNION ALL
    SELECT (mes + INTERVAL '1 month')::DATE    -- paso recursivo
    FROM calendario
    WHERE mes < DATE '2026-06-01'              -- condicion de parada
)
SELECT * FROM calendario;

-- G2. Uso practico: serie completa combinada con los datos, de modo
--     que un mes sin operaciones aparezca en cero y no desaparezca.
WITH RECURSIVE calendario AS (
    SELECT DATE '2026-01-01' AS mes
    UNION ALL
    SELECT (mes + INTERVAL '1 month')::DATE FROM calendario
    WHERE mes < DATE '2026-06-01'
),
por_mes AS (
    SELECT DATE_TRUNC('month', fecha_hora)::DATE AS mes, SUM(monto) AS importe
    FROM transacciones WHERE estatus = 'APROBADA'
    GROUP BY 1
)
SELECT c.mes, COALESCE(p.importe, 0) AS importe
FROM calendario c
LEFT JOIN por_mes p ON p.mes = c.mes
ORDER BY c.mes;

-- G3. Jerarquia. El caso de pagos no tiene una, de modo que se
--     construye una tabla temporal de estructura organizacional para
--     ilustrar el mecanismo.
CREATE TEMP TABLE areas (
    id_area   INT PRIMARY KEY,
    nombre    TEXT NOT NULL,
    id_padre  INT REFERENCES areas (id_area)
);

INSERT INTO areas VALUES
    (1, 'Direccion General',      NULL),
    (2, 'Operaciones',            1),
    (3, 'Tecnologia',             1),
    (4, 'Autorizaciones',         2),
    (5, 'Contracargos',           2),
    (6, 'Infraestructura',        3),
    (7, 'Desarrollo',             3),
    (8, 'Antifraude',             5);

WITH RECURSIVE jerarquia AS (
    SELECT id_area, nombre, id_padre, 1 AS nivel, nombre::TEXT AS ruta
    FROM areas
    WHERE id_padre IS NULL
    UNION ALL
    SELECT a.id_area, a.nombre, a.id_padre, j.nivel + 1,
           j.ruta || ' > ' || a.nombre
    FROM areas a
    JOIN jerarquia j ON j.id_area = a.id_padre
)
SELECT nivel, REPEAT('    ', nivel - 1) || nombre AS estructura, ruta
FROM jerarquia
ORDER BY ruta;


-- ---------------------------------------------------------------------
-- Bloque H. Preguntas de negocio del caso
-- ---------------------------------------------------------------------

-- H1. Operaciones que se salen del patron habitual de su tarjeta.
--     Una operacion que supera en tres desviaciones el promedio de su
--     propia tarjeta merece revision.
WITH aprobadas AS (
    SELECT id_transaccion, id_tarjeta, fecha_hora, monto
    FROM transacciones WHERE estatus = 'APROBADA'
),
con_estadistica AS (
    SELECT *,
           AVG(monto)    OVER (PARTITION BY id_tarjeta) AS promedio,
           STDDEV(monto) OVER (PARTITION BY id_tarjeta) AS desviacion,
           COUNT(*)      OVER (PARTITION BY id_tarjeta) AS operaciones
    FROM aprobadas
)
SELECT id_transaccion, id_tarjeta, monto,
       ROUND(promedio, 2) AS promedio_tarjeta,
       ROUND((monto - promedio) / NULLIF(desviacion, 0), 2) AS desviaciones
FROM con_estadistica
WHERE operaciones >= 10
  AND desviacion > 0
  AND (monto - promedio) / desviacion > 3
ORDER BY desviaciones DESC
LIMIT 15;

-- H2. Intervalo entre operaciones consecutivas de la misma tarjeta.
--     Un intervalo muy corto puede indicar reintentos o duplicidad.
WITH ordenadas AS (
    SELECT id_transaccion, id_tarjeta, fecha_hora, monto,
           LAG(fecha_hora) OVER (PARTITION BY id_tarjeta
                                 ORDER BY fecha_hora) AS anterior
    FROM transacciones
    WHERE estatus = 'APROBADA'
)
SELECT id_transaccion, id_tarjeta, fecha_hora,
       fecha_hora - anterior AS intervalo
FROM ordenadas
WHERE anterior IS NOT NULL
ORDER BY intervalo
LIMIT 10;

-- H3. Participacion acumulada de los comercios: cuantos concentran el
--     ochenta por ciento del importe.
WITH por_comercio AS (
    SELECT c.nombre, SUM(t.monto) AS importe
    FROM transacciones t
    JOIN terminales te ON te.id_terminal = t.id_terminal
    JOIN comercios  c  ON c.id_comercio  = te.id_comercio
    WHERE t.estatus = 'APROBADA'
    GROUP BY c.nombre
),
acumulado AS (
    SELECT nombre, importe,
           SUM(importe) OVER (ORDER BY importe DESC)     AS importe_acumulado,
           SUM(importe) OVER ()                          AS importe_total
    FROM por_comercio
)
SELECT nombre, importe,
       ROUND(100.0 * importe_acumulado / importe_total, 2) AS pct_acumulado
FROM acumulado
ORDER BY importe DESC;

-- H4. Evolucion del ticket promedio mes a mes, por ciudad.
WITH por_mes_ciudad AS (
    SELECT c.ciudad,
           DATE_TRUNC('month', t.fecha_hora)::DATE AS mes,
           AVG(t.monto)                            AS ticket
    FROM transacciones t
    JOIN terminales te ON te.id_terminal = t.id_terminal
    JOIN comercios  c  ON c.id_comercio  = te.id_comercio
    WHERE t.estatus = 'APROBADA'
    GROUP BY c.ciudad, mes
)
SELECT ciudad, mes,
       ROUND(ticket, 2) AS ticket_promedio,
       ROUND(ticket - LAG(ticket) OVER (PARTITION BY ciudad ORDER BY mes), 2)
           AS variacion
FROM por_mes_ciudad
ORDER BY ciudad, mes;


-- Pregunta de cierre de la sesion:
-- estas consultas recorren la tabla completa cada vez. Con cinco mil
-- filas responden de inmediato. Que ocurre con veinte millones, y como
-- se sabe que hace el motor por dentro para resolverlas.
