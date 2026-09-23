# c3_s3_b1_preparacion.md
## Preparacion de la sesion 3.3

**Bases de Datos y SQL con Python | BSG Institute | Capitulo 3, Sesion 3.3**

Esta sesion usa **los dos motores a la vez**. Es la unica del curso que lo exige.
Tiempo estimado: 10 minutos.

---

### 1. Punto de partida

| Elemento | Verificacion |
|---|---|
| Contenedor de PostgreSQL | `docker compose -f c2_s1_b2_docker_compose.yml ps` |
| Contenedor de MongoDB | `docker compose -f c3_s1_b2_docker_compose.yml ps` |
| Base `pagos` con `autorizacion` | 5000 transacciones |
| Coleccion `operaciones` | 5000 documentos |
| Coleccion `catalogo_categorias` | Creada en la sesion 3.2 |

**Ambos contenedores deben estar activos.** Si alguno quedo detenido tras la
sesion anterior, levantarlo ahora.

Verificacion conjunta:

```bash
python -c "import os,psycopg; from dotenv import load_dotenv; from pymongo import MongoClient; from urllib.parse import quote_plus; load_dotenv(override=True); print('postgres:', psycopg.connect(f\"host={os.getenv('PGHOST')} port={os.getenv('PGPORT')} dbname={os.getenv('POSTGRES_DB')} user={os.getenv('POSTGRES_USER')} password={os.getenv('POSTGRES_PASSWORD')}\").execute('SELECT COUNT(*) FROM pagos.transacciones').fetchone()[0]); print('mongo:', MongoClient(f\"mongodb://{quote_plus(os.getenv('MONGO_USER'))}:{quote_plus(os.getenv('MONGO_PASSWORD'))}@{os.getenv('MONGO_HOST')}:{os.getenv('MONGO_PORT')}/?authSource=admin\")[os.getenv('MONGO_DB')].operaciones.count_documents({}))"
```

Debe imprimir `postgres: 5000` y `mongo: 5000`.

---

### 2. Lo que hay que traer

Esta sesion no introduce tecnologia nueva. Lo que se necesita es el material
acumulado del curso.

- La ficha de seis puntos de **SQLite**, de las sesiones 1.1 y 1.2
- La de **PostgreSQL**, cerrada en la sesion 2.5
- La de **MongoDB**, con los puntos 2 y 3 completados en la 3.2

Si alguna quedo incompleta, conviene cerrarla antes. El taller las usa de
entrada.

---

### 3. Advertencia sobre el formato de la sesion

Esta sesion se califica distinto de las anteriores.

En los talleres previos habia respuestas correctas. En este, las partes de
escenarios y de matriz admiten varias respuestas defendibles, y lo que se evalua
es el argumento.

Dos participantes pueden elegir motores distintos y ambos obtener calificacion
completa, si cada uno sustenta su eleccion y declara lo que cede.

---

### 4. Lista de verificacion

- [ ] Ambos contenedores activos
- [ ] `postgres: 5000` y `mongo: 5000`
- [ ] Las tres fichas de seis puntos completas
- [ ] La coleccion `catalogo_categorias` existe

---

### 5. Continuidad

El capitulo 3 llevo el mismo caso por un camino distinto al del capitulo 2. Esta
sesion pone ambos lado a lado y construye la matriz de decision.

Es el ensayo directo del proyecto final, donde se evalua exactamente esta
competencia.
