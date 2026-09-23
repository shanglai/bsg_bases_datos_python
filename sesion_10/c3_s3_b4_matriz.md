# c3_s3_b4_matriz.md
## Matriz de decision

**Bases de Datos y SQL con Python | BSG Institute | Capitulo 3, Sesion 3.3**

Este documento es el producto acumulado del curso. Cada sesion aporto un renglon
o una columna, y aqui se consolida.

Es tambien el entregable central del proyecto final: no se evalua que el
participante elija bien, sino que sustente por que.

---

## 1. Las cuatro fichas de seis puntos

### SQLite (sesiones 1.1 y 1.2)

| Punto | Contenido |
|---|---|
| Modelo de datos | Relacional, esquema declarado, tipado dinamico por valor |
| Eficiente en | Lectura local, prototipo, archivo que se copia y se versiona |
| Garantias | Integridad de entidad, referencial y de dominio. Las llaves foraneas requieren activarse por conexion |
| Escritura frente a lectura | Un escritor a la vez sobre todo el archivo |
| Interfaz desde Python | `sqlite3`, en la biblioteca estandar. Interfaz DB-API |
| Conviene | Aplicacion local de un solo usuario, prueba, distribucion de un conjunto de datos |
| No conviene | Concurrencia de escritura, operacion continua con varios clientes |

### PostgreSQL (capitulo 2)

| Punto | Contenido |
|---|---|
| Modelo de datos | Relacional con esquema estricto, mas soporte documental en columnas JSONB |
| Eficiente en | Combinaciones, agregaciones, analisis con ventanas, consulta expresiva sobre datos relacionados |
| Garantias | Integridad completa, aplicada siempre y desde la declaracion. Transacciones sobre varias tablas |
| Escritura frente a lectura | La escritura paga restricciones e indices. La lectura paga recomposicion |
| Interfaz desde Python | `psycopg` 3, SQLAlchemy 2.0, lectura a pandas y Polars |
| Conviene | Integridad importante, relaciones estables, analisis expresivo, parte variable acotada |
| No conviene | Esquema que varia en su totalidad, reparto horizontal automatico |

### MongoDB (capitulo 3)

| Punto | Contenido |
|---|---|
| Modelo de datos | Coleccion de documentos independientes, anidados, sin esquema declarado |
| Eficiente en | Lectura de un agregado completo, busqueda en arreglos con indices multiclave, consulta sobre campos anidados |
| Garantias | Unicidad de `_id` y atomicidad de un documento. El resto es opcional y se declara |
| Escritura frente a lectura | La lectura no paga combinaciones. La escritura paga redundancia |
| Interfaz desde Python | PyMongo. Documentos y filtros como diccionarios |
| Conviene | Estructura que varia por completo, lectura del agregado entero, reparto horizontal |
| No conviene | Datos compartidos que cambian, integridad referencial, analisis que cruza colecciones |

### BigQuery (capitulo 4, pendiente)

Se completa en las sesiones 4.3 y 4.4.

---

## 2. Comparacion punto por punto

| Criterio | PostgreSQL | MongoDB | Diferencia real |
|---|---|---|---|
| Estructura variable | JSONB en una columna | Todo el documento | Donde vive la parte variable, no si se puede |
| Validacion de estructura | Obligatoria desde la declaracion | Opcional, se agrega despues | Que ocurre por omision |
| Integridad referencial | Llaves foraneas aplicadas por el motor | No existe | Diferencia sin equivalente |
| Transacciones | Entre tablas, siempre | Entre documentos, con requisitos | Costo de configuracion |
| Consulta analitica | SQL, ventanas, CTE | Canalizacion de agregacion | Expresividad frente a familiaridad |
| Busqueda en arreglos | Indice GIN sobre JSONB | Indice multiclave nativo | Comodidad |
| Combinar entidades | JOIN, optimizado por el motor | `$lookup`, posicion decidida a mano | Ventaja relacional |
| Corregir dato compartido | Una fila, atomico | N documentos, no atomico | Ventaja relacional |
| Reparto horizontal | Manual o por extension | Nativo | Ventaja documental |
| Herramientas gratuitas | DBeaver Community y otras | Compass | Empate practico |

---

## 3. Preguntas que deciden

Se responden sobre el sistema concreto, no en general. El orden importa: las
primeras pesan mas.

**1. Que fraccion del modelo tiene estructura estable.**
Casi toda, con una porcion variable acotada, apunta a PostgreSQL con JSONB.
Estructura que varia por completo y de forma impredecible apunta a MongoDB.

**2. Hay datos compartidos que cambian.**
Si los hay y cambian, la denormalizacion cobra caro. Es el criterio mas
subestimado.

**3. Quien debe garantizar la consistencia.**
Si la respuesta es "el motor, siempre", el modelo relacional lo hace por omision.
Si es "la aplicacion, y confiamos en ella", ambos sirven.

**4. Cuantos sistemas escriben sobre estos datos.**
Uno solo, con un equipo estable, admite garantias en la aplicacion. Varios
sistemas, con equipos distintos, exigen que la garantia viva en el motor.

**5. La consulta habitual lee un agregado completo o cruza entidades.**
Leer el agregado entero favorece al documento. Cruzar entidades favorece a lo
relacional.

**6. El volumen excede lo que cabe en un servidor.**
Si lo excede de verdad, el reparto horizontal nativo es una ventaja real. Conviene
comprobar el dato antes de usarlo como argumento.

**7. Que sabe operar el equipo.**
Criterio legitimo y no tecnico. Conviene declararlo como lo que es.

---

## 4. Plantilla para el proyecto final

Se completa una tabla por cada motor considerado, incluidos los descartados.

| | |
|---|---|
| **Requerimiento** | |
| **Motor propuesto** | |
| **Fraccion del modelo con estructura estable** | |
| **Datos compartidos que cambian** | |
| **Quien garantiza la consistencia** | |
| **Sistemas que escriben** | |
| **Consulta habitual** | |
| **Volumen esperado a 24 meses** | |
| **Conocimiento del equipo** | |
| **Decision** | |
| **Que se cede al elegirlo** | |
| **Que haria cambiar esta decision** | |

Los dos ultimos renglones son los que se evaluan. Una propuesta que no declara
que cede, o que no identifica que la haria cambiar, esta incompleta.

---

## 5. El caso de estudio, resuelto

Aplicacion de los criterios al caso de pagos, como ejemplo trabajado.

| Pregunta | Respuesta en el caso |
|---|---|
| Fraccion estable | Alta. Comercios, terminales, clientes, tarjetas y transacciones tienen estructura fija. Solo el mensaje de autorizacion varia |
| Datos compartidos que cambian | Si. Nombre y categoria del comercio, correo del cliente |
| Quien garantiza la consistencia | El motor. Es un sistema financiero con obligaciones de auditoria |
| Sistemas que escriben | Varios: captura en terminal, contracargos, conciliacion |
| Consulta habitual | Cruza entidades: importe por comercio, por ciudad, por marca |
| Volumen | Alto en transacciones, bajo en catalogos |
| Equipo | SQL es conocimiento comun |

**Decision para el caso: PostgreSQL con JSONB.**

**Que se cede:** el reparto horizontal automatico, y la comodidad de leer la
operacion completa sin combinaciones.

**Que haria cambiar esta decision:** que el volumen de transacciones excediera lo
que un servidor puede sostener, o que el mensaje de autorizacion dejara de ser
una porcion acotada y el modelo entero se volviera variable.

Conviene señalar algo incomodo: este es el resultado para ESTE caso. Un catalogo
de productos de comercio electronico, con atributos que difieren por categoria y
sin obligaciones de integridad entre entidades, daria el resultado contrario con
los mismos criterios.
