# c3_s1_b5_taller.md
## Taller de la sesion 3.1

**Bases de Datos y SQL con Python | BSG Institute**

Duracion estimada: 50 minutos dentro de la sesion.
Entrega: un archivo `.py` con el codigo y las respuestas escritas de la parte E.

Este taller aporta al componente de **trabajo en clase**, que representa el 25 por
ciento de la calificacion.

---

### Requisitos previos

Contenedor de MongoDB activo, coleccion `operaciones` cargada con
`c3_s1_b3_carga.py`, y `pymongo` instalado.

---

## Parte A. Consulta

Resolver con PyMongo. Entregar el codigo y el resultado.

**A1.** Contar las operaciones aprobadas del comercio Electro Maya.

**A2.** Listar las diez operaciones de mayor monto de la ciudad de Cancun,
mostrando identificador, monto y nombre del cliente.

**A3.** Contar las operaciones cuyo puntaje de riesgo supera 90. El puntaje vive
en `autorizacion.riesgo.puntaje`.

**A4.** Obtener las operaciones capturadas por QR cuya aplicacion sea CoDi.

**A5.** Contar cuantos documentos **no** traen el bloque `autorizacion.riesgo`.
Relacionar el resultado con lo observado en la sesion 2.4.

**A6.** Listar las operaciones de las marcas AMEX o MASTERCARD con monto superior
a 20000, ordenadas de mayor a menor.

---

## Parte B. Escritura

**B1.** Insertar un documento nuevo con la estructura completa del caso.
Verificar que quedo guardado.

**B2.** Insertar un documento con solo dos campos. Explicar por que MongoDB lo
acepta y que habria ocurrido en PostgreSQL.

**B3.** Actualizar el estatus de ese documento con `$set` y verificar que el
resto de sus campos sigue intacto.

**B4.** Repetir B3 usando `replace_one` sin `$set`. Comparar el resultado y
explicar la diferencia.

**B5.** Actualizar la categoria del comercio Cafe Aurora en **todos** sus
documentos. Reportar cuantos se modificaron.

**B6.** Eliminar los documentos creados en B1 y B2, y deshacer el cambio de B5.

---

## Parte C. El modelo documental

**C1.** Escribir la consulta que obtiene el importe aprobado por comercio, usando
la etapa de agrupacion. Comparar el codigo contra la consulta SQL equivalente de
la sesion 2.2, que necesitaba dos combinaciones.

**C2.** Contar cuantas veces se almacena el nombre del comercio Super Norteno en
la coleccion. Explicar por que.

**C3.** Escribir el codigo que corregiria una falta de ortografia en el nombre de
un comercio. Indicar cuantos documentos alcanza y compararlo con la operacion
equivalente en PostgreSQL.

**C4.** Intentar insertar un documento con un `_id` que ya existe. Registrar el
error y explicar que garantia del motor lo produjo.

**C5.** Insertar un documento donde `monto` sea la cadena `"mil pesos"` en lugar
de un numero. Verificar que MongoDB lo acepta, y despues ejecutar una suma sobre
la coleccion. Reportar que ocurre.

---

## Parte D. Comparacion directa

**D1.** Ejecutar la misma pregunta de negocio en los dos motores: importe
aprobado por comercio. Entregar ambos codigos y verificar que los resultados
coinciden.

**D2.** Medir el tiempo de ambas consultas. Reportar el metodo de medicion
conforme al criterio de la sesion 2.5.

**D3.** Explicar por que la comparacion de D2 no es concluyente sobre cual motor
es mas rapido.

---

## Parte E. Analisis y argumentacion

**E1.** El documento incorpora el comercio, el cliente y la tarjeta. Enumerar dos
ventajas y dos costos de esa decision, con evidencia de lo observado en el
taller.

**E2.** La sesion 2.4 mostro que PostgreSQL almacena, indexa y consulta
documentos JSONB. Formular al menos dos preguntas cuya respuesta permitiria
decidir si MongoDB aporta algo por encima de eso. No es necesario responderlas
todavia.

**E3.** MongoDB garantiza que la escritura de un documento es atomica, y no
garantiza nada entre documentos. Describir una situacion del caso de pagos donde
esa diferencia importe.

**E4.** Iniciar la ficha de seis puntos de MongoDB con lo observado hoy. Los
puntos 2 y 3 quedaran incompletos hasta la sesion 3.2.

---

## Parte F. Ejercicio de extension (opcional)

**F1.** Investigar el tipo `Decimal128` de MongoDB. Explicar por que el script de
carga convierte el monto a `float` y que se pierde con esa decision.

**F2.** Investigar la validacion de esquema de MongoDB. Escribir un validador que
exija que `monto` sea numerico y que `estatus` pertenezca a un conjunto de
valores.

**F3.** Comparar el tamano en disco de la coleccion contra el de las cinco tablas
equivalentes en PostgreSQL. Explicar la diferencia.

---

## Criterios de evaluacion

| Criterio | Peso |
|---|---|
| Consulta, incluidos campos anidados y operadores (parte A) | 25% |
| Escritura, en especial B4 (parte B) | 20% |
| Comprension del modelo documental, en especial C3 y C5 (parte C) | 25% |
| Comparacion entre motores (parte D) | 15% |
| Calidad del argumento en la parte E, en especial E1 y E3 | 15% |

Una respuesta que presente la flexibilidad de esquema solo como ventaja, sin
reconocer lo que se cede, obtiene calificacion parcial en la parte E.

---

## Cierre

La sesion mostro que MongoDB acepta cualquier estructura y que la lectura de una
operacion completa no requiere combinaciones.

Queda abierta la pregunta que da paso a la sesion 3.2: si el motor no valida
nada, como se responde una pregunta analitica sobre datos que pueden venir de
cualquier forma, y que herramientas ofrece MongoDB para hacerlo con eficiencia.
