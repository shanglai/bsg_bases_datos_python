# c1_s2_b5_taller.md
## Taller de la sesion 1.2

**Bases de Datos y SQL con Python | BSG Institute**

Duracion estimada: 50 minutos dentro de la sesion.
Entrega: el diagrama del modelo, el archivo DDL propio, el script de carga y las
respuestas escritas de la parte D.

Este taller aporta al componente de **trabajo en clase**, que representa el 25 por
ciento de la calificacion.

---

### Requisitos previos

Contar con `pagos_plano.csv`, generado en la sesion 1.1. Si no se conserva, volver
a ejecutar `c1_s1_b2_generar_datos.py` con la semilla `987654`.

---

## Parte A. Modelo conceptual

Trabajo en papel o en herramienta de diagramacion. No se escribe codigo todavia.

**A1.** Listar las entidades que se distinguen en el archivo plano. Para cada una,
indicar que columnas del archivo le pertenecen.

**A2.** Determinar la cardinalidad de cada relacion. Responder de forma explicita:

- Un cliente, cuantas tarjetas puede tener
- Una tarjeta, a cuantos clientes puede pertenecer
- Una terminal, a cuantos comercios puede pertenecer
- Una transaccion, cuantos contracargos puede recibir

**A3.** Dibujar el modelo conceptual con entidades y relaciones. Sin atributos,
sin llaves y sin tipos de dato.

---

## Parte B. Modelo logico y llaves

**B1.** Para cada entidad, identificar la **llave natural**: la combinacion de
atributos que distingue de forma univoca un registro de otro.

**B2.** Justificar por que el nombre del cliente no sirve como llave natural.
Sustentar la respuesta con una consulta sobre el archivo plano.

**B3.** Determinar si el codigo de terminal es unico por si solo. Verificarlo con
una consulta antes de responder.

> Este punto tiene una respuesta contraintuitiva. Conviene comprobarla en los
> datos y no deducirla.

**B4.** Definir la llave primaria de cada tabla y decidir, para cada caso, si
conviene usar la llave natural o un identificador artificial.

---

## Parte C. Modelo fisico

**C1.** Escribir el archivo DDL completo con las seis tablas. Debe incluir:

- Llave primaria en cada tabla
- Llaves foraneas con su referencia
- Al menos tres restricciones `CHECK`
- Al menos dos restricciones `UNIQUE`
- Tipos de dato apropiados para cada columna

**C2.** Escribir el script de Python que lee `pagos_plano.csv` y carga las seis
tablas. La carga debe realizarse dentro de una sola transaccion.

**C3.** Comprobar que el conteo de transacciones en el modelo normalizado coincide
con el numero de filas del archivo de origen.

**C4.** Ejecutar `PRAGMA foreign_key_check` y confirmar que devuelve cero filas.

---

## Parte D. Analisis y argumentacion

Responder por escrito.

**D1.** Intentar insertar un comercio con un nombre que ya existe. Registrar el
mensaje de error del motor y explicar que restriccion lo produjo.

**D2.** En la sesion 1.1 se observo que la columna `comercio` contenia diecisiete
valores distintos para siete comercios reales. Explicar cual de los dos mecanismos
siguientes previene que el problema reaparezca, y por que el otro no:

- La funcion de limpieza aplicada durante la carga
- La restriccion `UNIQUE` declarada en la tabla

**D3.** El archivo plano registra el contracargo como una marca de si o no, sin
fecha. Explicar que informacion se perdio en el origen y que consecuencia tiene
para un analisis de tiempos de disputa.

**D4.** Completar la ficha de seis puntos del modelo relacional normalizado y
compararla con la ficha de SQLite elaborada en la sesion 1.1. Indicar que cambio
y que permanece igual.

---

## Parte E. Ejercicio de extension (opcional)

**E1.** El modelo actual guarda la categoria como un atributo del comercio. Evaluar
si conviene extraerla a una septima tabla. Argumentar a favor y en contra.

**E2.** Proponer que restriccion adicional impediria registrar un contracargo sobre
una transaccion rechazada. Escribir la sentencia correspondiente.

**E3.** Estimar el espacio que ocupa el archivo plano frente al de la base
normalizada. Explicar el resultado.

---

## Criterios de evaluacion

| Criterio | Peso |
|---|---|
| Correccion del modelo conceptual y las cardinalidades (parte A) | 20% |
| Identificacion de llaves naturales, en particular B3 (parte B) | 25% |
| DDL con restricciones efectivas y carga verificada (parte C) | 25% |
| Calidad del argumento en la parte D, en especial D2 | 30% |

Un modelo que carga los datos sin declarar llaves foraneas ni restricciones
obtiene calificacion parcial en la parte C: la carga funciona, pero el motor no
protege la integridad.

---

## Cierre

El modelo resuelve la integridad de los datos. Queda abierta la pregunta que da
paso al capitulo 2: el motor sigue operando sobre un archivo unico con un solo
escritor a la vez. Que ocurre cuando varias terminales registran operaciones de
forma simultanea.
