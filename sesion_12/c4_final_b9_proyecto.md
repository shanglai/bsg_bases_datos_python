# c4_final_b9_proyecto.md
## Proyecto final

**Bases de Datos y SQL con Python | BSG Institute**

Representa el **25 por ciento** de la calificacion del curso.

---

## 1. Que se pide

Diseñar y sustentar la arquitectura de datos de un sistema, eligiendo los motores
y justificando cada eleccion con los criterios del curso.

**No se pide construir el sistema.** Se pide el diseño, una porcion implementada,
y el argumento que sostiene las decisiones.

---

## 2. Formato de entrega

Un documento y un archivo de codigo.

| Entregable | Contenido | Peso |
|---|---|---|
| Documento | Modelo, matriz de decision, argumento | 60% |
| Codigo | Una porcion funcionando | 40% |

Extension sugerida del documento: entre seis y diez cuartillas. Se evalua la
densidad del argumento, no el numero de paginas.

---

## 3. Elegir el caso

**Opcion A, recomendada.** Un sistema real de su organizacion. Es la que mas
sirve, y la que produce mejores entregas.

**Opcion B.** Uno de los escenarios del taller de la sesion 3.3: expedientes
clinicos, catalogo de comercio electronico, telemetria de vehiculos, o nomina.

**Opcion C.** Extender el caso de pagos del curso con un requerimiento nuevo.
Ejemplos: conciliacion con el banco emisor, deteccion de patrones de fraude,
tablero de operacion para el area comercial.

Si elige la opcion A y el caso tiene informacion sensible, **use datos
sinteticos**. El curso entero corrio sobre datos generados.

---

## 4. Contenido del documento

### 4.1 El problema

Que hace el sistema, quien lo usa, que decisiones se toman con esos datos. Media
cuartilla.

### 4.2 El modelo

- Las entidades y sus relaciones.
- Que parte tiene estructura estable y que parte varia.
- Un diagrama. Puede ser a mano y fotografiado.

### 4.3 La matriz de decision

Use la plantilla de `c3_s3_b4_matriz.md`. Debe incluir:

- Las siete preguntas respondidas sobre **este** sistema, no en general.
- Una tabla por cada motor considerado, **incluidos los descartados**.
- El renglon de que se cede.
- El renglon de que haria cambiar la decision.

Los dos ultimos concentran la evaluacion.

### 4.4 La arquitectura propuesta

Que motor guarda que, y por que. Si propone mas de uno, explique como se
mantienen coherentes entre si.

Los cuatro motores del curso y su papel tipico:

| Motor | Papel |
|---|---|
| SQLite | Local, un usuario, prototipo, distribuir un conjunto |
| PostgreSQL | Registro de la operacion, integridad, consulta expresiva |
| MongoDB | Agregado completo, estructura que varia por entero |
| Redis | Latencia durante la operacion, datos reconstruibles |
| BigQuery | Analisis sobre el historico, agregacion sobre volumen |

No es obligatorio usar mas de uno. Una arquitectura de un solo motor, bien
sustentada, vale igual que una de cuatro.

### 4.5 Lo que se cede

Una seccion propia. Toda decision cede algo. Si no encuentra que, no examino el
problema.

### 4.6 Como se opera

- Como se cargan los datos.
- Como se respalda.
- Que se hace cuando un componente falla.
- Cuanto costaria de forma aproximada.

---

## 5. Contenido del codigo

Una porcion que funcione de verdad. **No el sistema completo.** Debe incluir:

1. **El modelo declarado.** DDL de PostgreSQL, o esquema de BigQuery, o
   validador de MongoDB, segun lo que haya elegido.

2. **Carga de datos**, aunque sean pocos y sinteticos. Con semilla fija, para que
   sea reproducible.

3. **Tres consultas** que respondan preguntas de negocio del caso, no consultas
   de ejemplo.

4. **Una decision tecnica evidenciada.** Un indice con su plan, una particion con
   su estimado de bytes, una cache con su medicion, una validacion rechazando un
   dato invalido. Cualquiera, con la evidencia de que funciona.

5. **Un archivo README** con las instrucciones para ejecutarlo.

Requisitos que aplican de todo el curso:

- Credenciales en variables de entorno, nunca en el codigo.
- Consultas con parametros, nunca concatenando.
- Comentarios que expliquen las decisiones, no lo que hace cada linea.
- Toda medicion con su metodo declarado.

---

## 6. Criterios de evaluacion

| Criterio | Peso | Que se evalua |
|---|---|---|
| Matriz de decision | 25% | Las siete preguntas, y los dos renglones finales |
| Eleccion de motores | 15% | El argumento, no cual eligio |
| Modelo | 15% | Coherente con el caso y con la eleccion |
| Codigo funcionando | 25% | Que corra, y que evidencie una decision tecnica |
| Operacion | 10% | Carga, respaldo, falla, costo |
| Claridad | 10% | Que se entienda sin explicacion oral |

### Lo que NO se evalua

- Haber elegido los motores que el instructor habria elegido.
- La cantidad de tecnologia. Una arquitectura sencilla bien sustentada vale mas
  que una complicada sin argumento.
- El volumen de codigo.

### Lo que reprueba

- Una matriz sin el renglon de que se cede.
- Elegir un motor citando un argumento que el curso mostro que no resiste, sin
  matizarlo.
- Codigo que no corre.
- Credenciales en el codigo.

---

## 7. Cuatro errores frecuentes

**Proponer cuatro motores porque el curso enseño cuatro.** Cada motor que se
agrega hay que operarlo, respaldarlo y mantener coherente. Si uno basta, uno
basta.

**Justificar con consignas.** "MongoDB es para datos no estructurados" y
"PostgreSQL no escala" son las dos que el curso desarmo de forma explicita.

**Declarar que no se cede nada.** Siempre se cede algo.

**Medir sin metodo.** Un tiempo sin decir cuantas repeticiones ni que estadistico
no es verificable.

---

## 8. Entrega

| | |
|---|---|
| Formato | Un PDF o Markdown, mas un archivo comprimido con el codigo |
| Fecha | La que indique el instructor |
| Medio | El que indique BSG Institute |

Nombre del archivo: `proyecto_final_APELLIDO_NOMBRE`.

---

## 9. Una nota sobre el proposito

El curso recorrio cinco motores en catorce sesiones. Ninguno se estudio a fondo:
cada uno tiene libros enteros dedicados.

Lo que si se cubrio a fondo fue el criterio para elegir entre ellos, y eso es lo
que este proyecto evalua.

En tres anos, las versiones habran cambiado y habra motores que hoy no existen.
El criterio va a seguir sirviendo.
