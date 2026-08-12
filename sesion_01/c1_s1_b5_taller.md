# c1_s1_b5_taller.md
## Taller de la sesion 1.1

**Bases de Datos y SQL con Python | BSG Institute**

Duracion estimada: 50 minutos dentro de la sesion.
Entrega: un archivo `.py` o `.sql` con las respuestas, mas las respuestas escritas
de la parte C.

Este taller aporta al componente de **trabajo en clase**, que representa el 25 por
ciento de la calificacion. Se evalua tanto el resultado obtenido como la
justificacion tecnica.

---

### Requisitos previos

Haber ejecutado `c1_s1_b2_generar_datos.py` y contar con el archivo `pagos.db`.

---

## Parte A. Consulta sobre la tabla de movimientos

Resolver con SQL. Cada respuesta debe entregarse con la consulta utilizada.

**A1.** Cuantas operaciones se registraron en Guadalajara.

**A2.** Cual es el importe total aprobado en la ciudad de Merida.

**A3.** Listar las diez operaciones de mayor monto que ademas tengan contracargo.
Mostrar identificador, comercio, monto y fecha.

**A4.** Obtener el ticket promedio por metodo de captura, ordenado de mayor a
menor. Considerar unicamente operaciones aprobadas.

**A5.** Determinar en que mes se concentro el mayor importe aprobado.

> Sugerencia para A5: en SQLite, la funcion `strftime('%Y-%m', fecha_hora)`
> extrae el ano y el mes de una columna de texto con formato de fecha.

---

## Parte B. Acceso desde Python

Resolver con el modulo `sqlite3`. Entregar el codigo.

**B1.** Escribir una funcion `operaciones_por_ciudad(ciudad)` que reciba el nombre
de una ciudad y devuelva la cantidad de operaciones aprobadas. La ciudad debe
pasarse como **parametro** de la consulta, no concatenarse en la cadena.

**B2.** Escribir una funcion `resumen_por_marca()` que devuelva una lista de
diccionarios con la marca de tarjeta, la cantidad de operaciones y el importe
total. Utilizar `sqlite3.Row` para acceder a las columnas por nombre.

**B3.** Escribir una funcion `operaciones_en_rango(monto_minimo, monto_maximo)`
que reciba dos limites y devuelva las operaciones dentro del rango, ordenadas de
mayor a menor monto. Ambos limites se pasan como parametros.

**B4.** Modificar B1 de modo que, si la ciudad recibida no existe en la base, la
funcion devuelva cero en lugar de provocar un error.

---

## Parte C. Analisis y argumentacion

Responder por escrito, con dos o tres parrafos por pregunta.

**C1.** Ejecutar la siguiente consulta y explicar por que el resultado es
enganoso:

```sql
SELECT comercio, COUNT(*) AS operaciones
FROM movimientos
GROUP BY comercio
ORDER BY operaciones DESC;
```

Indicar cuantos comercios existen en realidad y como se determino.

**C2.** El correo electronico de un cliente aparece repetido en todas sus filas.
Describir que tendria que ocurrir para corregir el correo de un solo cliente, y
que riesgo introduce esa operacion.

**C3.** Aplicar los seis puntos de la ficha del curso a SQLite, con base en lo
observado en esta sesion:

1. Modelo de datos que asume
2. Operaciones en las que resulta eficiente
3. Garantias de consistencia que ofrece
4. Relacion entre el costo de escritura y el de lectura
5. Interfaz desde Python
6. Escenario en el que conviene su uso y escenario en el que no

Esta ficha inicia la matriz de decision que se completa a lo largo del curso.

---

## Parte D. Ejercicio de extension (opcional)

**D1.** Escribir una consulta que identifique posibles duplicados de comercio
comparando el nombre normalizado con `UPPER(TRIM(comercio))`. Explicar por que
esta solucion resuelve el caso actual pero no previene el problema de fondo.

**D2.** Estimar, sin ejecutar la operacion, cuantas filas habria que modificar si
un comercio cambiara de categoria.

---

## Criterios de evaluacion

| Criterio | Peso |
|---|---|
| Correccion de las consultas de la parte A | 30% |
| Uso de parametros en lugar de concatenacion en la parte B | 30% |
| Calidad del argumento tecnico en la parte C | 40% |

Una consulta que devuelve el resultado correcto pero construye la condicion por
concatenacion de cadenas obtiene calificacion parcial en la parte B.

---

## Cierre

La parte C deja planteada la pregunta que abre la sesion 1.2: que estructura
impide que un mismo comercio se registre bajo tres escrituras distintas. La
respuesta es el modelo relacional normalizado.
