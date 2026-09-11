# c2_s5_b1_preparacion.md
## Preparacion de la sesion 2.5

**Bases de Datos y SQL con Python | BSG Institute | Capitulo 2, Sesion 2.5**

Continua sobre el entorno de la sesion 2.1. No hay instalacion nueva, pero si un
requisito de espacio que conviene verificar antes.

Tiempo estimado: 10 minutos.

---

### 1. Punto de partida

| Elemento | Verificacion |
|---|---|
| Contenedor de PostgreSQL | `docker compose -f c2_s1_b2_docker_compose.yml ps` |
| Base `pagos` cargada | Consulta de conteo |
| DBeaver conectado | Se abre la conexion |
| Espacio libre en disco | Al menos 1 GB |

---

### 2. Requisito de espacio

Esta sesion genera una tabla de dos millones de filas para poder medir el efecto
de un indice. Ocupa alrededor de **170 MB**, y los indices que se crean durante
la sesion suman otro tanto.

Contando el espacio de trabajo del motor, conviene tener **1 GB libre**.

Verificar el espacio del volumen de Docker:

```bash
docker system df
```

Si el espacio es limitado, la tabla se puede generar mas pequena. El material
funciona igual con quinientas mil filas:

```bash
python c2_s5_b2_volumen.py 500000
```

Con menos de doscientas mil filas, el motor tiende a elegir el recorrido
secuencial en todos los casos y el ejercicio pierde sentido.

---

### 3. Generar la tabla de volumen

```bash
python c2_s5_b2_volumen.py
```

La tabla se construye **dentro del motor** con `generate_series`, sin transferir
datos desde Python. Dos millones de filas tardan menos de diez segundos.

La salida debe reportar:

- 2,000,000 filas
- alrededor de 165 MB
- la distribucion por comercio, con Super Norteno cerca del 30 por ciento
- cero indices sobre la tabla

**El instructor indica si esto se ejecuta antes o durante la sesion.**

---

### 4. Verificacion

```sql
SELECT COUNT(*) FROM pagos.transacciones_volumen;
```

Debe devolver `2000000`.

```sql
SELECT indexname FROM pg_indexes
WHERE schemaname = 'pagos' AND tablename = 'transacciones_volumen';
```

Debe devolver cero filas. La tabla se entrega sin indices a proposito: crearlos y
medir su efecto es el ejercicio de la sesion.

---

### 5. Repaso previo

Esta sesion se apoya en un punto de la sesion 2.4 que conviene tener fresco.

Ahi se observo que un indice GIN existente **no se usaba** cuando el predicado
era poco selectivo, o cuando la condicion aplicaba una funcion sobre la columna.

Hoy se estudia ese fenomeno de forma sistematica, sobre indices ordinarios y con
volumen suficiente para que los tiempos sean visibles.

---

### 6. Lista de verificacion

- [ ] El contenedor esta activo
- [ ] Hay al menos 1 GB libre
- [ ] `pagos.transacciones_volumen` existe con 2,000,000 de filas
- [ ] La tabla no tiene indices
- [ ] DBeaver se conecta a la base `pagos`
- [ ] Se conserva la ficha de seis puntos de PostgreSQL

---

### 7. Limpieza posterior

Al terminar el capitulo 2, la tabla de volumen se puede eliminar:

```sql
DROP TABLE IF EXISTS pagos.transacciones_volumen;
```

El capitulo 3 no la necesita. El resto de la base si se conserva.
