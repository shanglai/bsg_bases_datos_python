# c4_final_b7_taller.md
## Ejercicios de la sesion final

**Bases de Datos y SQL con Python | BSG Institute**

Dos ejercicios cortos, guiados, dentro de la sesion. No hay entrega separada: lo
que se evalua del cierre es el proyecto final.

---

## Ejercicio 1. Redis, en Cloud Shell

**Duracion: 15 minutos.**

### Preparacion

1. Abrir Cloud Shell en la consola de GCP, con el icono de terminal arriba a la
   derecha.
2. Instalar el controlador:

```bash
pip install redis --quiet
```

3. Subir `c4_final_b4_redis_alumno.py` con el menu de tres puntos de Cloud Shell,
   o pegarlo con el editor.

### Ejecucion

```bash
python c4_final_b4_redis_alumno.py HOST TU_USUARIO TU_CLAVE
```

El instructor reparte los tres valores. Cada quien tiene su propio usuario.

### Que observar

**A.** Las cinco estructuras, y para que sirve cada una. Anotar cual usaria para
cada uno de estos casos del sistema de pagos:

| Caso | Estructura |
|---|---|
| Contar intentos por tarjeta en un minuto | |
| Saber si una tarjeta esta bloqueada | |
| Importe acumulado por comercio del dia, ordenado | |
| Perfil de riesgo con varios campos | |
| Operaciones pendientes de revision manual | |

**B.** La expiracion. Ningun otro motor del curso la tiene como propiedad de la
clave. En PostgreSQL habria que guardar una fecha de caducidad y borrar con un
proceso aparte.

**C.** El limitador. Explicar por que `INCR` funciona con dos procesos
simultaneos y un `SELECT` seguido de `UPDATE` no.

**D.** El aislamiento. Cuatro operaciones que devuelven `NOPERM`. Anotar por que
`KEYS *` esta prohibido para todos y no solo para los alumnos.

### Ejercicio adicional

Escribir un contador de operaciones por comercio usando un conjunto ordenado,
alimentarlo con diez operaciones, y obtener los tres primeros. Todo dentro de su
propio prefijo.

---

## Ejercicio 2. BigQuery, en la consola

**Duracion: 15 minutos.**

### Preparacion

Abrir BigQuery Studio en la consola, seleccionar el proyecto de la clase, y
localizar el conjunto `pagos`, tabla `operaciones`.

**Antes de ejecutar cualquier consulta, mirar arriba a la derecha el estimado de
bytes que va a procesar.** Ese es el precio.

### Los cinco ejercicios

**1. El costo de las columnas.**

Ejecutar ambas y anotar el estimado de cada una:

```sql
SELECT * FROM `PROYECTO.pagos.operaciones` LIMIT 10;

SELECT estatus, COUNT(*) FROM `PROYECTO.pagos.operaciones` GROUP BY estatus;
```

Explicar por que el `LIMIT 10` no abarata la primera.

**2. Subcolumnas.**

Obtener el importe aprobado por comercio, usando `comercio.nombre`. Comparar el
codigo con la version de PostgreSQL de la sesion 2.2, que necesitaba dos `JOIN`.

**3. Columnas repetidas.**

Contar cuantas veces aparece cada senal de riesgo, con `UNNEST`.

Despues contar las filas totales y las que quedan tras el `UNNEST`. Explicar la
diferencia y corregirla con `LEFT JOIN UNNEST`.

**4. Particiones.**

Ejecutar la misma agregacion con y sin filtro de fecha. Anotar los dos estimados
de bytes.

**5. El error que anula la particion.**

```sql
-- Anula la particion
WHERE DATE(fecha_hora) BETWEEN '2026-03-01' AND '2026-03-31'

-- La aprovecha
WHERE fecha_hora >= '2026-03-01' AND fecha_hora < '2026-04-01'
```

Comparar los estimados. Relacionarlo con lo visto en la sesion 2.5 sobre
funciones aplicadas a columnas indexadas.

### Ejercicio adicional

Consultar `INFORMATION_SCHEMA.JOBS_BY_PROJECT` para ver cuanto proceso de verdad
cada consulta que ejecuto, y cuales devolvieron resultado desde la cache sin
cobrar.

---

## Lo que se lleva de estos dos ejercicios

**De Redis.** La estructura se elige por la operacion, no por el dato. Y el
aislamiento en un almacen clave-valor se consigue con convencion de nombres mas
permisos, porque no hay esquemas.

**De BigQuery.** Se paga por bytes leidos. Nombrar las columnas, filtrar por la
columna de particion, y no envolverla en una funcion. El habito de mirar el
estimado antes de ejecutar vale mas que cualquier truco de sintaxis.

**De los dos juntos.** Ninguno sustituye a PostgreSQL. Redis responde durante la
operacion, BigQuery analiza despues, y el registro sigue viviendo en el motor
transaccional.
