# c2_s3_b4_taller.md
## Taller de la sesion 2.3

**Bases de Datos y SQL con Python | BSG Institute**

Duracion estimada: 50 minutos dentro de la sesion.
Entrega: un archivo `.sql` con las consultas y las respuestas escritas de la
parte E.

Este taller aporta al componente de **trabajo en clase**, que representa el 25 por
ciento de la calificacion.

---

### Requisitos previos

Contenedor activo, base `pagos` cargada, DBeaver conectado.

---

## Parte A. Funciones de ventana

**A1.** Para la tarjeta 5, listar sus operaciones aprobadas con el monto, el
acumulado y el total de la tarjeta en cada fila. Ordenar por fecha.

**A2.** Calcular, para cada operacion aprobada, que porcentaje representa del
importe total de su comercio. Mostrar las diez de mayor porcentaje.

**A3.** Explicar la diferencia entre estas dos expresiones y verificarla en los
datos:

```sql
SUM(monto) OVER (PARTITION BY id_tarjeta)
SUM(monto) OVER (PARTITION BY id_tarjeta ORDER BY fecha_hora)
```

**A4.** Obtener el ticket promedio movil de las ultimas tres operaciones de cada
tarjeta.

---

## Parte B. Ordenamiento y desplazamiento

**B1.** Rankear a los clientes por cantidad de operaciones aprobadas usando las
tres funciones de rango. Explicar por que `ROW_NUMBER`, `RANK` y `DENSE_RANK`
producen valores distintos a partir del tercer lugar.

**B2.** Obtener la operacion de mayor monto de cada comercio, mostrando
identificador, comercio y monto. Resolverlo con una funcion de ventana.

> En la sesion 2.2 este mismo problema se resolvio con subconsulta. Comparar
> ambas soluciones.

**B3.** Para cada tarjeta, calcular el tiempo transcurrido desde su operacion
anterior. Listar las diez operaciones con el intervalo mas corto.

**B4.** Calcular la variacion porcentual del importe mensual respecto del mes
previo.

**B5.** Para cada ciudad, obtener sus tres comercios de mayor importe.

---

## Parte C. Expresiones de tabla comunes

**C1.** Reescribir la consulta de B5 usando `WITH`, con al menos dos CTE
encadenadas. Comparar la legibilidad contra la version con subconsultas anidadas.

**C2.** Calcular, por cliente, cuantas desviaciones estandar se aleja su gasto
total respecto del gasto promedio de todos los clientes. Requiere al menos tres
etapas.

**C3.** Determinar cuantos comercios concentran el ochenta por ciento del importe
aprobado. Usar una CTE con acumulado.

**C4.** Explicar por que la siguiente consulta falla y corregirla:

```sql
SELECT c.ciudad, c.nombre, SUM(t.monto) AS importe
FROM pagos.transacciones t
JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
WHERE ROW_NUMBER() OVER (PARTITION BY c.ciudad
                         ORDER BY SUM(t.monto) DESC) = 1
GROUP BY c.ciudad, c.nombre;
```

---

## Parte D. CTE recursiva

**D1.** Generar la serie de todas las fechas del primer trimestre de 2026, una
fila por dia.

**D2.** Combinar esa serie con las operaciones aprobadas de modo que los dias sin
actividad aparezcan con importe cero, en lugar de desaparecer del resultado.

**D3.** Sobre la tabla temporal `areas` que se crea en el bloque G del archivo de
consultas, obtener para cada area su nivel jerarquico y la ruta completa desde la
raiz.

**D4.** Modificar D3 para que muestre unicamente las areas que no tienen areas
hijas.

**D5.** Explicar que ocurriria si se omitiera la condicion de parada en una CTE
recursiva, y que mecanismo ofrece PostgreSQL para limitar el efecto.

---

## Parte E. Analisis y argumentacion

**E1.** El calculo del acumulado por tarjeta puede resolverse con una funcion de
ventana en el motor, con `cumsum` en pandas o con `cum_sum` en Polars. Formular
un criterio para elegir, sin recurrir a mediciones de tiempo.

**E2.** En la sesion 2.2 se resolvio el maximo por comercio con una subconsulta
correlacionada. Explicar por que la version con funcion de ventana es preferible,
y en que consiste la diferencia de trabajo para el motor.

**E3.** Una CTE mejora la legibilidad. Explicar si tambien mejora el desempeno,
y en que casos podria empeorarlo.

**E4.** El criterio de tres desviaciones estandar identifica operaciones atipicas
respecto del historial de su tarjeta. Señalar dos limitaciones de ese criterio
como mecanismo de deteccion de fraude.

---

## Parte F. Ejercicio de extension (opcional)

**F1.** Resolver A1 tres veces: con funcion de ventana en SQL, con pandas y con
Polars. Verificar que los tres resultados coinciden.

**F2.** Investigar la clausula `WINDOW`, que permite nombrar una definicion de
ventana y reutilizarla en varias columnas de la misma consulta. Reescribir A1 con
ella.

**F3.** Comparar `ROWS` y `RANGE` sobre una columna con valores repetidos, y
explicar en que caso cada uno da el resultado esperado.

---

## Criterios de evaluacion

| Criterio | Peso |
|---|---|
| Funciones de ventana y comprension del marco (parte A) | 25% |
| Ordenamiento y desplazamiento, en especial B1 y B5 (parte B) | 25% |
| CTE, en especial C4 (parte C) | 20% |
| CTE recursiva (parte D) | 15% |
| Calidad del argumento en la parte E, en especial E1 y E2 | 15% |

Una consulta que produce el resultado correcto colapsando el detalle con
`GROUP BY` cuando el ejercicio pedia conservarlo obtiene calificacion parcial.

---

## Cierre

Todas estas consultas recorren la tabla completa cada vez, y con cinco mil filas
responden de inmediato. Queda abierta la pregunta que da paso a la sesion 2.4:
que ocurre cuando la tabla tiene millones de filas, y como se averigua que hace
el motor por dentro para resolver una consulta.
