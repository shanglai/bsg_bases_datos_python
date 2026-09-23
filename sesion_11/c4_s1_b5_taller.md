# c4_s1_b5_taller.md
## Taller de la sesion 4.1

**Bases de Datos y SQL con Python | BSG Institute**

Duracion estimada: 50 minutos dentro de la sesion.
Entrega: un archivo `.py` con el codigo y las respuestas escritas de la parte E.

Este taller aporta al componente de **trabajo en clase**, que representa el 25 por
ciento de la calificacion.

---

### Requisitos previos

Contenedor de Redis activo, PostgreSQL con el caso cargado, y `redis` instalado.

---

## Parte A. Estructuras

Todas las claves deben llevar el prefijo `taller:` para poder limpiarlas al
final.

**A1.** Guardar un contador de intentos para la tarjeta 42 e incrementarlo cinco
veces. Leer el valor.

**A2.** Guardar el perfil de la tarjeta 42 como diccionario, con al menos cuatro
campos. Leer un solo campo sin traer los demas.

**A3.** Construir un conjunto con las tarjetas bloqueadas y comprobar la
pertenencia de dos valores, uno presente y uno ausente.

**A4.** Construir un conjunto ordenado con el importe de los siete comercios.
Obtener los tres primeros y la posicion de Electro Maya.

**A5.** Explicar por que A3 usa conjunto y A4 conjunto ordenado, y que se perderia
al intercambiarlos.

**A6.** Ejecutar `TYPE` sobre las cuatro claves creadas y reportar el tipo de cada
una.

---

## Parte B. Expiracion y atomicidad

**B1.** Guardar una clave con expiracion de tres segundos. Verificar su TTL,
esperar y comprobar que desaparecio.

**B2.** Escribir una funcion `intentos_recientes(id_tarjeta, ventana)` que
incremente un contador y le fije expiracion solo la primera vez. Debe servir para
limitar intentos por minuto.

> Sugerencia: `INCR` sobre una clave inexistente la crea en 1. Fijar la
> expiracion solo cuando el valor devuelto sea 1.

**B3.** Explicar por que la funcion de B2 es correcta aun si dos procesos la
llaman al mismo tiempo.

**B4.** Implementar un cerrojo elemental con `SET` y `nx=True`. Demostrar que un
segundo intento falla mientras el primero lo tiene.

**B5.** Señalar dos cosas que le faltan a ese cerrojo para ser correcto en
produccion.

---

## Parte C. La cache

**C1.** Escribir una funcion `perfil(id_tarjeta)` con el patron cache-aside:
buscar en Redis, y si no esta, calcular contra PostgreSQL, guardar y devolver.
Debe indicar si el dato vino de cache o se calculo.

**C2.** Medir el tiempo de cien llamadas con la cache vacia y cien con la cache
llena. Reportar conforme al criterio de la sesion 2.5.

**C3.** Insertar una transaccion nueva para una tarjeta que ya este en cache.
Demostrar que la cache devuelve un dato que ya no es cierto.

**C4.** Corregirlo con invalidacion explicita y verificar.

**C5.** Comparar el tiempo de leer el perfil desde Redis contra calcularlo en
PostgreSQL. Reportar el metodo de medicion.

**C6.** A la vista del resultado de C5, responder: con este volumen de datos,
¿esta justificada la cache? Sustentar la respuesta.

---

## Parte D. Aplicado al caso

**D1.** Implementar un limitador que rechace mas de cinco intentos por tarjeta en
un minuto. Demostrarlo con seis llamadas seguidas.

**D2.** Mantener un conjunto ordenado con el importe acumulado por comercio del
dia, actualizado con `ZINCRBY` en cada operacion. Simularlo con cien operaciones.

**D3.** Mantener un conjunto de tarjetas bloqueadas y una funcion que consulte la
pertenencia antes de autorizar.

**D4.** Escribir una funcion que, dada una transaccion, aplique las tres
verificaciones anteriores y devuelva si se autoriza o no, con el motivo.

**D5.** Estimar cuantas veces por segundo se ejecutaria esa funcion en un sistema
real, y que ocurriria si cada verificacion fuera a PostgreSQL.

---

## Parte E. Analisis y argumentacion

**E1.** Enumerar tres datos del caso que SI convendria guardar en Redis y tres
que NO. Sustentar cada uno con el criterio de reconstruibilidad.

**E2.** La invalidacion de cache tiene tres estrategias. Elegir una para el perfil
de riesgo y otra para el bloqueo de una tarjeta, y explicar por que son distintas.

**E3.** Redis puede persistir en disco. Explicar por que eso no lo convierte en
sustituto de PostgreSQL para el registro de la transaccion.

**E4.** Un compañero propone mover toda la tabla de comercios a Redis, porque son
solo siete filas y se consultan siempre. Evaluar la propuesta.

**E5.** Completar la ficha de seis puntos de Redis.

---

## Parte F. Ejercicio de extension (opcional)

**F1.** Investigar las canalizaciones de comandos. Comparar el tiempo de mil
`SET` individuales contra mil dentro de una canalizacion.

**F2.** Investigar las politicas de desalojo de Redis. Explicar cual corresponde a
una cache y cual a un almacen.

**F3.** Investigar los flujos de Redis. Explicar en que se diferencian de una
lista usada como cola.

---

## Criterios de evaluacion

| Criterio | Peso |
|---|---|
| Elegir la estructura correcta y justificarla (parte A) | 20% |
| Expiracion y atomicidad, en especial B3 (parte B) | 20% |
| Cache-aside e invalidacion (parte C) | 25% |
| Aplicacion al caso (parte D) | 15% |
| Calidad del argumento en la parte E, en especial E1 y E4 | 20% |

Una solucion de C6 que concluya que la cache esta justificada sin sustentarlo con
la medicion obtiene calificacion parcial, aunque la conclusion pueda defenderse
por otras razones.

---

## Cierre

Redis resolvio la latencia, y para hacerlo renuncio a casi todo lo demas: no hay
consulta, no hay esquema, no hay combinaciones, y el dato se puede perder.

Queda una pregunta que ninguno de los cuatro motores vistos responde bien: como
se analiza el comportamiento de dos anos de operaciones, con agregaciones sobre
cientos de millones de registros, sin que cada consulta tarde horas.

Es lo que abre la sesion 4.3.
