# c3_s1_b1_preparacion.md
## Preparacion de la sesion 3.1

**Bases de Datos y SQL con Python | BSG Institute | Capitulo 3, Sesion 3.1**

Esta sesion agrega un motor nuevo. Tiempo estimado: 25 minutos.

---

### 1. Lo importante primero

**PostgreSQL no se apaga.** El capitulo 3 usa los dos motores a la vez:

- La carga de MongoDB **lee** los datos desde PostgreSQL.
- La sesion 3.3 ejecuta la misma consulta en ambos y los compara.

Ambos contenedores deben quedar activos hasta el final del curso.

---

### 2. Punto de partida

| Elemento | Verificacion |
|---|---|
| Contenedor de PostgreSQL | `docker compose -f c2_s1_b2_docker_compose.yml ps` |
| Base `pagos` cargada | 5000 transacciones |
| Columna `autorizacion` | Cargada en la sesion 2.4 |
| Archivo `.env` | El de la sesion 2.1 |

Comprobar el origen:

```sql
SELECT COUNT(*) FROM pagos.transacciones WHERE autorizacion IS NOT NULL;
```

Debe devolver `5000`. Si devuelve cero, ejecutar `c2_s4_b2_payload.py`.

---

### 3. Paso a paso

#### 3.1 Instalar el controlador

```bash
pip install pymongo
```

`pymongo` es el controlador oficial de MongoDB para Python. No requiere
compilacion ni dependencias del sistema.

#### 3.2 Agregar las variables al archivo .env

Abrir el archivo `.env` creado en la sesion 2.1 y **agregar al final** las lineas
de `c3_s1_b2_env_ejemplo.txt`, sustituyendo el valor de `MONGO_PASSWORD`.

No se crea un archivo nuevo. Los dos motores leen del mismo.

#### 3.3 Levantar MongoDB

```bash
docker compose -f c3_s1_b2_docker_compose.yml up -d
```

Verificar:

```bash
docker compose -f c3_s1_b2_docker_compose.yml ps
```

El estado debe ser activo y saludable. La primera vez tarda mas, porque descarga
la imagen.

#### 3.4 Verificar la conexion desde Python

```bash
python -c "import os; from dotenv import load_dotenv; from pymongo import MongoClient; load_dotenv(); c = MongoClient(f\"mongodb://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@{os.getenv('MONGO_HOST','localhost')}:{os.getenv('MONGO_PORT','27017')}/?authSource=admin\"); print(c.server_info()['version'])"
```

Debe imprimir la version del servidor.

#### 3.5 Cliente grafico

**DBeaver Community NO se conecta a MongoDB.** El controlador de MongoDB solo
esta disponible en las ediciones comerciales de DBeaver. Con la edicion gratuita
que se instalo en la sesion 2.1, MongoDB no aparece en la lista de conexiones.

DBeaver se sigue usando para PostgreSQL durante el resto del curso.

Para MongoDB se usa **MongoDB Compass**, que es gratuito y oficial:

`https://www.mongodb.com/products/tools/compass`

Cadena de conexion en Compass:

```
mongodb://curso:LA_CLAVE@localhost:27017/?authSource=admin
```

Compass permite explorar documentos anidados, escribir filtros y probar
canalizaciones de agregacion con vista previa etapa por etapa. Esa ultima
funcion es especialmente util en la sesion 3.2.

No es obligatorio: la sesion trabaja desde Python. Conviene instalarlo de todos
modos, porque ver el documento completo ayuda a entender el modelo.

---

### 4. El tropiezo mas frecuente

La imagen oficial crea el usuario en la base `admin`, no en la base de trabajo.
Por eso la cadena de conexion incluye `authSource=admin`:

```
mongodb://curso:clave@localhost:27017/?authSource=admin
```

Omitir ese parametro produce un error de autenticacion cuyo mensaje no dice cual
es la causa.

---

### 5. Lista de verificacion

- [ ] El contenedor de PostgreSQL sigue activo
- [ ] `SELECT COUNT(*) ... WHERE autorizacion IS NOT NULL` devuelve 5000
- [ ] `pymongo` esta instalado
- [ ] El archivo `.env` tiene las cinco variables de MongoDB
- [ ] El contenedor de MongoDB esta activo y saludable
- [ ] La verificacion desde Python imprime la version del servidor
- [ ] MongoDB Compass instalado y conectado (opcional pero recomendado)

---

### 6. Problemas frecuentes

| Sintoma | Causa probable | Accion |
|---|---|---|
| Error de autenticacion | Falta `authSource=admin` | Revisar la cadena de conexion |
| El puerto 27017 esta ocupado | Ya hay un MongoDB en el equipo | Cambiar `MONGO_PORT` a `27018` |
| El contenedor arranca y se detiene | Faltan variables en `.env` | Revisar con `docker compose logs` |
| La contrasena no funciona | Se cambio despues del primer arranque | `down -v` y volver a levantar |
| `ModuleNotFoundError: pymongo` | Entorno virtual no activo | Activarlo y reinstalar |

La cuarta fila es la misma trampa de la sesion 2.1: el volumen conserva las
credenciales con las que se inicializo.

---

### 7. Comandos de operacion

```bash
# Levantar
docker compose -f c3_s1_b2_docker_compose.yml up -d

# Consola de MongoDB
docker exec -it curso_mongo mongosh -u curso -p

# Detener sin perder datos
docker compose -f c3_s1_b2_docker_compose.yml stop

# Eliminar todo, incluidos los datos
docker compose -f c3_s1_b2_docker_compose.yml down -v
```

---

### 8. Repaso previo

Esta sesion se apoya en la 2.4. Conviene recordar dos cosas:

**El mensaje de autorizacion** es un documento anidado cuya estructura varia
segun el metodo de captura, y cerca de un seis por ciento no trae el bloque de
riesgo.

**JSONB dentro de PostgreSQL** ya permitia almacenarlo, indexarlo y consultarlo.
El capitulo 3 examina que aporta un motor construido enteramente alrededor de esa
idea.
