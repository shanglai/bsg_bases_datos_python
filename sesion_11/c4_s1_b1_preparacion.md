# c4_s1_b1_preparacion.md
## Preparacion de la sesion 4.1

**Bases de Datos y SQL con Python | BSG Institute | Capitulo 4, Sesion 4.1**

Tercer motor del curso. Es la instalacion mas sencilla de las tres.
Tiempo estimado: 15 minutos.

---

### 1. Punto de partida

| Elemento | Verificacion |
|---|---|
| Contenedor de PostgreSQL | Activo, con el caso cargado |
| Contenedor de MongoDB | Activo, se usa en el proyecto final |
| Archivo `.env` | El de las sesiones 2.1 y 3.1 |

PostgreSQL es el origen de los datos que Redis va a guardar en cache, de modo que
debe estar activo.

---

### 2. Paso a paso

#### 2.1 Instalar el controlador

```bash
pip install redis
```

#### 2.2 Agregar las variables al archivo .env

Abrir el `.env` existente y **agregar al final** las lineas de
`c4_s1_b2_env_ejemplo.txt`, sustituyendo el valor de `REDIS_PASSWORD`.

Sigue siendo un solo archivo para los tres motores.

#### 2.3 Levantar Redis

```bash
docker compose -f c4_s1_b2_docker_compose.yml up -d
docker compose -f c4_s1_b2_docker_compose.yml ps
```

La imagen es pequena y arranca en segundos.

#### 2.4 Verificar desde Python

```bash
python -c "import os,redis; from dotenv import load_dotenv; load_dotenv(override=True); print(redis.Redis(host=os.getenv('REDIS_HOST','localhost'), port=int(os.getenv('REDIS_PORT',6379)), password=os.getenv('REDIS_PASSWORD') or None).info('server')['redis_version'])"
```

Debe imprimir la version del servidor.

#### 2.5 Consola (opcional)

```bash
docker exec -it curso_redis redis-cli -a LA_CLAVE
```

Comandos utiles para explorar:

```
PING
INFO server
DBSIZE
SCAN 0 MATCH demo:* COUNT 10
```

**Nunca usar `KEYS *` en un servidor con datos.** Recorre el espacio completo de
claves y bloquea el servidor mientras lo hace. Se usa `SCAN`, que avanza por
partes.

No hace falta cliente grafico. Si alguien quiere uno, RedisInsight es el oficial
y es gratuito.

---

### 3. Una diferencia con los motores anteriores

En PostgreSQL y en MongoDB, la contrasena queda grabada en el volumen la primera
vez y cambiarla despues no surte efecto sin `down -v`. Fue la trampa de las
sesiones 2.1 y 3.1.

**En Redis no ocurre.** La contrasena se declara en el comando de arranque cada
vez, de modo que cambiarla en el `.env` y volver a levantar el contenedor
funciona sin borrar nada.

---

### 4. Lista de verificacion

- [ ] PostgreSQL activo con el caso cargado
- [ ] `redis` instalado en el entorno virtual
- [ ] El `.env` tiene las tres variables de Redis
- [ ] El contenedor de Redis esta activo y saludable
- [ ] La verificacion desde Python imprime la version

---

### 5. Problemas frecuentes

| Sintoma | Causa probable | Accion |
|---|---|---|
| `AuthenticationError` | Falta `REDIS_PASSWORD` en el `.env` | Revisar el archivo |
| `ConnectionRefusedError` | El contenedor no esta activo | `docker compose ps` |
| El puerto 6379 esta ocupado | Ya hay un Redis en el equipo | Cambiar `REDIS_PORT` a 6380 |
| Los valores llegan como `b'...'` | Falta `decode_responses=True` | Agregarlo al crear el cliente |

La ultima fila no es un error sino un detalle del controlador, y aparece siempre
la primera vez.

---

### 6. Repaso previo

Esta sesion se apoya en dos ideas anteriores.

**De la sesion 2.5.** Una medicion sin metodo declarado no es verificable. Hoy se
vuelve a aplicar, y el resultado va a ser incomodo.

**De la sesion 3.3.** El escenario de telemetria del taller no encajaba en
ninguno de los tres motores. El capitulo 4 llena ese hueco desde dos lados
distintos.

---

### 7. Continuidad

Redis es el tercer motor local del curso. Los tres conviven hasta el final,
porque el proyecto final puede proponer una arquitectura que use mas de uno.
