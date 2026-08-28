# c2_s1_b6_taller.md
## Taller de la sesion 2.1

**Bases de Datos y SQL con Python | BSG Institute**

Duracion estimada: 50 minutos dentro de la sesion.
Entrega: los archivos `.sql` y `.py` producidos, mas las respuestas escritas de
la parte D.

Este taller aporta al componente de **trabajo en clase**, que representa el 25 por
ciento de la calificacion.

---

### Requisitos previos

- Contenedor de PostgreSQL activo
- DBeaver conectado a la base `pagos`
- Base cargada con `c2_s1_b4_carga.py`

---

## Parte A. Exploracion con DBeaver

Trabajo en el cliente grafico. Entregar una captura por punto.

**A1.** Localizar el esquema `pagos` en el navegador de objetos y expandir la
tabla `transacciones`. Identificar donde muestra DBeaver las llaves foraneas y
donde los indices.

**A2.** Abrir el diagrama entidad-relacion que DBeaver genera de forma automatica
sobre el esquema. Compararlo con `c1_s2_d2_modelo_logico.png` de la sesion 1.2 y
señalar una diferencia de representacion.

**A3.** Ubicar el comentario declarado sobre la columna `transacciones.monto` y
explicar de donde proviene.

**A4.** Ejecutar la siguiente consulta y describir que informacion entrega:

```sql
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'pagos'
ORDER BY table_name, ordinal_position;
```

---

## Parte B. Diferencias de tipo entre SQLite y PostgreSQL

Resolver con SQL en DBeaver.

**B1.** Ejecutar las consultas siguientes y explicar los resultados:

```sql
-- Comparacion directa
SELECT 0.1::float8 + 0.2::float8 = 0.3::float8     AS con_punto_flotante,
       0.1::numeric + 0.2::numeric = 0.3::numeric  AS con_decimal_exacto;

-- El valor que se obtiene en realidad
SELECT (0.1::float8 + 0.2::float8)::text AS resultado_flotante;

-- Acumulacion de diez centavos
SELECT SUM(v::float8)::text  AS suma_flotante,
       SUM(v::numeric)::text AS suma_decimal
FROM (VALUES (0.01),(0.01),(0.01),(0.01),(0.01),
             (0.01),(0.01),(0.01),(0.01),(0.01)) AS t(v);
```

Relacionar el resultado con la eleccion de `NUMERIC(12,2)` para la columna
`monto`, y estimar que ocurriria al sumar cinco mil importes.

> Nota: el tipo `REAL` de PostgreSQL tiene tan poca precision que la comparacion
> se redondea y aparenta ser correcta. `float8`, equivalente a
> `DOUBLE PRECISION`, muestra el comportamiento con claridad.

**B2.** La columna `fecha_hora` es de tipo `TIMESTAMP`, mientras que en SQLite se
almaceno como texto. Escribir una consulta que obtenga el importe aprobado por
mes utilizando funciones de fecha del motor, sin manipular cadenas.

**B3.** Intentar insertar una transaccion con `estatus = 'PENDIENTE'`. Registrar
el mensaje de error y señalar que restriccion lo produjo.

**B4.** Intentar insertar una tarjeta con `ultimos4 = '12A4'`. Registrar el
mensaje de error y explicar que valida la restriccion.

---

## Parte C. Acceso desde Python

Entregar el codigo.

**C1.** Escribir una funcion `conectar()` que construya la cadena de conexion a
partir de variables de entorno y devuelva la conexion. Ningun valor de
credencial debe aparecer en el archivo.

**C2.** Escribir una funcion `resumen_por_ciudad(ciudad)` que devuelva la
cantidad de operaciones aprobadas y el importe total de esa ciudad. La ciudad se
pasa como parametro.

**C3.** Escribir una funcion `comercios_por_categoria(categorias)` que reciba una
lista de categorias y devuelva los comercios correspondientes. Resolverlo con un
solo parametro.

> Sugerencia: `WHERE categoria = ANY(%s)` admite una lista de Python como valor.

**C4.** Modificar C2 de modo que, ante un error de conexion, la funcion emita un
mensaje comprensible en lugar del rastreo completo.

**C5.** Escribir una funcion `registrar_contracargo(id_transaccion)` que inserte
un contracargo. Debe operar dentro de una transaccion y revertir si la
transaccion referida no existe o no esta aprobada.

---

## Parte D. Analisis y argumentacion

Responder por escrito.

**D1.** Ejecutar los bloques 1 y 2 de `c2_s1_b5_parametros.py`. Explicar por que
la consulta del bloque 2 devuelve el catalogo completo, y señalar en que punto
exacto el valor dejo de comportarse como dato.

**D2.** Un compañero propone resolver el problema verificando que el valor
recibido no contenga apostrofes antes de concatenarlo. Argumentar por que esa
solucion es inferior al uso de parametros.

**D3.** Los parametros sustituyen valores pero no identificadores. Explicar por
que un nombre de tabla no puede pasarse como parametro y que mecanismo ofrece
`psycopg` para ese caso.

**D4.** El archivo `.env` no se versiona, pero `c2_s1_b2_env_ejemplo.txt` si.
Explicar el motivo de esa asimetria y señalar que limitacion tiene el archivo
`.env` como mecanismo de proteccion de credenciales.

**D5.** Completar la ficha de seis puntos de PostgreSQL y compararla con la de
SQLite de la sesion 1.1. Indicar en cuales de los seis puntos hay diferencia.

---

## Parte E. Ejercicio de extension (opcional)

**E1.** Modificar `c2_s1_b4_carga.py` para que las transacciones se carguen con
`executemany` en lugar de `COPY`. Medir el tiempo de ambas versiones y reportar
la diferencia.

**E2.** Detener el contenedor con `stop` y volver a levantarlo. Verificar que los
datos siguen presentes y explicar que pieza del archivo de composicion lo
garantiza.

**E3.** Abrir dos conexiones simultaneas desde DBeaver y desde Python, y ejecutar
una consulta en cada una al mismo tiempo. Contrastar el comportamiento con la
limitacion de escritura de SQLite señalada en la sesion 1.2.

---

## Criterios de evaluacion

| Criterio | Peso |
|---|---|
| Exploracion del modelo en DBeaver (parte A) | 15% |
| Comprension de las diferencias de tipo (parte B) | 25% |
| Uso de parametros y manejo de credenciales (parte C) | 30% |
| Calidad del argumento en la parte D, en especial D2 | 30% |

Una funcion de la parte C que construya la condicion por concatenacion de
cadenas, o que contenga una credencial escrita en el archivo, obtiene
calificacion parcial aunque devuelva el resultado correcto.

---

## Cierre

La sesion resolvio el acceso seguro y la carga. Queda abierta la pregunta que da
paso a la sesion 2.2: los datos ya estan en seis tablas separadas, de modo que
responder una pregunta de negocio exige recomponerlos. Como se consulta
informacion que reside en varias tablas a la vez.
