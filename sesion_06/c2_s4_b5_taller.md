# c2_s4_b5_taller.md
## Taller de la sesion 2.4

**Bases de Datos y SQL con Python | BSG Institute**

Duracion estimada: 50 minutos dentro de la sesion.
Entrega: un archivo `.sql`, un archivo `.py` y las respuestas escritas de la
parte E.

Este taller aporta al componente de **trabajo en clase**, que representa el 25 por
ciento de la calificacion.

---

### Requisitos previos

Contenedor activo, base `pagos` cargada, columna `autorizacion` presente. Si no
existe, ejecutar `c2_s4_b2_payload.py`.

---

## Parte A. Acceso al documento

**A1.** Mostrar el mensaje de autorizacion completo de una operacion con metodo
`BANDA`, en formato legible.

**A2.** Para cada metodo de captura, listar los campos distintos que aparecen
dentro del bloque `captura`. Explicar por que no son los mismos.

**A3.** Obtener el nombre del emisor y el tiempo de respuesta de las diez
operaciones con mayor tiempo de respuesta.

**A4.** Extraer la latitud y la longitud del dispositivo usando acceso por ruta.

**A5.** Explicar la diferencia entre estas dos expresiones y verificarla con
`pg_typeof`:

```sql
autorizacion->'emisor'->'nombre'
autorizacion->'emisor'->>'nombre'
```

**A6.** Contar las operaciones cuyo puntaje de riesgo supera 90. Explicar por que
hace falta una conversion de tipo.

---

## Parte B. Busqueda dentro del documento

**B1.** Contar cuantos mensajes traen el bloque `riesgo` y cuantos no. Relacionar
el resultado con la version del protocolo.

**B2.** Obtener las operaciones rechazadas por `LIMITE_EXCEDIDO`, resuelto con el
operador de contencion.

**B3.** Resolver B2 de nuevo con `->>`. Verificar que el resultado es identico.

**B4.** Contar las operaciones que presentan la senal `dispositivo_nuevo`.

**B5.** Obtener las operaciones que traen a la vez las claves `rechazo` y
`riesgo`.

**B6.** Listar cada senal de riesgo con su numero de ocurrencias, ordenado de
mayor a menor. Requiere expandir el arreglo a filas.

---

## Parte C. Indices

**C1.** Sin ningun indice sobre `autorizacion`, obtener el plan de la consulta
B2. Registrar el tipo de recorrido y el tiempo.

**C2.** Crear un indice GIN sobre la columna y volver a obtener el plan.
Registrar el cambio.

**C3.** Obtener el plan de la consulta B3, la version con `->>`, con el indice ya
creado. Explicar el resultado.

**C4.** Ejecutar el plan de esta consulta y explicar por que el motor **no** usa
el indice:

```sql
SELECT COUNT(*) FROM pagos.transacciones
WHERE autorizacion @> '{"emisor": {"pais": "MX"}}';
```

**C5.** Crear un indice de expresion sobre el puntaje de riesgo y verificar que
una consulta de rango lo aprovecha.

**C6.** Comparar el tamano del indice GIN completo contra el de
`jsonb_path_ops`. Indicar que se pierde al elegir el segundo.

---

## Parte D. SQLAlchemy 2.0 y JSONB

**D1.** Declarar una clase mapeada para la tabla `comercios` en estilo 2.0, con
`Mapped` y `mapped_column`. No usar `Column` ni `declarative_base`.

**D2.** Escribir una consulta con `select()` y `session.execute()` que devuelva
los comercios de una ciudad recibida como parametro.

**D3.** Declarar la clase de `transacciones` incluyendo la columna
`autorizacion` como `JSONB` y `monto` como `Numeric(12, 2)`. Explicar por que el
tipo de `monto` importa.

**D4.** Escribir una consulta que cuente las operaciones de un emisor dado,
resolviendo el filtro **en el motor**, no en Python.

**D5.** Escribir la misma consulta usando el operador de contencion, de modo que
pueda aprovechar el indice GIN.

**D6.** Demostrar el problema de las consultas en cadena: recorrer los comercios
accediendo a sus terminales, contar las consultas generadas, y corregirlo con
carga anticipada.

---

## Parte E. Analisis y argumentacion

**E1.** El bloque `captura` tiene entre tres y cinco campos segun el metodo.
Calcular cuantas columnas haria falta declarar para modelarlo de forma
relacional, y que proporcion quedaria nula en cada fila.

**E2.** Explicar por que el operador `->>` comparado con texto no aprovecha el
indice GIN, mientras que `@>` si lo hace.

**E3.** El modelo relacional rechaza un estatus invalido mediante `CHECK`. El
documento acepta cualquier estructura. Proponer dos mecanismos para recuperar
parte de esa garantia sobre la columna JSONB, y señalar el limite de cada uno.

**E4.** Formular un criterio para decidir que informacion va en columnas y cual
en un documento, dentro de una misma tabla.

**E5.** Completar la ficha de seis puntos de PostgreSQL con lo aprendido sobre
datos semiestructurados. Anticipar en cuales de los seis puntos podria diferir
MongoDB.

---

## Parte F. Ejercicio de extension (opcional)

**F1.** Investigar `jsonb_path_query` y el lenguaje de rutas SQL/JSON.
Reescribir B4 con ese mecanismo.

**F2.** Escribir una consulta que detecte mensajes con estructura inesperada, por
ejemplo un `puntaje` que no sea numerico. Usar `jsonb_typeof`.

**F3.** Medir el efecto del indice GIN sobre la velocidad de escritura:
cronometrar una actualizacion masiva de la columna con y sin indice.

---

## Criterios de evaluacion

| Criterio | Peso |
|---|---|
| Acceso al documento, en especial A5 y A6 (parte A) | 20% |
| Busqueda y expansion (parte B) | 20% |
| Indices, en especial C3 y C4 (parte C) | 25% |
| SQLAlchemy 2.0 y filtrado en el motor (parte D) | 20% |
| Calidad del argumento en la parte E, en especial E3 y E4 | 15% |

Una solucion de la parte D que traiga todas las filas y filtre en Python obtiene
calificacion parcial aunque devuelva el resultado correcto.

---

## Cierre

El documento resolvio la variabilidad del mensaje, a costa de la garantia de
estructura que el modelo relacional si ofrece. Queda abierta la pregunta que da
paso al capitulo 3: si esta es la ventaja del modelo documental, y PostgreSQL ya
la tiene, que aporta MongoDB por encima de lo que se vio hoy.
