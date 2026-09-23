# c3_s2_b1_preparacion.md
## Preparacion de la sesion 3.2

**Bases de Datos y SQL con Python | BSG Institute | Capitulo 3, Sesion 3.2**

Continua sobre el entorno de la sesion 3.1. No hay motores nuevos.
Tiempo estimado: 10 minutos.

---

### 1. Punto de partida

| Elemento | Verificacion |
|---|---|
| Contenedor de MongoDB | `docker compose -f c3_s1_b2_docker_compose.yml ps` |
| Contenedor de PostgreSQL | Sigue activo, se usa en la sesion 3.3 |
| Coleccion `operaciones` | 5000 documentos |
| `pymongo` y `pandas` | Instalados |

Comprobar la coleccion:

```bash
python -c "import os; from dotenv import load_dotenv; from pymongo import MongoClient; from urllib.parse import quote_plus; load_dotenv(override=True); print(MongoClient(f\"mongodb://{quote_plus(os.getenv('MONGO_USER'))}:{quote_plus(os.getenv('MONGO_PASSWORD'))}@{os.getenv('MONGO_HOST','localhost')}:{os.getenv('MONGO_PORT','27017')}/?authSource=admin\")[os.getenv('MONGO_DB')].operaciones.count_documents({}))"
```

Debe devolver `5000`. Si devuelve cero, ejecutar `c3_s1_b3_carga.py`.

---

### 2. Verificar que el servidor admite lo que usa la sesion

Esta sesion usa capacidades que no todos los servidores compatibles con el
protocolo de MongoDB implementan: varias etapas de agregacion, indices parciales,
validacion de esquema y la estructura completa del plan de ejecucion.

```bash
python c3_s2_b1_verifica.py
```

El script las prueba una por una sobre una coleccion temporal que elimina al
terminar. Con la imagen oficial `mongo:7` deben salir todas disponibles.

Si alguna falla, el mensaje indica cual. La causa habitual es una version del
servidor anterior a la esperada.

---

### 3. Repaso previo

Esta sesion se apoya en dos ideas del capitulo 2 y una de la 3.1.

**De la sesion 2.2.** El orden logico de evaluacion de SQL es fijo:
`FROM`, `WHERE`, `GROUP BY`, `HAVING`, `SELECT`, `ORDER BY`. Hoy se vera que en
MongoDB ese orden lo decide quien escribe la consulta, y que eso tiene
consecuencias.

**De la sesion 2.5.** El diagnostico de un plan se hace comparando los documentos
examinados contra los devueltos. El mismo criterio aplica aqui, con otros
nombres.

**De la sesion 3.1.** La coleccion acepto un documento con el monto escrito como
texto, y `$sum` lo ignoro sin advertir. Hoy se ve como evitarlo.

---

### 4. Lista de verificacion

- [ ] El contenedor de MongoDB esta activo
- [ ] El de PostgreSQL tambien
- [ ] La coleccion `operaciones` tiene 5000 documentos
- [ ] `c3_s2_b1_verifica.py` reporta todas las capacidades disponibles
- [ ] `pandas` esta instalado
- [ ] Se conserva la ficha de seis puntos de MongoDB, con los puntos 2 y 3
      pendientes

---

### 5. Continuidad con la sesion anterior

La sesion 3.1 mostro el modelo documental y lo que se gana y se cede al adoptarlo.
Dejo dos cosas sin resolver: como consultar con eficiencia una coleccion sin
esquema, y como evitar que un dato mal formado entre en los calculos.

La sesion 3.2 responde ambas. La 3.3 usa esas respuestas para decidir cuando
conviene cada motor.
