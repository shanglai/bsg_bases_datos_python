# c2_s1_b1_preparacion.md
## Preparacion del entorno de la sesion 2.1

**Bases de Datos y SQL con Python | BSG Institute | Capitulo 2, Sesion 2.1**

Esta guia se completa **antes** de la sesion. Tiempo estimado: 40 minutos.
Es la unica sesion del curso con instalacion significativa, y el entorno que
queda se usa hasta la sesion 4.4.

---

### 1. Que cambia respecto del capitulo 1

El capitulo 1 trabajo con SQLite, un motor embebido: la base era un archivo y no
habia servidor. A partir de esta sesion el motor es PostgreSQL, que opera como
servidor y admite varios clientes conectados al mismo tiempo.

Eso introduce tres elementos nuevos:

| Elemento | Para que sirve |
|---|---|
| Contenedor | Ejecuta el servidor sin instalarlo en el sistema operativo |
| DBeaver | Cliente grafico para explorar la base y escribir consultas |
| Archivo `.env` | Guarda las credenciales fuera del codigo fuente |

---

### 2. Requisitos

| Componente | Version | Verificacion |
|---|---|---|
| Motor de contenedores | vigente | `docker --version` |
| Python | 3.11 o superior | `python --version` |
| DBeaver Community | vigente | Se abre la aplicacion |

---

### 3. Paso a paso

#### 3.1 Verificar el motor de contenedores

```bash
docker --version
docker compose version
docker run --rm hello-world
```

El tercer comando descarga una imagen minima y la ejecuta. Si responde con el
mensaje de bienvenida, el entorno esta listo.

Si `docker compose version` no responde pero `docker-compose --version` si, se
trata de una version anterior. En ese caso, sustituir `docker compose` por
`docker-compose` en todos los comandos de esta guia.

#### 3.2 Preparar el directorio de trabajo

En el mismo directorio del curso, con el entorno virtual activo:

```bash
pip install "psycopg[binary]" python-dotenv
```

`psycopg` es el controlador de PostgreSQL para Python. La variante `binary`
incluye las bibliotecas compiladas y evita necesitar un compilador local.

#### 3.3 Crear el archivo de credenciales

Copiar `c2_s1_b2_env_ejemplo.txt` con el nombre `.env` y sustituir el valor de
`POSTGRES_PASSWORD`.

```bash
# Windows (PowerShell)
Copy-Item c2_s1_b2_env_ejemplo.txt .env

# macOS o Linux
cp c2_s1_b2_env_ejemplo.txt .env
```

El punto inicial hace que el archivo quede oculto en algunos sistemas. Es
intencional.

#### 3.4 Levantar el servidor

```bash
docker compose -f c2_s1_b2_docker_compose.yml up -d
```

Verificar el estado:

```bash
docker compose -f c2_s1_b2_docker_compose.yml ps
```

La columna de estado debe indicar que el servicio esta activo y en condicion
saludable. La primera vez tarda un poco mas, porque descarga la imagen.

#### 3.5 Instalar y configurar DBeaver

Descargar DBeaver Community desde `https://dbeaver.io/download/`.

Crear la conexion:

1. Nueva conexion, seleccionar PostgreSQL
2. Servidor: `localhost`
3. Puerto: `5432`
4. Base de datos: `pagos`
5. Usuario y contrasena: los valores del archivo `.env`
6. Probar la conexion. DBeaver ofrece descargar el controlador la primera vez;
   aceptar
7. Finalizar

Si la prueba responde de forma correcta, el entorno esta listo.

#### 3.6 Verificar desde Python

```bash
python -c "import psycopg, os; from dotenv import load_dotenv; load_dotenv(); print(psycopg.connect(f\"host={os.getenv('PGHOST','localhost')} port={os.getenv('PGPORT','5432')} dbname={os.getenv('POSTGRES_DB')} user={os.getenv('POSTGRES_USER')} password={os.getenv('POSTGRES_PASSWORD')}\").execute('SELECT version()').fetchone()[0])"
```

Debe imprimir la version del servidor.

---

### 4. Datos de partida

Se requiere `pagos_plano.csv`, generado en la sesion 1.1. Si no se conserva:

```bash
python c1_s1_b2_generar_datos.py
```

La semilla es `987654` y no debe modificarse.

---

### 5. Lista de verificacion

- [ ] `docker run --rm hello-world` responde de forma correcta
- [ ] `psycopg` y `python-dotenv` quedaron instalados en el entorno virtual
- [ ] Existe el archivo `.env` con la contrasena modificada
- [ ] El contenedor aparece activo y saludable
- [ ] DBeaver se conecta a la base `pagos`
- [ ] La verificacion desde Python imprime la version del servidor
- [ ] `pagos_plano.csv` existe y contiene 5000 filas

---

### 6. Problemas frecuentes

| Sintoma | Causa probable | Accion |
|---|---|---|
| El puerto 5432 esta ocupado | Ya existe un PostgreSQL en el equipo | Cambiar `PGPORT` a `5433` en `.env` y ajustar el puerto en DBeaver |
| El contenedor arranca y se detiene | Falta el archivo `.env` o una variable | Revisar con `docker compose logs` |
| DBeaver rechaza la contrasena | Se modifico `.env` despues del primer arranque | `docker compose down -v` y volver a levantar |
| `ModuleNotFoundError: psycopg` | El entorno virtual no esta activo | Activarlo y reinstalar |
| La conexion desde Python falla y desde DBeaver funciona | `PGHOST` o `PGPORT` mal definidos en `.env` | Corregir y volver a ejecutar |

La cuarta fila de la tabla merece atencion: el volumen conserva las credenciales
con las que se inicializo la base. Cambiar la contrasena en `.env` despues del
primer arranque no la modifica dentro del contenedor. `down -v` elimina el
volumen y permite volver a empezar.

---

### 7. Comandos de operacion cotidiana

```bash
# Levantar
docker compose -f c2_s1_b2_docker_compose.yml up -d

# Detener sin perder datos
docker compose -f c2_s1_b2_docker_compose.yml stop

# Ver la bitacora
docker compose -f c2_s1_b2_docker_compose.yml logs -f

# Eliminar todo, incluidos los datos
docker compose -f c2_s1_b2_docker_compose.yml down -v
```

El entorno queda activo para el resto del curso. No es necesario repetir esta
guia en las sesiones siguientes.
