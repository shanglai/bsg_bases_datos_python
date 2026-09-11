# c2_s5_b5_taller.md
## Taller de la sesion 2.5

**Bases de Datos y SQL con Python | BSG Institute**

Duracion estimada: 50 minutos dentro de la sesion.
Entrega: un archivo `.sql`, un archivo `.py`, y las respuestas escritas de la
parte E con los planes de ejecucion registrados.

Este taller aporta al componente de **trabajo en clase**, que representa el 25 por
ciento de la calificacion. Es el ultimo taller del capitulo 2.

---

### Requisitos previos

Contenedor activo, base `pagos` cargada, y la tabla
`pagos.transacciones_volumen` con dos millones de filas. Si no existe:

```bash
python c2_s5_b2_volumen.py
```

---

## Parte A. Leer un plan

Para cada punto, registrar el plan completo y el tiempo de ejecucion.

**A1.** Eliminar todos los indices de `transacciones_volumen` y obtener el plan
de esta consulta:

```sql
SELECT COUNT(*), SUM(monto)
FROM pagos.transacciones_volumen
WHERE id_tarjeta = 77
  AND fecha_hora BETWEEN '2026-02-01' AND '2026-02-28';
```

**A2.** Identificar en ese plan: el tipo de recorrido, las filas estimadas, las
filas reales y el tiempo de ejecucion.

**A3.** Ejecutar `EXPLAIN (ANALYZE, BUFFERS)` sobre la misma consulta. Indicar
cuantos bloques se leyeron de memoria y cuantos de disco.

**A4.** Repetir A3 de inmediato. Explicar por que cambian los numeros de bloques.

---

## Parte B. Crear y medir

**B1.** Crear un indice que sirva para la consulta de A1. Justificar el orden de
las columnas.

**B2.** Obtener el plan de nuevo. Registrar el cambio de recorrido y la relacion
entre los tiempos.

**B3.** Medir el tamano del indice y compararlo con el de la tabla.

**B4.** Escribir una consulta que aproveche el indice creado y otra que, teniendo
el mismo indice disponible, no lo use. Explicar la diferencia.

**B5.** Crear un indice de cobertura con `INCLUDE (monto)` y verificar que el
plan cambia a `Index Only Scan`. Explicar que significa ese nombre.

---

## Parte C. Cuando el indice no se usa

Para cada caso, registrar el plan y explicar el motivo.

**C1.** Un predicado que coincide con la mayoria de las filas.

**C2.** Una funcion aplicada sobre la columna indexada, por ejemplo
`WHERE DATE(fecha_hora) = '2026-03-15'`.

**C3.** Reescribir C2 como un rango y verificar que ahora si usa el indice.

**C4.** Un filtro solo sobre la segunda columna de un indice compuesto.

**C5.** Consultar `pg_stat_user_indexes` y detectar si algun indice tiene cero
lecturas. Explicar por que un indice no usado no es neutro.

---

## Parte D. Transacciones desde Python

**D1.** Escribir una funcion `transferir(origen, destino, monto)` sobre una tabla
de saldos con restriccion `CHECK (saldo >= 0)`. Debe aplicar los dos movimientos
o ninguno.

**D2.** Demostrar que la funcion revierte de forma correcta cuando el saldo no
alcanza. Mostrar el estado antes y despues.

**D3.** Provocar un error de tabla inexistente sobre una conexion, y despues
ejecutar `SELECT 1` sobre la misma conexion. Registrar el segundo mensaje de
error y explicarlo.

**D4.** Corregir D3 de modo que la conexion quede utilizable tras el error.

**D5.** Escribir una carga por lotes que inserte una lista de registros, algunos
de los cuales violan una restriccion. Los registros validos deben quedar
guardados y los invalidos descartados, sin perder el lote completo.

**D6.** Escribir una funcion que capture al menos tres tipos distintos de error
del motor y devuelva un mensaje comprensible para cada uno, usando el atributo
`sqlstate`.

---

## Parte E. Analisis y argumentacion

**E1.** Comparar el tiempo de una insercion masiva con y sin indices. Reportar la
relacion y explicar el resultado.

**E2.** Formular un criterio para decidir si conviene crear un indice. Debe
considerar la frecuencia de la consulta, la selectividad del filtro, el costo de
escritura y el espacio.

**E3.** El plan reporta filas estimadas y filas reales. Explicar que significa una
diferencia grande entre ambas y que se hace al respecto.

**E4.** Un compañero propone crear un indice sobre cada columna de la tabla, por
si acaso. Argumentar por que es una mala idea.

**E5.** Explicar por que una medicion basada en una sola ejecucion no es
confiable, y describir un procedimiento de medicion defendible.

**E6.** Cerrar la ficha de seis puntos de PostgreSQL. El capitulo 2 termina aqui,
de modo que esta version es la que entra en la matriz de decision del proyecto
final.

---

## Parte F. Ejercicio de extension (opcional)

**F1.** Crear un indice parcial que solo cubra las operaciones rechazadas.
Comparar su tamano contra el indice completo equivalente.

**F2.** Investigar `pg_stat_statements` y explicar que aporta frente a
`EXPLAIN ANALYZE`.

**F3.** Ejecutar dos transacciones simultaneas desde dos conexiones distintas,
ambas modificando la misma fila. Observar el bloqueo y explicarlo.

**F4.** Comparar el comportamiento de una consulta bajo `READ COMMITTED` y bajo
`REPEATABLE READ`, con una modificacion confirmada por otra conexion entre dos
lecturas.

---

## Criterios de evaluacion

| Criterio | Peso |
|---|---|
| Lectura correcta del plan, en especial A2 y A4 | 20% |
| Creacion y medicion del indice (parte B) | 20% |
| Los cuatro casos en que el indice no se usa (parte C) | 25% |
| Transacciones y manejo de errores (parte D) | 20% |
| Calidad del argumento en la parte E, en especial E2 y E4 | 15% |

Una medicion reportada sin indicar el numero de repeticiones ni el estadistico
utilizado obtiene calificacion parcial, aunque el numero sea correcto.

---

## Cierre

El capitulo 2 llevo el modelo relacional del archivo unico al servidor, de la
consulta simple al analisis, y del ejemplo de juguete al volumen y la
concurrencia.

Queda abierta la pregunta que da paso al capitulo 3: la sesion 2.4 mostro que
PostgreSQL almacena, indexa y consulta documentos. Que aporta entonces un motor
construido enteramente alrededor de esa idea, y en que casos ese aporte justifica
renunciar a lo que este capitulo construyo.
