# c3_s2_b7_guia_uso.md
## Guia de uso de los materiales de la sesion 3.2

**Bases de Datos y SQL con Python | BSG Institute | Capitulo 3, Sesion 3.2**

Documento para el instructor.

---

## 1. Inventario de archivos

| Archivo | Tipo | Destinatario | Momento de uso |
|---|---|---|---|
| `c3_s2_b0_diagramas.py` | Script | Instructor | Preparacion previa |
| `c3_s2_d1_tuberia.puml` | Fuente | Instructor | Preparacion previa |
| `c3_s2_d2_unwind.puml` | Fuente | Instructor | Preparacion previa |
| `c3_s2_b1_preparacion.md` | Guia | Participante | Dos dias antes |
| `c3_s2_b1_verifica.py` | Script | Participante | Dos dias antes |
| `c3_s2_b2_agregacion.py` | Script | Ambos | Minuto 5 |
| `c3_s2_b3_indices.py` | Script | Ambos | Minuto 35 |
| `c3_s2_b4_pandas.py` | Script | Ambos | Minuto 100 |
| `c3_s2_b5_taller.md` | Taller | Participante | Minuto 50 |
| `c3_s2_b6_presentacion.html` | Presentacion | Instructor | Toda la sesion |
| `c3_s2_b8_solucionario.py` | Solucionario | **Solo instructor** | Preparacion y revision |
| `c3_s2_d1` a `d3` (PNG) | Figuras | Instructor | Diapositivas 4, 8 y 16 |

---

## 2. Riesgo operativo

Bajo en instalacion, medio en capacidades del servidor.

Esta sesion usa mas superficie de MongoDB que la 3.1: `$lookup`, `$facet`,
`$project` con expresiones, indices parciales y validacion de esquema. Con la
imagen oficial `mongo:7` todo esta disponible.

Por eso se incluye `c3_s2_b1_verifica.py`, que prueba cada capacidad y reporta
cuales faltan. **Conviene correrlo en el equipo del aula antes de la clase.**

---

## 3. Preparacion previa del instructor

### 3.1 Ensayo del camino completo

```bash
docker compose -f c3_s1_b2_docker_compose.yml up -d
python c3_s2_b1_verifica.py
python c3_s2_b2_agregacion.py
python c3_s2_b3_indices.py
python c3_s2_b4_pandas.py
python c3_s2_b8_solucionario.py
```

### 3.2 Estado del entorno al iniciar

Contenedores activos, coleccion cargada, y la coleccion **sin indices propios**
salvo el de `_id`. El bloque 2 de `c3_s2_b3_indices.py` los elimina por su cuenta,
de modo que el orden de ejecucion no importa.

---

## 4. Envio previo al participante

Se envian `c3_s2_b1_preparacion.md` y `c3_s2_b1_verifica.py`, con dos dias de
anticipacion.

---

## 5. Secuencia de la sesion

| Min. | Bloque | Material | Modalidad |
|---|---|---|---|
| 0 a 5 | Recuperacion y verificacion | `b6` diapositiva 2 | Discusion |
| 5 a 25 | La canalizacion y los acumuladores | `b6` 4 a 7, bloques 1 a 3 de `b2` | Demostracion |
| 25 a 40 | Arreglos y combinaciones | `b6` 8 a 10, bloques 4 y 5 de `b2` | Demostracion |
| 40 a 50 | Indices y plan | `b6` 11 y 12, bloques 1 a 4 de `b3` | Demostracion |
| 50 a 100 | Taller | `b5` | Practica |
| 100 a 113 | Validacion y pandas | `b6` 13 a 18, bloque 5 de `b3` y `b4` | Demostracion |
| 113 a 120 | Cierre | `b6` 19 a 21 | Discusion |

### 5.1 El momento de mayor valor didactico

La diapositiva 9, sobre agrupar un arreglo sin expandirlo.

Conviene plantearlo como prediccion: proyectar la consulta sin `$unwind` y pedir
que anticipen el resultado. Casi siempre responden que cuenta cada senal.

Lo que devuelve es un conteo por **combinacion** de senales. Un resultado que
parece razonable y responde otra pregunta.

Inmediatamente despues, los tres numeros del `$unwind`: 5000 originales, 4741 tras
la expansion, 7042 conservando los vacios. La segunda cifra es menor que la
primera, y eso sorprende hasta que se explica que los documentos sin arreglo
desaparecen.

Conectar con la sesion 2.2: es el equivalente de convertir un `LEFT JOIN` en
`INNER JOIN` sin darse cuenta.

### 5.2 Un detalle tecnico que conviene no omitir

`cursor.explain()` de PyMongo **no** devuelve `executionStats`. Sin ese bloque no
hay documentos examinados ni tiempo real, que son justo las cifras que sirven
para decidir.

La forma correcta es el comando explicito:

```python
base.command("explain", {"find": "operaciones", "filter": filtro},
             verbosity="executionStats")
```

Es un tropiezo silencioso: `explain()` devuelve algo, y ese algo no trae lo que
hace falta.

### 5.3 La conexion que cierra el curso

La diapositiva 18 recorre el tipo del monto a lo largo de cuatro sesiones. Es la
tercera vez que aparece el tema, y ahora se puede formular como principio: la
decision del tipo se toma una sola vez, en el almacenamiento, y todo lo que viene
despues la hereda.

Con un grupo de banca, este recorrido suele ser el momento que mas se recuerda
del capitulo.

---

## 6. Administracion del taller

| Parte | Tiempo | Contenido |
|---|---|---|
| A | 13 min | Canalizacion |
| B | 12 min | Arreglos y combinaciones |
| C | 13 min | Indices |
| D | 7 min | Validacion y pandas |
| E | 5 min | Analisis |
| F | Opcional | Extension |

Si el grupo se atrasa, la parte D se reduce a D1 y D2; el resto se cubre en la
demostracion posterior.

### 6.1 Puntos de atencion durante la revision

- **A2**: una sola tuberia, con `$cond` dentro del `$group`.
- **A5**: el enunciado admite dos lecturas. Se acepta cualquiera si el
  razonamiento reconoce que despues de `$group` el documento cambio de forma.
- **B2** es el punto de mayor valor del taller.
- **C2 y C3**: exigir que reporten examinados frente a devueltos, no solo la
  etapa ganadora.
- **E2**: se valora que proponga medir antes de rechazar.
- Error transversal: colocar `$match` despues de `$group` o de `$unwind`.

---

## 7. Dependencias entre archivos

```
coleccion operaciones (sesion 3.1)
        |
        +--> c3_s2_b1_verifica.py       (coleccion temporal, se elimina)
        +--> c3_s2_b2_agregacion.py     (crea catalogo_categorias)
        +--> c3_s2_b3_indices.py        (crea y elimina indices)
        +--> c3_s2_b4_pandas.py         (solo lectura)
        +--> c3_s2_b8_solucionario.py
```

`c3_s2_b2_agregacion.py` deja la coleccion `catalogo_categorias`, que la sesion
3.3 reutiliza. No conviene eliminarla.

---

## 8. Continuidad hacia la sesion 3.3

Se conservan:

- La coleccion `operaciones` y el catalogo de categorias
- La ficha de seis puntos de MongoDB, ya con los puntos 2 y 3 completos
- Ambos contenedores activos, que la 3.3 necesita para comparar

La sesion 3.3 ejecuta la misma pregunta de negocio en los dos motores y construye
la matriz de decision que se evalua en el proyecto final.
