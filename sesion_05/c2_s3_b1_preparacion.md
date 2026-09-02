# c2_s3_b1_preparacion.md
## Preparacion de la sesion 2.3

**Bases de Datos y SQL con Python | BSG Institute | Capitulo 2, Sesion 2.3**

Esta sesion continua sobre el entorno de la sesion 2.1. No hay instalacion nueva.
Tiempo estimado: 5 minutos.

---

### 1. Punto de partida

| Elemento | Verificacion |
|---|---|
| Contenedor de PostgreSQL | `docker compose -f c2_s1_b2_docker_compose.yml ps` |
| Base `pagos` cargada | Consulta de conteo, abajo |
| DBeaver conectado | Se abre la conexion |
| `pandas` y `polars` | Instalados en la sesion 2.2 |

---

### 2. Verificacion

```bash
docker compose -f c2_s1_b2_docker_compose.yml up -d
```

En DBeaver:

```sql
SELECT COUNT(*) FROM pagos.transacciones;
```

Debe devolver `5000`. Si devuelve cero o falla, volver a cargar:

```bash
python c2_s1_b4_carga.py
```

---

### 3. Repaso previo

Esta sesion se apoya en dos puntos de la sesion 2.2. Conviene tenerlos frescos.

**El orden logico de evaluacion.** La consulta se escribe empezando por `SELECT`
y el motor la evalua empezando por `FROM`:

```
FROM y JOIN  ->  WHERE  ->  GROUP BY  ->  HAVING  ->  SELECT  ->  ORDER BY
```

**Que hace GROUP BY.** Colapsa cada grupo en una sola fila. Toda columna del
`SELECT` debe estar en el `GROUP BY` o dentro de una funcion de agregacion.

La sesion 2.3 parte justamente del limite que impone ese comportamiento.

---

### 4. Lista de verificacion

- [ ] El contenedor esta activo
- [ ] La consulta de conteo devuelve 5000
- [ ] DBeaver se conecta a la base `pagos`
- [ ] Se recuerda el orden logico de evaluacion
- [ ] Se conserva la ficha de seis puntos de PostgreSQL

---

### 5. Continuidad con la sesion anterior

La sesion 2.2 respondio preguntas del tipo cuanto sumo cada grupo. El resultado
es una fila por grupo y el detalle desaparece.

La sesion 2.3 responde preguntas del tipo como se fue formando ese total, sin
perder el detalle. Es la diferencia entre un reporte de totales y un analisis de
comportamiento.
