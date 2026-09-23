# c3_s2_b5_taller.md
## Taller de la sesion 3.2

**Bases de Datos y SQL con Python | BSG Institute**

Duracion estimada: 50 minutos dentro de la sesion.
Entrega: un archivo `.py` con el codigo y las respuestas escritas de la parte E.

Este taller aporta al componente de **trabajo en clase**, que representa el 25 por
ciento de la calificacion.

---

### Requisitos previos

Contenedor de MongoDB activo, coleccion `operaciones` cargada, y `pymongo` y
`pandas` instalados.

---

## Parte A. Canalizacion de agregacion

**A1.** Obtener el importe aprobado por categoria de comercio, con el numero de
operaciones y el ticket promedio, ordenado por importe descendente.

**A2.** Obtener, por marca de tarjeta, el total de operaciones, las rechazadas y
el porcentaje de rechazo. Resolverlo en una sola tuberia.

> Sugerencia: `$sum` con `$cond` permite contar de forma condicional, igual que
> `COUNT(*) FILTER` en la sesion 2.2.

**A3.** Listar las tres ciudades de mayor importe, mostrando ademas la lista de
comercios distintos de cada una.

**A4.** Calcular el importe aprobado por mes. El campo `fecha_hora` es de tipo
fecha, de modo que se pueden usar operadores de fecha.

**A5.** Explicar por que estas dos tuberias devuelven lo mismo y cual conviene:

```python
[{"$match": {"estatus": "APROBADA"}}, {"$group": {...}}]
[{"$group": {...}}, {"$match": {"estatus": "APROBADA"}}]
```

---

## Parte B. Arreglos y combinaciones

**B1.** Contar cuantas veces aparece cada senal de riesgo en toda la coleccion.

**B2.** Ejecutar B1 sin `$unwind` y explicar por que el resultado es distinto.

**B3.** Determinar cuantas operaciones tienen tres o mas senales de riesgo.

**B4.** Contar los documentos que resultan de un `$unwind` sobre las senales, con
y sin `preserveNullAndEmptyArrays`. Explicar la diferencia.

**B5.** Construir una coleccion de catalogo con las siete categorias y un codigo
de giro. Combinarla con el resumen por categoria usando `$lookup`.

**B6.** Explicar dos diferencias entre `$lookup` y un `LEFT JOIN` de SQL.

---

## Parte C. Indices

**C1.** Listar los indices de la coleccion. Explicar por que existe uno sin
haberlo creado.

**C2.** Obtener el plan de esta consulta sin indices propios, y registrar la
etapa ganadora, los documentos examinados y los devueltos:

```python
{"comercio.ciudad": "Monterrey", "estatus": "APROBADA"}
```

**C3.** Crear un indice que sirva para esa consulta y volver a obtener el plan.
Justificar el orden de los campos.

**C4.** Crear un indice sobre el arreglo de senales de riesgo y verificar que una
busqueda por una senal lo aprovecha. Explicar que es un indice multiclave.

**C5.** Crear un indice unico sobre un campo de una coleccion de prueba y
demostrar que rechaza el duplicado.

**C6.** Consultar `index_information` y explicar el costo de mantener indices que
no se usan, con base en lo visto en la sesion 2.5.

---

## Parte D. Validacion de esquema y pandas

**D1.** Crear una coleccion con un validador `$jsonSchema` que exija:

- los campos `_id`, `monto` y `estatus`
- `monto` numerico y no negativo
- `estatus` dentro de un conjunto de tres valores

**D2.** Probar el validador con cinco documentos: uno correcto y cuatro que
violen cada regla. Registrar cuales se aceptan.

**D3.** Explicar la diferencia entre `validationLevel` `strict` y `moderate`, y
en que situacion sirve cada uno.

**D4.** Llevar a un dataframe el resultado de A1, usando `$project` para que
llegue ya plano.

**D5.** Llevar cien documentos completos a un dataframe con `json_normalize`.
Reportar cuantas columnas se generaron y cuantas tienen mas de la mitad de
valores nulos.

**D6.** Comparar D4 y D5 y formular el criterio para elegir entre aplanar en el
servidor o en el cliente.

---

## Parte E. Analisis y argumentacion

**E1.** La validacion de esquema recupera parte del control que la sesion 3.1
mostro ausente. Enumerar que recupera y que no.

**E2.** Un compañero propone activar validacion estricta sobre la coleccion
`operaciones`, que ya tiene cinco mil documentos cargados. Señalar dos riesgos y
proponer un camino mas seguro.

**E3.** El campo `monto` llego a este punto como flotante. Reconstruir el
recorrido desde la sesion 2.1 y explicar en que momento se pudo haber evitado.

**E4.** `$lookup` existe, pero el material sugiere preferir la incorporacion.
Formular un criterio para decidir entre ambos.

**E5.** Completar los puntos 2 y 3 de la ficha de seis puntos de MongoDB, que
quedaron pendientes en la sesion 3.1.

---

## Parte F. Ejercicio de extension (opcional)

**F1.** Investigar `$facet` y construir una tuberia que devuelva, en un solo
recorrido, el resumen por ciudad, por metodo de captura y el total general.

**F2.** Investigar los indices de texto de MongoDB y crear uno sobre el nombre
del comercio. Comparar su comportamiento con un filtro por expresion regular.

**F3.** Medir el tiempo de una tuberia con `$match` al inicio y con `$match` al
final. Reportar conforme al criterio de medicion de la sesion 2.5.

---

## Criterios de evaluacion

| Criterio | Peso |
|---|---|
| Canalizacion de agregacion, en especial A2 y A5 | 25% |
| Arreglos y combinaciones, en especial B2 y B4 | 20% |
| Indices y lectura del plan (parte C) | 25% |
| Validacion de esquema y pandas (parte D) | 15% |
| Calidad del argumento en la parte E, en especial E2 y E4 | 15% |

Una tuberia que coloca `$match` despues de `$group` o de `$unwind` obtiene
calificacion parcial aunque el resultado sea correcto.

---

## Cierre

La sesion mostro que MongoDB si tiene con que consultar, agregar, indexar y
validar. Queda abierta la pregunta que cierra el capitulo: con todo esto sobre la
mesa, y sabiendo que PostgreSQL tambien almacena, indexa y consulta documentos,
en que casos conviene cada uno. Es lo que se evalua en la sesion 3.3.
