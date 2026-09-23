# c3_s3_b5_taller.md
## Taller de la sesion 3.3

**Bases de Datos y SQL con Python | BSG Institute**

Duracion estimada: 50 minutos dentro de la sesion.
Entrega: la matriz de decision completa y las respuestas escritas.

Este taller es distinto de los anteriores: **se evalua por la calidad del
argumento, no por el resultado**. Dos participantes pueden elegir motores
distintos y ambos obtener calificacion completa, si cada uno sustenta su
eleccion.

Aporta al componente de **trabajo en clase**, que representa el 25 por ciento de
la calificacion, y es el ensayo directo del proyecto final.

---

### Requisitos previos

Ambos motores activos con el caso cargado. Las cuatro fichas de seis puntos del
curso, aunque la de BigQuery este incompleta.

---

## Parte A. Verificar la comparacion

**A1.** Ejecutar la pregunta 1 de `c3_s3_b2_comparacion.py` en ambos motores y
confirmar que los siete comercios coinciden.

**A2.** Los tiempos que imprime el script difieren. Enumerar al menos tres
razones por las que esa diferencia **no** permite afirmar que un motor es mas
rapido que el otro.

**A3.** Resolver en ambos motores: tasa de contracargo por comercio, sobre
operaciones aprobadas. Verificar que coinciden.

**A4.** Resolver en ambos motores: las cinco operaciones de mayor monto cuyo
puntaje de riesgo supere 80, mostrando comercio y emisor.

**A5.** Para cada una de A3 y A4, indicar en cual motor resulto mas breve de
escribir y por que.

---

## Parte B. Los costos que no se ven

**B1.** Ejecutar el costo 1 de `c3_s3_b3_costos.py`. Explicar por que el mismo
comercio termina con dos nombres y por que ninguna consulta lo advierte.

**B2.** Proponer dos mecanismos para evitar esa situacion en MongoDB, e indicar
que cede cada uno.

**B3.** Comparar el tamano en disco del caso en ambos motores. Explicar la
diferencia.

**B4.** Estimar cuanto trabajo costaria migrar la coleccion de MongoDB hacia un
modelo relacional. Enumerar los pasos, no el tiempo.

**B5.** Explicar la asimetria: por que salir del modelo relacional es mas barato
que entrar en el.

---

## Parte C. Escenarios

Para cada escenario, elegir motor y sustentarlo con la plantilla de
`c3_s3_b4_matriz.md`. No hay respuesta unica; se evalua el argumento.

**C1.** Un sistema de expedientes clinicos. Cada especialidad registra campos
distintos. Los datos del paciente son compartidos y se corrigen con frecuencia.
Obligaciones regulatorias de trazabilidad.

**C2.** Un catalogo de productos de comercio electronico. Los atributos difieren
por categoria: una laptop tiene procesador y memoria, una camisa tiene talla y
color. Se lee mucho mas de lo que se escribe. La ficha se muestra completa.

**C3.** Un sistema de telemetria de vehiculos. Cada modelo envia un conjunto
distinto de sensores. Volumen de millones de lecturas diarias. El analisis es por
agregacion temporal y casi nunca se lee un registro individual.

**C4.** El sistema de pagos del caso, pero con la restriccion de que debe
soportar cien veces el volumen actual y operar en tres regiones.

**C5.** Un sistema de nomina. Estructura estable, obligaciones fiscales, montos
que deben cuadrar al centavo, veinte personas del area contable consultandolo.

---

## Parte D. El argumento en contra

Para cada afirmacion, indicar si es un criterio valido, un criterio parcialmente
valido o un argumento que no resiste, y sustentarlo con evidencia del curso.

**D1.** "MongoDB es para datos no estructurados."

**D2.** "MongoDB es mas rapido que PostgreSQL."

**D3.** "Con MongoDB no hay que definir esquema, se avanza mas rapido."

**D4.** "PostgreSQL no escala."

**D5.** "Ya tenemos MongoDB operando, conviene usarlo."

---

## Parte E. La matriz

**E1.** Completar la plantilla de `c3_s3_b4_matriz.md` para el caso de pagos, sin
copiar la version resuelta del documento. Llegar a una conclusion propia.

**E2.** Completar los dos ultimos renglones con especial cuidado: que se cede al
elegir, y que haria cambiar la decision.

**E3.** Elegir uno de los escenarios de la parte C y completar la plantilla
tambien para el motor que se descarto. Explicar por que se descarto.

**E4.** Cerrar la ficha de seis puntos de MongoDB, si quedo algo pendiente de la
sesion 3.2.

---

## Parte F. Ejercicio de extension (opcional)

**F1.** Investigar las transacciones multidocumento de MongoDB. Indicar que
exigen en configuracion y que limites tienen.

**F2.** Investigar las extensiones de reparto horizontal de PostgreSQL. Evaluar
si cambian la respuesta de C4.

**F3.** Tomar un sistema real de su organizacion y aplicarle la plantilla. Es el
ejercicio que mas se parece al proyecto final.

---

## Criterios de evaluacion

| Criterio | Peso |
|---|---|
| Verificacion de que ambos motores coinciden (parte A) | 15% |
| Comprension de los costos no visibles, en especial B1 y B5 | 20% |
| Escenarios: calidad del argumento, no la eleccion (parte C) | 30% |
| Distinguir criterio de consigna (parte D) | 20% |
| Matriz completa, en especial los dos ultimos renglones (parte E) | 15% |

**Lo que no se evalua:** haber elegido el mismo motor que el instructor.

**Lo que si se evalua:** haber declarado que se cede, y haber identificado que
haria cambiar la decision. Una propuesta sin esos dos elementos esta incompleta
aunque la eleccion sea acertada.

---

## Cierre

El capitulo 3 termina con la matriz en la mano y con tres motores caracterizados.
Queda uno: el almacen analitico en la nube, que responde una pregunta que ninguno
de los tres resuelve bien.

La sesion 4.1 abre el capitulo 4 con el modelo clave-valor, y la 4.3 con
BigQuery. La matriz se completa ahi, y es la que se entrega en el proyecto final.
