# c2_s2_b1_preparacion.md
## Preparacion de la sesion 2.2

**Bases de Datos y SQL con Python | BSG Institute | Capitulo 2, Sesion 2.2**

Esta sesion continua sobre el entorno de la sesion 2.1. No hay instalacion de
motores ni contenedores nuevos. Tiempo estimado: 10 minutos.

---

### 1. Punto de partida

| Elemento | Origen | Verificacion |
|---|---|---|
| Contenedor de PostgreSQL | Sesion 2.1 | `docker compose -f c2_s1_b2_docker_compose.yml ps` |
| Base `pagos` cargada | Sesion 2.1 | Consulta de conteo, abajo |
| Archivo `.env` | Sesion 2.1 | Presente en el directorio |
| DBeaver conectado | Sesion 2.1 | Se abre la conexion |

---

### 2. Bibliotecas nuevas

```bash
pip install pandas polars sqlalchemy
```

Opcional, para la lectura en paralelo de Polars:

```bash
pip install connectorx
```

`connectorx` no es obligatorio. El material funciona sin el, con un camino
alternativo que se explica en la sesion.

---

### 3. Verificacion del punto de partida

Levantar el contenedor si no esta activo:

```bash
docker compose -f c2_s1_b2_docker_compose.yml up -d
```

Comprobar que la base conserva los datos:

```bash
python -c "import psycopg, os; from dotenv import load_dotenv; load_dotenv(); print(psycopg.connect(f\"host={os.getenv('PGHOST','localhost')} port={os.getenv('PGPORT','5432')} dbname={os.getenv('POSTGRES_DB')} user={os.getenv('POSTGRES_USER')} password={os.getenv('POSTGRES_PASSWORD')}\").execute('SELECT COUNT(*) FROM pagos.transacciones').fetchone()[0])"
```

Debe imprimir `5000`.

Si imprime cero o falla, volver a cargar:

```bash
python c2_s1_b4_carga.py
```

---

### 4. Una nota sobre la URI de SQLAlchemy

Este punto genera confusion y conviene adelantarlo.

SQLAlchemy necesita saber que controlador usar. Si la URI dice solo
`postgresql://`, la version 2.0 busca `psycopg2`, que es el controlador de la
generacion anterior y no se instalo en este curso. El error resultante menciona
un modulo que el codigo nunca nombro.

La forma correcta declara el controlador de forma explicita:

```
postgresql+psycopg://usuario:clave@localhost:5432/pagos
```

El material de la sesion usa siempre esa forma.

---

### 5. Lista de verificacion

- [ ] El contenedor esta activo
- [ ] La consulta de conteo devuelve 5000
- [ ] `pandas`, `polars` y `sqlalchemy` quedaron instalados
- [ ] DBeaver se conecta a la base `pagos`
- [ ] Se conserva la ficha de seis puntos de PostgreSQL de la sesion 2.1

---

### 6. Continuidad con la sesion anterior

La sesion 2.1 dejo los datos en seis tablas separadas, con la integridad
garantizada por el motor. Esa separacion tiene una consecuencia: ninguna
pregunta de negocio se responde ya con una sola tabla.

La sesion 2.2 resuelve como recomponer la informacion.
