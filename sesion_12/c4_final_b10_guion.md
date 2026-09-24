# c4_final_b10_guion.md
## Guion de ejecucion de la sesion final

**Bases de Datos y SQL con Python | BSG Institute**

Documento para el instructor.

Duracion: 120 minutos. Presentacion: 21 diapositivas.

**Es una sesion apretada.** Redis y BigQuery en dos horas, mas el proyecto final,
obliga a ver ambos en la superficie. El guion esta calculado para que quepa, y
cada bloque tiene un plan de recorte.

---

## 0. Alistamiento previo

Todo lo de `c4_final_b1_aprovisionamiento.md`, hecho **el dia anterior**.

| Elemento | Estado |
|---|---|
| Tabla `operaciones` en BigQuery | 5000 filas, particionada y agrupada |
| SQL validado con `--dry_run` | Cero errores |
| VM de Redis | Activa, ACL cargadas |
| `credenciales_alumnos.csv` | Impreso o listo para repartir |
| Roles IAM | Otorgados y probados con una cuenta |
| Cuota de consulta por usuario | Configurada |

**Probar con una cuenta de alumno**, no solo con la suya. Es la unica forma de
detectar un permiso faltante antes de la clase.

---

## 1. Recorrido

### Minuto 0 a 10. Acceso y verificacion
**Diapositivas 2 y 3. Modalidad: exposicion.**

Repartir credenciales de Redis. Confirmar que todos entran a la consola de GCP y
ven el conjunto `pagos`.

**Este bloque se puede ir de tiempo.** Si alguien no entra, que trabaje con el
vecino: perder diez minutos aqui compromete la sesion entera.

Con la diapositiva 3, plantear las dos preguntas que ningun motor anterior
responde. Es el hilo que justifica ver dos tecnologias en dos horas.

---

### Minuto 10 a 25. Redis
**Diapositivas 4 a 6. Modalidad: exposicion.**

La tabla comparativa de la diapositiva 4 es el nucleo. El renglon que importa es
el ultimo: si se reinicia, el dato puede perderse.

**De ahi sale todo el criterio:** Redis guarda lo que se puede reconstruir. Una
cache, un contador, un ranking. No el registro de la transaccion.

En la diapositiva 5, las cinco estructuras. No detenerse en cada comando: el
ejercicio las recorre. Lo que hay que dejar es que **la estructura se elige por
la operacion, no por el dato**.

En la 6, el limitador. Punto a subrayar: `INCR` es atomico, y por eso funciona
con concurrencia. El argumento que justifica Redis es la concurrencia, no la
velocidad de una consulta aislada.

---

### Minuto 25 a 40. Ejercicio 1
**Diapositiva 7. Modalidad: practica.**

Cloud Shell, `pip install redis`, ejecutar el script con sus credenciales.

**El momento que vale la pena, minuto 35.** El bloque 4 del script, donde cuatro
operaciones devuelven `NOPERM`.

Preguntar al grupo por que `KEYS *` esta prohibido **para todos**, no solo para
ellos. La respuesta: recorre el espacio completo de claves y bloquea el servidor
mientras lo hace. En una base con millones de claves, ejecutarlo en produccion es
un incidente.

Conectar con el aislamiento: no hay esquemas ni bases separadas por permiso, de
modo que la multi-tenencia se consigue con convencion de nombres mas ACL.

**Si el grupo se atrasa:** basta con que ejecuten el script y vean la salida. La
discusion se hace sobre lo proyectado.

---

### Minuto 40 a 70. BigQuery
**Diapositivas 8 a 14. Modalidad: exposicion con demostracion.**

| Diapositiva | Contenido | Minuto |
|---|---|---|
| 8 | Tabla comparativa contra PostgreSQL | 42 |
| 9 y 10 | **El costo por bytes leidos** | 47 |
| 11 | Subcolumnas, y la diferencia con JSONB | 54 |
| 12 | `UNNEST` y su trampa | 59 |
| 13 | Particion y agrupamiento | 64 |
| 14 | Dataform y preparacion de datos | 68 |

**El momento de mayor valor, minuto 47.** Ejecutar en vivo, con el estimado de
bytes visible:

```sql
SELECT * FROM `proyecto.pagos.operaciones` LIMIT 10;
SELECT estatus, COUNT(*) FROM `proyecto.pagos.operaciones` GROUP BY estatus;
```

Preguntar antes: cual creen que procesa mas bytes.

La respuesta habitual es que el `LIMIT 10` hace la primera barata. No: el limite
recorta lo que se **devuelve**, no lo que se **lee**.

Frase que se llevan: **en BigQuery se nombran las columnas, siempre.**

**Minuto 59.** El `UNNEST` que descarta filas vacias. Es la tercera vez que
aparece el mismo error en el curso: en SQL con `LEFT JOIN` convertido en `INNER`,
en MongoDB con `$unwind`, y aqui. Vale la pena nombrarlo como patron.

**Minuto 64.** `DATE(fecha_hora)` anula la particion. Mismo fenomeno de la sesion
2.5 con los indices. Ejecutar ambas versiones y comparar el estimado.

**Si el grupo se atrasa:** la diapositiva 14, sobre Dataform, se comenta en un
minuto sin demostracion. Es la mas prescindible del bloque.

---

### Minuto 70 a 85. Ejercicio 2
**Diapositiva 15. Modalidad: practica.**

Los cinco ejercicios de `c4_final_b7_taller.md`, en BigQuery Studio.

**Insistir en que anoten el estimado de bytes ANTES de ejecutar.** Es el habito
que la sesion busca dejar, y el unico que les va a servir el lunes.

**Punto de control, minuto 80.** Preguntar que estimados obtuvieron en el
ejercicio 1. Si alguien reporta que `SELECT *` fue mas barato, hay un
malentendido que corregir ahi mismo.

---

### Minuto 85 a 95. Los tres juntos
**Diapositiva 16. Modalidad: discusion.**

La figura de la arquitectura completa: Redis durante la autorizacion, PostgreSQL
al registrar, BigQuery al analizar.

Los dos puntos a dejar dichos:

- Redis **no es el registro**. Es lo que evita ir a PostgreSQL mil veces por
  segundo.
- BigQuery **no es el origen**. Es una copia derivada, pensada para leerse por
  columnas.

---

### Minuto 95 a 110. Proyecto final
**Diapositivas 17 a 19. Modalidad: exposicion.**

Repartir `c4_final_b9_proyecto.md` y recorrerlo.

Lo que hay que dejar clarisimo:

1. **No se pide construir el sistema.** Se pide el diseño, una porcion
   implementada, y el argumento.
2. **Los dos renglones que deciden la calificacion**: que se cede, y que haria
   cambiar la decision.
3. **No se evalua haber elegido los motores que el instructor habria elegido.**

En la diapositiva 19, los cuatro errores frecuentes. El primero merece enfasis:
proponer cuatro motores porque el curso enseño cuatro es el error mas comun, y
cada motor que se agrega hay que operarlo.

**Abrir preguntas aqui**, no al final. Es lo que mas dudas genera.

---

### Minuto 110 a 120. Cierre
**Diapositivas 20 y 21. Modalidad: discusion.**

La tabla de los cinco motores y su momento.

El mensaje de cierre, que conviene decir tal cual:

> Ninguno de los cinco se estudio a fondo. Cada uno tiene libros enteros
> dedicados, y en tres anos las versiones habran cambiado y habra motores que hoy
> no existen.
>
> Lo que si se cubrio a fondo fue el criterio para elegir entre ellos. Eso es lo
> que va a seguir sirviendo.

---

## 2. Plan de recorte, por si se atrasa

En orden de que sacrificar primero:

| Orden | Que se recorta | Cuanto ahorra |
|---|---|---|
| 1 | Diapositiva 14, Dataform sin demostracion | 4 min |
| 2 | Ejercicio adicional de Redis | 3 min |
| 3 | Ejercicios 3 y 4 de BigQuery, se proyectan | 5 min |
| 4 | Diapositiva 16, arquitectura, se comenta rapido | 5 min |

**Lo que NO se recorta, en ningun caso:**

- El minuto 47, el costo por bytes leidos. Es lo unico de BigQuery que les va a
  servir el lunes.
- El bloque del proyecto final. Es el 25 por ciento de su calificacion.

---

## 3. Los tres momentos que sostienen la sesion

1. **Minuto 47.** `SELECT *` con `LIMIT` no es barato. Desarma la intuicion que
   traen de SQL y es el habito mas util que se llevan.
2. **Minuto 35.** Los cuatro `NOPERM` de Redis. Muestran multi-tenencia real en
   un motor sin esquemas.
3. **Minuto 100.** Los dos renglones de la matriz. Es lo que define como se
   califica el proyecto.

---

## 4. Despues de la clase

```bash
gcloud compute instances delete curso-redis --zone=us-central1-a
gcloud compute firewall-rules delete curso-redis-6379
rm credenciales_alumnos.csv acl_alumnos.conf
```

BigQuery se puede dejar hasta que entreguen el proyecto final.
