-- =====================================================================
-- c2_s2_b2_consultas.sql
-- Sesion 2.2: consulta sobre varias tablas
--
-- Motor: PostgreSQL
-- Base:  pagos, esquema pagos, seis tablas cargadas en la sesion 2.1
-- Uso:   se ejecuta desde DBeaver, bloque por bloque
-- =====================================================================

SET search_path TO pagos;


-- ---------------------------------------------------------------------
-- Bloque A. El problema que abre la sesion
--
-- El modelo normalizado guarda cada dato en un solo lugar. Eso resolvio
-- la integridad y creo una consecuencia: ninguna pregunta de negocio se
-- responde ya con una sola tabla.
-- ---------------------------------------------------------------------

-- A1. La tabla de hechos no contiene un solo nombre legible.
SELECT * FROM transacciones LIMIT 5;

-- A2. Pregunta de negocio: cuanto vendio cada comercio.
--     Los datos necesarios estan en tres tablas distintas.
SELECT COUNT(*) AS filas_en_transacciones FROM transacciones;
SELECT COUNT(*) AS filas_en_terminales    FROM terminales;
SELECT COUNT(*) AS filas_en_comercios     FROM comercios;


-- ---------------------------------------------------------------------
-- Bloque B. Combinaciones
-- ---------------------------------------------------------------------

-- B1. La combinacion mas simple: hechos con su terminal.
SELECT t.id_transaccion, t.monto, te.codigo AS terminal
FROM transacciones t
JOIN terminales te ON te.id_terminal = t.id_terminal
LIMIT 10;

-- B2. Cadena de combinaciones hasta el comercio.
SELECT t.id_transaccion, t.monto, c.nombre AS comercio, c.ciudad
FROM transacciones t
JOIN terminales te ON te.id_terminal = t.id_terminal
JOIN comercios  c  ON c.id_comercio  = te.id_comercio
LIMIT 10;

-- B3. La consulta completa del caso: comercio, cliente y tarjeta.
SELECT t.id_transaccion,
       t.fecha_hora,
       c.nombre    AS comercio,
       cl.nombre   AS cliente,
       ta.marca    AS marca_tarjeta,
       t.monto
FROM transacciones t
JOIN terminales te ON te.id_terminal = t.id_terminal
JOIN comercios  c  ON c.id_comercio  = te.id_comercio
JOIN tarjetas   ta ON ta.id_tarjeta  = t.id_tarjeta
JOIN clientes   cl ON cl.id_cliente  = ta.id_cliente
ORDER BY t.monto DESC
LIMIT 10;

-- B4. USING abrevia cuando las columnas se llaman igual en ambos lados.
SELECT t.id_transaccion, c.nombre
FROM transacciones t
JOIN terminales te USING (id_terminal)
JOIN comercios  c  USING (id_comercio)
LIMIT 5;

-- B5. INNER frente a LEFT.
--     La primera devuelve solo las transacciones con contracargo.
--     La segunda devuelve todas, con nulo donde no hay contracargo.
SELECT COUNT(*) AS con_inner
FROM transacciones t
JOIN contracargos cc ON cc.id_transaccion = t.id_transaccion;

SELECT COUNT(*) AS con_left
FROM transacciones t
LEFT JOIN contracargos cc ON cc.id_transaccion = t.id_transaccion;

-- B6. El uso practico de LEFT: encontrar lo que NO tiene pareja.
SELECT COUNT(*) AS transacciones_sin_contracargo
FROM transacciones t
LEFT JOIN contracargos cc ON cc.id_transaccion = t.id_transaccion
WHERE cc.id_transaccion IS NULL;

-- B7. Error frecuente: filtrar la tabla derecha en WHERE anula el LEFT.
--     Esta consulta devuelve lo mismo que un INNER JOIN.
SELECT COUNT(*) AS left_anulado
FROM transacciones t
LEFT JOIN contracargos cc ON cc.id_transaccion = t.id_transaccion
WHERE cc.fecha_contracargo IS NULL OR cc.id_contracargo IS NOT NULL;


-- ---------------------------------------------------------------------
-- Bloque C. Agregaciones
-- ---------------------------------------------------------------------

-- C1. La pregunta del bloque A, ya resuelta.
SELECT c.nombre                AS comercio,
       COUNT(*)                AS operaciones,
       SUM(t.monto)            AS importe_total,
       ROUND(AVG(t.monto), 2)  AS ticket_promedio
FROM transacciones t
JOIN terminales te ON te.id_terminal = t.id_terminal
JOIN comercios  c  ON c.id_comercio  = te.id_comercio
WHERE t.estatus = 'APROBADA'
GROUP BY c.nombre
ORDER BY importe_total DESC;

-- C2. Agrupacion por dos columnas.
SELECT c.ciudad,
       t.metodo_captura,
       COUNT(*)     AS operaciones,
       SUM(t.monto) AS importe
FROM transacciones t
JOIN terminales te ON te.id_terminal = t.id_terminal
JOIN comercios  c  ON c.id_comercio  = te.id_comercio
WHERE t.estatus = 'APROBADA'
GROUP BY c.ciudad, t.metodo_captura
ORDER BY c.ciudad, importe DESC;

-- C3. WHERE frente a HAVING.
--     WHERE filtra filas antes de agrupar.
--     HAVING filtra grupos despues de agregar.
SELECT c.nombre,
       COUNT(*)     AS operaciones,
       SUM(t.monto) AS importe
FROM transacciones t
JOIN terminales te ON te.id_terminal = t.id_terminal
JOIN comercios  c  ON c.id_comercio  = te.id_comercio
WHERE t.estatus = 'APROBADA'          -- filtra transacciones
GROUP BY c.nombre
HAVING SUM(t.monto) > 1000000          -- filtra comercios
ORDER BY importe DESC;

-- C4. Agregacion condicional: varias medidas en una sola pasada.
SELECT c.nombre,
       COUNT(*)                                                   AS total,
       COUNT(*) FILTER (WHERE t.estatus = 'APROBADA')             AS aprobadas,
       COUNT(*) FILTER (WHERE t.estatus = 'RECHAZADA')            AS rechazadas,
       ROUND(100.0 * COUNT(*) FILTER (WHERE t.estatus = 'RECHAZADA')
             / COUNT(*), 2)                                        AS pct_rechazo
FROM transacciones t
JOIN terminales te ON te.id_terminal = t.id_terminal
JOIN comercios  c  ON c.id_comercio  = te.id_comercio
GROUP BY c.nombre
ORDER BY pct_rechazo DESC;

-- C5. Agregacion sobre fechas, con el tipo real de la sesion 2.1.
SELECT DATE_TRUNC('month', t.fecha_hora)::DATE AS mes,
       COUNT(*)     AS operaciones,
       SUM(t.monto) AS importe
FROM transacciones t
WHERE t.estatus = 'APROBADA'
GROUP BY mes
ORDER BY mes;

-- C6. Cuidado con COUNT(*) y COUNT(columna).
--     El primero cuenta filas. El segundo cuenta valores no nulos.
SELECT COUNT(*)                  AS filas,
       COUNT(fecha_contracargo)  AS con_fecha
FROM contracargos;


-- ---------------------------------------------------------------------
-- Bloque D. Subconsultas
-- ---------------------------------------------------------------------

-- D1. Subconsulta escalar: comparar contra un valor global.
SELECT id_transaccion, monto
FROM transacciones
WHERE monto > (SELECT AVG(monto) FROM transacciones WHERE estatus = 'APROBADA')
  AND estatus = 'APROBADA'
ORDER BY monto DESC
LIMIT 10;

-- D2. Subconsulta en IN.
SELECT nombre, ciudad
FROM comercios
WHERE id_comercio IN (
    SELECT id_comercio FROM terminales GROUP BY id_comercio HAVING COUNT(*) >= 4
);

-- D3. EXISTS: conviene cuando solo interesa saber si hay coincidencia.
SELECT c.nombre
FROM comercios c
WHERE EXISTS (
    SELECT 1
    FROM terminales te
    JOIN transacciones t ON t.id_terminal = te.id_terminal
    JOIN contracargos cc ON cc.id_transaccion = t.id_transaccion
    WHERE te.id_comercio = c.id_comercio
);

-- D4. Subconsulta en FROM: se agrega en dos etapas.
SELECT ciudad, ROUND(AVG(importe), 2) AS importe_promedio_por_comercio
FROM (
    SELECT c.ciudad, c.nombre, SUM(t.monto) AS importe
    FROM transacciones t
    JOIN terminales te ON te.id_terminal = t.id_terminal
    JOIN comercios  c  ON c.id_comercio  = te.id_comercio
    WHERE t.estatus = 'APROBADA'
    GROUP BY c.ciudad, c.nombre
) AS por_comercio
GROUP BY ciudad
ORDER BY importe_promedio_por_comercio DESC;

-- D5. Subconsulta correlacionada: se evalua una vez por fila externa.
--     Es la forma mas costosa. En la sesion 2.3 se resuelve mejor con
--     funciones de ventana.
SELECT c.nombre,
       (SELECT COUNT(*)
        FROM terminales te
        WHERE te.id_comercio = c.id_comercio) AS terminales
FROM comercios c
ORDER BY terminales DESC;


-- ---------------------------------------------------------------------
-- Bloque E. Orden logico de evaluacion
--
-- La consulta se escribe en un orden y el motor la evalua en otro.
-- Conocer el orden real explica por que ciertas cosas no funcionan.
--
--   1. FROM y JOIN     se arma el conjunto de filas
--   2. WHERE           se filtran filas
--   3. GROUP BY        se forman los grupos
--   4. HAVING          se filtran grupos
--   5. SELECT          se calculan las columnas de salida
--   6. ORDER BY        se ordena
--   7. LIMIT           se recorta
-- ---------------------------------------------------------------------

-- E1. Falla: el alias de SELECT no existe todavia cuando corre WHERE.
-- SELECT monto * 1.16 AS con_iva
-- FROM transacciones
-- WHERE con_iva > 1000;

-- E2. Funciona: ORDER BY se evalua despues de SELECT.
SELECT id_transaccion, monto * 1.16 AS con_iva
FROM transacciones
ORDER BY con_iva DESC
LIMIT 5;

-- E3. Falla: WHERE no puede usar una funcion de agregacion.
-- SELECT c.nombre
-- FROM comercios c JOIN terminales te USING (id_comercio)
-- WHERE COUNT(*) > 3
-- GROUP BY c.nombre;

-- E4. Funciona: la condicion sobre el agregado va en HAVING.
SELECT c.nombre, COUNT(*) AS terminales
FROM comercios c
JOIN terminales te USING (id_comercio)
GROUP BY c.nombre
HAVING COUNT(*) > 3
ORDER BY terminales DESC;


-- ---------------------------------------------------------------------
-- Bloque F. Preguntas de negocio del caso
-- ---------------------------------------------------------------------

-- F1. Los diez clientes con mayor gasto aprobado.
SELECT cl.nombre, cl.correo,
       COUNT(*)     AS operaciones,
       SUM(t.monto) AS gasto
FROM transacciones t
JOIN tarjetas ta ON ta.id_tarjeta = t.id_tarjeta
JOIN clientes cl ON cl.id_cliente = ta.id_cliente
WHERE t.estatus = 'APROBADA'
GROUP BY cl.id_cliente, cl.nombre, cl.correo
ORDER BY gasto DESC
LIMIT 10;

-- F2. Tasa de contracargo por comercio.
SELECT c.nombre,
       COUNT(*)                                          AS aprobadas,
       COUNT(cc.id_contracargo)                          AS contracargos,
       ROUND(100.0 * COUNT(cc.id_contracargo)
             / COUNT(*), 3)                              AS tasa_pct
FROM transacciones t
JOIN terminales te ON te.id_terminal = t.id_terminal
JOIN comercios  c  ON c.id_comercio  = te.id_comercio
LEFT JOIN contracargos cc ON cc.id_transaccion = t.id_transaccion
WHERE t.estatus = 'APROBADA'
GROUP BY c.nombre
ORDER BY tasa_pct DESC;

-- F3. Comercios sin ninguna operacion rechazada.
SELECT c.nombre
FROM comercios c
WHERE NOT EXISTS (
    SELECT 1
    FROM terminales te
    JOIN transacciones t ON t.id_terminal = te.id_terminal
    WHERE te.id_comercio = c.id_comercio
      AND t.estatus = 'RECHAZADA'
);

-- F4. Distribucion horaria de la operacion.
SELECT EXTRACT(HOUR FROM fecha_hora)::INT AS hora,
       COUNT(*)                            AS operaciones
FROM transacciones
WHERE estatus = 'APROBADA'
GROUP BY hora
ORDER BY hora;


-- Pregunta de cierre de la sesion:
-- todas estas consultas producen un agregado por grupo. Que ocurre
-- cuando la pregunta necesita comparar cada fila contra su propio
-- grupo, por ejemplo el gasto acumulado de una tarjeta operacion
-- por operacion.
