# c2_s2_b4_taller.md
## Taller de la sesion 2.2

**Bases de Datos y SQL con Python | BSG Institute**

Duracion estimada: 50 minutos dentro de la sesion.
Entrega: un archivo `.sql` con las consultas, un archivo `.py` con el codigo, y
las respuestas escritas de la parte D.

Este taller aporta al componente de **trabajo en clase**, que representa el 25 por
ciento de la calificacion.

---

### Requisitos previos

Contenedor activo, base `pagos` cargada, DBeaver conectado, y `pandas`, `polars`
y `sqlalchemy` instalados.

---

## Parte A. Combinaciones

Resolver con SQL en DBeaver.

**A1.** Listar las veinte operaciones de mayor monto, mostrando identificador,
fecha, nombre del comercio, ciudad y monto. Considerar solo aprobadas.

**A2.** Obtener, para cada terminal, el nombre de su comercio y la cantidad de
operaciones que capturo.

**A3.** Listar las operaciones que tienen contracargo, mostrando el nombre del
cliente, el comercio y el monto.

**A4.** Determinar cuantos clientes no tienen ninguna operacion rechazada.

> Sugerencia: es un caso de combinacion externa con filtro sobre el lado nulo, o
> bien de `NOT EXISTS`.

**A5.** Ejecutar las dos consultas siguientes y explicar por que devuelven
distinto resultado:

```sql
SELECT COUNT(*) FROM pagos.transacciones t
LEFT JOIN pagos.contracargos cc ON cc.id_transaccion = t.id_transaccion
WHERE cc.id_contracargo IS NULL;

SELECT COUNT(*) FROM pagos.transacciones t
LEFT JOIN pagos.contracargos cc
       ON cc.id_transaccion = t.id_transaccion
      AND cc.id_contracargo IS NULL;
```

---

## Parte B. Agregaciones

**B1.** Calcular el importe aprobado por ciudad y por metodo de captura, ordenado
por importe descendente.

**B2.** Obtener la tasa de rechazo por marca de tarjeta, expresada en porcentaje
con dos decimales. Resolverlo en una sola pasada sobre la tabla.

> Sugerencia: `COUNT(*) FILTER (WHERE ...)` permite varias medidas condicionales
> sin repetir la consulta.

**B3.** Determinar los comercios cuyo ticket promedio aprobado supera los mil
pesos y que ademas tengan mas de trescientas operaciones.

**B4.** Calcular el importe aprobado por mes. Usar funciones de fecha del motor,
sin manipular cadenas.

**B5.** Explicar por que la siguiente consulta falla y corregirla:

```sql
SELECT c.nombre, SUM(t.monto) AS importe
FROM pagos.transacciones t
JOIN pagos.terminales te USING (id_terminal)
JOIN pagos.comercios  c  USING (id_comercio)
WHERE SUM(t.monto) > 1000000
GROUP BY c.nombre;
```

---

## Parte C. Subconsultas

**C1.** Listar las operaciones cuyo monto supera el triple del ticket promedio
general aprobado.

**C2.** Obtener los comercios que operan al menos cuatro terminales, resuelto con
una subconsulta en `IN`.

**C3.** Resolver C2 de nuevo, ahora con `EXISTS`. Comparar ambas soluciones y
señalar en que casos conviene cada una.

**C4.** Calcular, por ciudad, el promedio del importe total de sus comercios.
Requiere agregar en dos etapas.

**C5.** Obtener el monto maximo de cada comercio junto con el identificador de la
operacion correspondiente.

> Advertencia: `SELECT c.nombre, MAX(t.monto), t.id_transaccion` no funciona.
> Explicar por que antes de buscar la solucion.

---

## Parte D. Lectura hacia dataframes

Entregar el codigo.

**D1.** Escribir una funcion `motor()` que construya el objeto de SQLAlchemy a
partir de variables de entorno, con el controlador declarado de forma explicita.

**D2.** Leer el resultado de B1 hacia un dataframe de pandas y hacia uno de
Polars. Reportar los tipos que asigno cada biblioteca a la columna de importe.

**D3.** Leer la columna `monto` de la tabla completa con pandas. Comparar la suma
obtenida en el dataframe contra `SELECT SUM(monto)` ejecutado en el motor.
Imprimir el valor de pandas con veinte decimales y comentar el resultado.

**D4.** Escribir una funcion `resumen_por_ciudad(ciudad)` que devuelva un
dataframe con el resumen de esa ciudad. La ciudad se pasa como parametro de la
consulta.

**D5.** Materializar el resultado de B3 en una tabla llamada
`pagos.comercios_premium`, usando `to_sql`. Verificar el conteo desde DBeaver e
inspeccionar que estructura creo pandas.

---

## Parte E. Analisis y argumentacion

Responder por escrito.

**E1.** A partir del resultado de D3, explicar que ocurre con la garantia de
aritmetica exacta que se establecio en la sesion 2.1 al declarar la columna como
`NUMERIC`.

**E2.** Formular un criterio para decidir cuando agregar en el motor y cuando
traer las filas al dataframe. El criterio debe ser aplicable sin medir tiempos.

**E3.** Inspeccionar en DBeaver la tabla creada en D5. Señalar tres diferencias
respecto de las tablas del modelo, y explicar en que casos esa diferencia
importa y en cuales no.

**E4.** Completar el punto 5 de la ficha de seis puntos de PostgreSQL, sobre la
interfaz desde Python y la lectura hacia dataframes.

---

## Parte F. Ejercicio de extension (opcional)

**F1.** Medir el tiempo de las dos rutas de agregacion sobre la tabla completa, y
estimar como cambiaria la comparacion con veinte millones de filas.

**F2.** Reescribir la consulta C5 usando `DISTINCT ON`, que es una extension
propia de PostgreSQL. Comparar la legibilidad contra la solucion con subconsulta.

**F3.** Leer el mismo resultado con `pl.read_database` sobre una conexion de
psycopg y con `pl.read_database_uri` mediante connectorx. Comparar los tipos
resultantes.

---

## Criterios de evaluacion

| Criterio | Peso |
|---|---|
| Correccion de las combinaciones, en especial A4 y A5 | 25% |
| Agregaciones y comprension del orden de evaluacion (parte B) | 25% |
| Subconsultas, en especial C5 (parte C) | 20% |
| Lectura hacia dataframes con parametros (parte D) | 15% |
| Calidad del argumento en la parte E, en especial E1 y E2 | 15% |

Una consulta que devuelve el resultado correcto mediante una combinacion que
multiplica filas obtiene calificacion parcial. Verificar siempre el conteo.

---

## Cierre

Las consultas de este taller producen un agregado por grupo: una fila de salida
por cada comercio, ciudad o mes. Queda abierta la pregunta que da paso a la
sesion 2.3: que ocurre cuando la pregunta necesita comparar cada operacion contra
su propio grupo, por ejemplo el gasto acumulado de una tarjeta operacion por
operacion, sin perder el detalle.
