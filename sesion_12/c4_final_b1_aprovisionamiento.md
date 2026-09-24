# c4_final_b1_aprovisionamiento.md
## Aprovisionamiento de la sesion final

**Bases de Datos y SQL con Python | BSG Institute**

Documento para el instructor. **Los alumnos no instalan nada.**

Tiempo estimado: 45 minutos, mas la espera de la carga.
Hacerlo al menos **un dia antes** de la clase.

---

## 1. Resumen de lo que se aprovisiona

| Componente | Donde | Para que |
|---|---|---|
| Conjunto de datos `pagos` en BigQuery | Proyecto del instructor | Ejercicio 2 |
| Tabla `operaciones`, particionada y agrupada | Proyecto del instructor | Ejercicio 2 |
| VM `curso-redis` con un usuario por alumno | Proyecto del instructor | Ejercicio 1 |
| Roles IAM para los alumnos | Proyecto del instructor | Acceso de todos |

Los alumnos solo necesitan un navegador y su cuenta de Google.

---

## 2. Antes de empezar

```bash
gcloud auth login
gcloud config set project MI_PROYECTO
gcloud services enable bigquery.googleapis.com compute.googleapis.com
```

Para la parte de preparacion de datos con Gemini, ademas:

```bash
gcloud services enable cloudaicompanion.googleapis.com
```

---

## 3. BigQuery

### 3.1 Generar el archivo de carga

```bash
python c4_final_b3_exporta_bigquery.py
```

Produce `operaciones.ndjson` (unos 4.4 MB, 5000 registros) y `esquema.json`.

Requiere PostgreSQL con el caso cargado y la columna `autorizacion`, es decir el
entorno de las sesiones 2.1 y 2.4.

### 3.2 Crear el conjunto y cargar

```bash
bq mk --location=us-central1 --dataset MI_PROYECTO:pagos

bq load --source_format=NEWLINE_DELIMITED_JSON \
   --time_partitioning_field=fecha_hora \
   --time_partitioning_type=DAY \
   --clustering_fields=estatus,metodo_captura \
   MI_PROYECTO:pagos.operaciones operaciones.ndjson esquema.json
```

El particionamiento y el agrupamiento **son contenido de la sesion**. Sin ellos,
el ejercicio 4 y el 5 no demuestran nada.

### 3.3 Verificar

```bash
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) AS filas FROM `MI_PROYECTO.pagos.operaciones`'
```

Debe devolver 5000.

### 3.4 Validar el SQL de la sesion, sin costo

```bash
./c4_final_b6_valida_sql.sh MI_PROYECTO c4_final_b5_bigquery.sql
```

Usa `bq query --dry_run`, que comprueba sintaxis y reporta bytes **sin ejecutar
ni cobrar**. Reporta cada sentencia como valida o con error, y suma el total que
procesaria la sesion completa.

**Este paso no es opcional.** El SQL de BigQuery de esta sesion no se pudo probar
durante su elaboracion, y el validador es la forma de confirmarlo.

---

## 4. Redis

### 4.1 Por que una VM y no Memorystore

Memorystore vive dentro de una VPC. Los alumnos, conectandose desde Cloud Shell,
**no lo alcanzan** sin un conector serverless, un bastion o una VPN. Ademas el
nivel mas pequeno se cobra por hora encendido.

Una `e2-small` con Redis 7 cuesta centavos por el dia de la clase, se alcanza
desde Cloud Shell, y permite un usuario por alumno con ACL, que de por si es
contenido de la sesion.

### 4.2 Aprovisionar

```bash
./c4_final_b2_provisiona_redis.sh MI_PROYECTO 20 "RANGO_DEL_AULA/24"
```

El tercer argumento es el rango de IP publica desde donde se conectaran. El
script **rechaza** `0.0.0.0/0`: un Redis abierto a internet se compromete en
minutos.

Para averiguar el rango del aula, desde ahi:

```bash
curl -s ifconfig.me
```

Si los alumnos trabajan desde Cloud Shell, el rango de salida de Cloud Shell no
es fijo. Dos opciones:

- Permitir el rango de la red del aula y pedir que trabajen desde su equipo.
- Permitir un rango amplio **solo durante la clase** y borrar la regla al
  terminar.

La segunda es aceptable para dos horas, con contrasenas generadas al azar y sin
datos reales. Conviene decidirlo de forma consciente.

### 4.3 Que produce

| Archivo | Contenido |
|---|---|
| `acl_alumnos.conf` | Las ACL, que el script aplica al servidor |
| `credenciales_alumnos.csv` | Una fila por alumno, para repartir |

**`credenciales_alumnos.csv` contiene contrasenas en claro.** Se reparte una fila
a cada persona y despues se borra. No subirlo a ningun repositorio.

### 4.4 Lo que garantiza el aislamiento

Comprobado sobre un Redis real:

```
alumno01 escribe en alumno01:*          OK
alumno01 escribe en alumno02:*          NOPERM
alumno01 ejecuta FLUSHALL               NOPERM
alumno01 ejecuta KEYS *                 NOPERM
alumno01 lee CONFIG GET                 NOPERM
alumno02 lee una clave de alumno01      NOPERM
```

Las cinco estructuras funcionan dentro del prefijo propio, incluidas `EXPIRE`,
`TTL` y `SCAN`.

---

## 5. Accesos IAM de los alumnos

Con un grupo de Google es mas limpio que uno por uno:

```bash
gcloud projects add-iam-policy-binding MI_PROYECTO \
  --member="group:curso-bsg@midominio.com" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding MI_PROYECTO \
  --member="group:curso-bsg@midominio.com" \
  --role="roles/bigquery.dataViewer"
```

| Rol | Permite |
|---|---|
| `bigquery.jobUser` | Ejecutar consultas, y que se le cobren al proyecto |
| `bigquery.dataViewer` | Leer los datos del conjunto |

**No otorgar `bigquery.dataEditor` ni `bigquery.admin`.** Con lector y ejecutor
alcanza para todo el ejercicio, y nadie puede borrar la tabla a media clase.

Si quiere que creen tablas derivadas, cree un conjunto aparte:

```bash
bq mk --dataset MI_PROYECTO:pagos_alumnos
bq add-iam-policy-binding --member="group:curso-bsg@midominio.com" \
   --role="roles/bigquery.dataEditor" MI_PROYECTO:pagos_alumnos
```

Asi pueden escribir en ese conjunto y no en el de origen.

---

## 6. Control de costo

La sesion completa procesa unos pocos MB. **El primer TiB de consultas al mes es
gratuito**, de modo que no genera cargo.

Aun asi, conviene poner un limite, porque un alumno puede equivocarse:

```bash
bq update --default_partition_expiration=0 \
  --max_time_travel_hours=48 MI_PROYECTO:pagos
```

Y sobre todo, una cuota de consulta por usuario en la consola, bajo
IAM y administracion, Cuotas: **Query usage per day per user**.
Ponerla en 1 GB por alumno deja margen de sobra y acota cualquier error.

Alerta de presupuesto en la cuenta de facturacion, con umbral bajo, por si acaso.

---

## 7. Desmontar despues de la clase

```bash
gcloud compute instances delete curso-redis --zone=us-central1-a
gcloud compute firewall-rules delete curso-redis-6379
rm credenciales_alumnos.csv acl_alumnos.conf
```

BigQuery se puede dejar: el almacenamiento de 4 MB no cuesta de forma
apreciable, y los alumnos podrian necesitarlo para el proyecto final. Si prefiere
quitarlo:

```bash
bq rm -r -f MI_PROYECTO:pagos
```

Retirar tambien los roles IAM cuando termine el periodo del proyecto final.

---

## 8. Lista de verificacion

- [ ] `bq query 'SELECT COUNT(*)'` devuelve 5000
- [ ] La tabla esta particionada por `fecha_hora` y agrupada
- [ ] `c4_final_b6_valida_sql.sh` reporta cero errores
- [ ] La VM de Redis responde y los ACL estan cargados
- [ ] La regla de firewall NO es `0.0.0.0/0`
- [ ] `credenciales_alumnos.csv` generado y listo para repartir
- [ ] Los roles IAM otorgados al grupo
- [ ] Cuota de consulta por usuario configurada
- [ ] Probado el ejercicio de Redis desde Cloud Shell con un usuario de prueba
- [ ] Probados los cinco ejercicios de BigQuery en la consola

---

## 9. Plan de respaldo

Si algo del aprovisionamiento falla el dia de la clase:

**Si Redis no responde.** Se proyecta la ejecucion desde la maquina del
instructor y se comenta. El ejercicio 1 pasa a demostracion. Se pierden 15
minutos de practica, no la sesion.

**Si BigQuery no esta accesible para alguien.** El conjunto publico
`bigquery-public-data` esta disponible para cualquier cuenta con
`bigquery.jobUser`, y permite hacer los ejercicios de costo y de anidamiento
sobre otra tabla. Conviene tener identificada una tabla de respaldo con campos
anidados.

**Si falla la red del aula.** La sesion pasa a exposicion con la presentacion y
el proyecto final, que es lo que no depende de conexion.
