# c2_s4_b1_preparacion.md
## Preparacion de la sesion 2.4

**Bases de Datos y SQL con Python | BSG Institute | Capitulo 2, Sesion 2.4**

Continua sobre el entorno de la sesion 2.1. No hay instalacion nueva.
Tiempo estimado: 10 minutos.

---

### 1. Punto de partida

| Elemento | Verificacion |
|---|---|
| Contenedor de PostgreSQL | `docker compose -f c2_s1_b2_docker_compose.yml ps` |
| Base `pagos` cargada | Consulta de conteo, abajo |
| DBeaver conectado | Se abre la conexion |
| `sqlalchemy` | Instalado en la sesion 2.2 |

---

### 2. Verificacion

```bash
docker compose -f c2_s1_b2_docker_compose.yml up -d
```

En DBeaver:

```sql
SELECT COUNT(*) FROM pagos.transacciones;
```

Debe devolver `5000`. Si no, volver a cargar con `c2_s1_b4_carga.py`.

---

### 3. Dato nuevo de esta sesion

La sesion agrega el mensaje de autorizacion, que hasta ahora no estaba en el
modelo. Se genera con:

```bash
python c2_s4_b2_payload.py
```

El script agrega la columna `autorizacion` de tipo `JSONB` a la tabla
`transacciones` y la llena con un mensaje por operacion. Usa la semilla `987654`,
de modo que todos los participantes obtienen los mismos documentos.

Verificacion:

```sql
SELECT COUNT(*) FROM pagos.transacciones WHERE autorizacion IS NOT NULL;
```

Debe devolver `5000`.

**El script puede ejecutarse antes o durante la sesion.** El instructor lo indica.

---

### 4. Repaso previo

Esta sesion se apoya en dos ideas anteriores.

**De la sesion 1.2.** Una regla declarada en la estructura la aplica el motor en
toda escritura. Una validacion escrita en el codigo solo actua cuando ese codigo
corre. Esa distincion vuelve a aparecer hoy, con un giro: el documento acepta
casi cualquier cosa.

**De la sesion 2.1.** La columna `monto` se declaro `NUMERIC(12,2)` para
conservar aritmetica exacta. Hoy se retoma al mapear la tabla con SQLAlchemy.

---

### 5. Lista de verificacion

- [ ] El contenedor esta activo
- [ ] La consulta de conteo devuelve 5000
- [ ] `sqlalchemy` esta instalado
- [ ] DBeaver se conecta a la base `pagos`
- [ ] Se conserva la ficha de seis puntos de PostgreSQL

---

### 6. Continuidad con la sesion anterior

El capitulo 2 ha trabajado con un modelo de esquema fijo: cada tabla declara sus
columnas y el motor rechaza lo que no encaja.

La sesion 2.4 aborda el caso contrario: informacion cuya estructura varia entre
filas y no puede fijarse de antemano. Es tambien la preparacion del capitulo 3,
porque introduce el modelo documental dentro del motor relacional.
