-- =====================================================================
-- c2_s4_b3_jsonb.sql
-- Sesion 2.4: datos semiestructurados en PostgreSQL
--
-- Motor: PostgreSQL
-- Base:  pagos, con la columna transacciones.autorizacion cargada por
--        c2_s4_b2_payload.py
-- Uso:   se ejecuta desde DBeaver, bloque por bloque
-- =====================================================================

SET search_path TO pagos;


-- ---------------------------------------------------------------------
-- Bloque A. El problema que abre la sesion
--
-- El mensaje de autorizacion llega anidado y su forma depende del
-- metodo de captura. Modelarlo con columnas obligaria a declararlas
-- todas y dejarlas nulas casi siempre.
-- ---------------------------------------------------------------------

-- A1. Un mensaje completo, tal como llega.
SELECT jsonb_pretty(autorizacion)
FROM transacciones
WHERE metodo_captura = 'CONTACTLESS'
LIMIT 1;

-- A2. El mismo bloque, con otro metodo. Los campos son distintos.
SELECT jsonb_pretty(autorizacion->'captura')
FROM transacciones
WHERE metodo_captura = 'QR'
LIMIT 1;

-- A3. Cuantos campos distintos existen en el bloque captura, por metodo.
--     jsonb_object_keys expande el objeto a una fila por clave.
SELECT autorizacion->'captura'->>'metodo'              AS metodo,
       STRING_AGG(DISTINCT campo, ', ' ORDER BY campo) AS campos
FROM transacciones,
     jsonb_object_keys(autorizacion->'captura') AS campo
GROUP BY metodo
ORDER BY metodo;

-- A4. Cuantas columnas habria que declarar para cubrir todo el mensaje.
SELECT COUNT(DISTINCT campo) AS claves_de_primer_nivel
FROM transacciones, jsonb_object_keys(autorizacion) AS campo;


-- ---------------------------------------------------------------------
-- Bloque B. JSON frente a JSONB
--
-- PostgreSQL ofrece dos tipos. JSON conserva el texto original tal cual.
-- JSONB lo descompone en una representacion binaria.
-- ---------------------------------------------------------------------

-- B1. JSON conserva el orden de las claves, los espacios y los
--     duplicados. JSONB normaliza y descarta el duplicado.
SELECT '{"b": 1, "a": 2, "a": 3}'::json  AS como_json,
       '{"b": 1, "a": 2, "a": 3}'::jsonb AS como_jsonb;

-- B2. Solo JSONB admite indices y el operador de contencion.
--     La eleccion del curso es JSONB por esas dos razones.
SELECT '{"a": 1}'::jsonb @> '{"a": 1}'::jsonb AS contiene;


-- ---------------------------------------------------------------------
-- Bloque C. Operadores de acceso
--
--   ->    devuelve jsonb
--   ->>   devuelve texto
--   #>    devuelve jsonb siguiendo una ruta
--   #>>   devuelve texto siguiendo una ruta
-- ---------------------------------------------------------------------

-- C1. La diferencia entre -> y ->>
SELECT id_transaccion,
       autorizacion->'emisor'            AS objeto_emisor,
       autorizacion->'emisor'->>'nombre' AS nombre_texto,
       pg_typeof(autorizacion->'emisor')            AS tipo_flecha_simple,
       pg_typeof(autorizacion->'emisor'->>'nombre') AS tipo_flecha_doble
FROM transacciones
LIMIT 3;

-- C2. Acceso por ruta. Equivale a encadenar flechas y se lee mejor
--     cuando el anidamiento es profundo.
SELECT id_transaccion,
       autorizacion#>>'{dispositivo,ubicacion,lat}' AS latitud,
       autorizacion#>>'{dispositivo,ubicacion,lon}' AS longitud
FROM transacciones
LIMIT 5;

-- C3. Acceso a un elemento de arreglo, por posicion.
SELECT id_transaccion,
       autorizacion#>>'{riesgo,senales,0}' AS primera_senal
FROM transacciones
WHERE jsonb_array_length(COALESCE(autorizacion#>'{riesgo,senales}', '[]'::jsonb)) > 0
LIMIT 5;

-- C4. Error frecuente: comparar sin convertir el tipo.
--     El operador ->> devuelve texto, de modo que la comparacion
--     numerica exige una conversion explicita.
SELECT COUNT(*) AS puntaje_alto
FROM transacciones
WHERE (autorizacion#>>'{riesgo,puntaje}')::INT > 90;


-- ---------------------------------------------------------------------
-- Bloque D. Operadores de existencia y contencion
--
--   ?     la clave existe en el primer nivel
--   ?|    existe al menos una de las claves
--   ?&    existen todas las claves
--   @>    el documento contiene a otro
-- ---------------------------------------------------------------------

-- D1. Mensajes que traen el bloque de riesgo.
--     Alrededor de un seis por ciento no lo trae, porque proviene de
--     una version anterior del protocolo.
SELECT autorizacion->>'version' AS version,
       COUNT(*)                                             AS total,
       COUNT(*) FILTER (WHERE autorizacion ? 'riesgo')      AS con_riesgo,
       COUNT(*) FILTER (WHERE NOT autorizacion ? 'riesgo')  AS sin_riesgo
FROM transacciones
GROUP BY version
ORDER BY total DESC;

-- D2. Contencion: mensajes rechazados por fondos insuficientes.
SELECT COUNT(*) AS rechazos_por_fondos
FROM transacciones
WHERE autorizacion @> '{"rechazo": {"codigo": "FONDOS_INSUFICIENTES"}}';

-- D3. La misma consulta con ->>. Da el mismo resultado y no puede
--     aprovechar el indice GIN del bloque E.
SELECT COUNT(*) AS rechazos_por_fondos
FROM transacciones
WHERE autorizacion->'rechazo'->>'codigo' = 'FONDOS_INSUFICIENTES';

-- D4. Contencion dentro de un arreglo.
SELECT COUNT(*) AS con_geo_inusual
FROM transacciones
WHERE autorizacion @> '{"riesgo": {"senales": ["geo_inusual"]}}';

-- D5. Varias claves a la vez.
SELECT COUNT(*) AS completos
FROM transacciones
WHERE autorizacion ?& array['emisor', 'dispositivo', 'captura', 'riesgo'];


-- ---------------------------------------------------------------------
-- Bloque E. Indices GIN
--
-- Un indice B-tree ordena valores escalares y no sirve para buscar
-- dentro de un documento. GIN indexa el contenido: cada clave y cada
-- valor apuntan a las filas que los contienen.
-- ---------------------------------------------------------------------

-- E1. Sin indice, toda busqueda dentro del documento recorre la tabla.
EXPLAIN ANALYZE
SELECT COUNT(*) FROM transacciones
WHERE autorizacion @> '{"captura": {"aplicacion": "CoDi"}}';

-- E2. Indice GIN sobre la columna completa.
CREATE INDEX idx_autorizacion_gin ON transacciones USING GIN (autorizacion);
ANALYZE transacciones;

-- E3. La misma consulta, ya con indice. El plan cambia de Seq Scan a
--     Bitmap Index Scan sobre idx_autorizacion_gin.
EXPLAIN ANALYZE
SELECT COUNT(*) FROM transacciones
WHERE autorizacion @> '{"captura": {"aplicacion": "CoDi"}}';

-- E4. Un predicado mas selectivo aprovecha mejor el indice.
--     Tres senales de riesgo simultaneas ocurren en pocas filas.
EXPLAIN ANALYZE
SELECT COUNT(*) FROM transacciones
WHERE autorizacion @> '{"riesgo": {"senales": ["geo_inusual",
                                               "monto_atipico",
                                               "hora_inusual"]}}';

-- E5. Un predicado POCO selectivo no usa el indice, y hace bien.
--     Este emisor aparece en cerca de una de cada seis filas. Leer el
--     indice y despues visitar esas filas cuesta mas que recorrer la
--     tabla de corrido.
EXPLAIN ANALYZE
SELECT COUNT(*) FROM transacciones
WHERE autorizacion @> '{"emisor": {"nombre": "BANORTE"}}';

-- Observacion que conviene registrar:
--   Un indice existente no garantiza que se use. El planificador estima
--   cuantas filas devolvera el filtro y elige. Con baja selectividad,
--   el recorrido secuencial gana.
--   Crear un indice y suponer que se usa es un error de diagnostico.
--   El plan es la unica forma de saberlo, y se estudia en la sesion 2.5.

-- E6. El operador ->> no puede usar el indice GIN de la columna.
--     Devuelve el mismo resultado que D2 y siempre recorre la tabla.
EXPLAIN ANALYZE
SELECT COUNT(*) FROM transacciones
WHERE autorizacion->'captura'->>'aplicacion' = 'CoDi';

-- E7. La clase de operadores jsonb_path_ops produce un indice mas
--     pequeno y mas rapido, a cambio de soportar solo @>
--     (no soporta ? ni ?| ni ?&).
CREATE INDEX idx_autorizacion_path ON transacciones
    USING GIN (autorizacion jsonb_path_ops);

SELECT indexname,
       pg_size_pretty(pg_relation_size(('pagos.' || indexname)::regclass)) AS tamano
FROM pg_indexes
WHERE tablename = 'transacciones' AND indexname LIKE 'idx_autorizacion%';

-- E8. Indice de expresion sobre un solo campo. Es un B-tree ordinario
--     y sirve para rangos, cosa que GIN no hace.
CREATE INDEX idx_puntaje_riesgo ON transacciones
    (((autorizacion#>>'{riesgo,puntaje}')::INT));
ANALYZE transacciones;

EXPLAIN ANALYZE
SELECT COUNT(*) FROM transacciones
WHERE (autorizacion#>>'{riesgo,puntaje}')::INT > 98;

-- E9. Criterio de eleccion.
--     GIN completo            varias claves, operadores ? y @>
--     GIN jsonb_path_ops      solo @>, menor tamano
--     B-tree de expresion     un campo concreto, comparaciones de rango


-- ---------------------------------------------------------------------
-- Bloque F. Construir y modificar documentos
-- ---------------------------------------------------------------------

-- F1. Construir un objeto a partir de columnas.
SELECT jsonb_build_object(
           'id', id_transaccion,
           'monto', monto,
           'estatus', estatus
       ) AS resumen
FROM transacciones
LIMIT 3;

-- F2. Agregar filas en un arreglo de objetos.
SELECT jsonb_agg(jsonb_build_object('id', id_transaccion, 'monto', monto))
           AS operaciones
FROM (SELECT id_transaccion, monto FROM transacciones LIMIT 3) t;

-- F3. Modificar un campo anidado. jsonb_set no altera la tabla, solo
--     devuelve el documento modificado.
SELECT jsonb_pretty(
           jsonb_set(autorizacion, '{riesgo,puntaje}', '999'::jsonb)
       ) AS modificado
FROM transacciones
WHERE autorizacion ? 'riesgo'
LIMIT 1;

-- F4. Eliminar una clave.
SELECT autorizacion - 'dispositivo' AS sin_dispositivo
FROM transacciones LIMIT 1;

-- F5. Combinar dos documentos. El operador de concatenacion sustituye
--     las claves del primer nivel, no fusiona en profundidad.
SELECT '{"a": {"x": 1}, "b": 2}'::jsonb || '{"a": {"y": 9}}'::jsonb AS resultado;


-- ---------------------------------------------------------------------
-- Bloque G. Expandir el documento a filas
-- ---------------------------------------------------------------------

-- G1. Las senales de riesgo, una por fila.
SELECT senal, COUNT(*) AS ocurrencias
FROM transacciones,
     jsonb_array_elements_text(
         COALESCE(autorizacion#>'{riesgo,senales}', '[]'::jsonb)) AS senal
GROUP BY senal
ORDER BY ocurrencias DESC;

-- G2. Convertir el documento en una tabla con columnas.
SELECT t.id_transaccion, a.*
FROM transacciones t,
     jsonb_to_record(t.autorizacion) AS a(version TEXT, recibido_en TEXT)
LIMIT 5;

-- G3. La combinacion de ambos mundos: columnas relacionales y campos
--     del documento en la misma consulta.
SELECT c.nombre                                     AS comercio,
       t.metodo_captura,
       COUNT(*)                                     AS operaciones,
       ROUND(AVG((t.autorizacion#>>'{riesgo,puntaje}')::INT), 1)
           AS puntaje_promedio,
       ROUND(AVG((t.autorizacion#>>'{emisor,tiempo_respuesta_ms}')::INT), 0)
           AS respuesta_ms
FROM transacciones t
JOIN terminales te ON te.id_terminal = t.id_terminal
JOIN comercios  c  ON c.id_comercio  = te.id_comercio
WHERE t.autorizacion ? 'riesgo'
GROUP BY c.nombre, t.metodo_captura
ORDER BY puntaje_promedio DESC
LIMIT 10;


-- ---------------------------------------------------------------------
-- Bloque H. La restriccion que el documento no impone
--
-- El modelo relacional rechaza un estatus invalido. El documento no
-- rechaza nada: acepta cualquier estructura.
-- ---------------------------------------------------------------------

-- H1. El modelo relacional rechaza esto.
-- INSERT INTO transacciones (id_transaccion, fecha_hora, id_terminal,
--     id_tarjeta, monto, moneda, estatus, metodo_captura)
-- VALUES ('TRX9999999', NOW(), 1, 1, 100, 'MXN', 'PENDIENTE', 'CHIP');

-- H2. El documento acepta cualquier cosa, incluso un disparate.
SELECT '{"puntaje": "no es un numero", "senales": "tampoco es un arreglo"}'::jsonb
           AS documento_valido_pero_sin_sentido;

-- H3. Una restriccion CHECK puede recuperar parte del control.
ALTER TABLE transacciones ADD CONSTRAINT chk_autorizacion_version
    CHECK (autorizacion ? 'version');

-- H4. Comprobacion de que la restriccion opera.
-- UPDATE transacciones SET autorizacion = '{"sin": "version"}'::jsonb
-- WHERE id_transaccion = 'TRX0000001';


-- Pregunta de cierre de la sesion:
-- el documento resolvio la variabilidad del mensaje, a costa de la
-- garantia de estructura. Si esta es la ventaja de MongoDB, que aporta
-- MongoDB por encima de lo que ya hace PostgreSQL. Se responde en el
-- capitulo 3.
