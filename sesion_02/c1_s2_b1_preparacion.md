# c1_s2_b1_preparacion.md
## Punto de partida de la sesion 1.2

**Bases de Datos y SQL con Python | BSG Institute | Capitulo 1, Sesion 1.2**

Esta sesion no requiere instalar software nuevo. Continua sobre el entorno de la
sesion 1.1 y sobre los datos ya generados.

---

### 1. Que se necesita

| Elemento | Origen | Como se obtiene |
|---|---|---|
| Entorno virtual activo | Sesion 1.1 | `source .venv/bin/activate` |
| `pagos_plano.csv` | Sesion 1.1 | Se genera con `c1_s1_b2_generar_datos.py` |
| `c1_s2_b2_ddl_modelo.sql` | Esta sesion | Se entrega en clase |
| `c1_s2_b3_migracion.py` | Esta sesion | Se entrega en clase |

---

### 2. Verificacion del punto de partida

Ejecutar en el directorio de trabajo:

```bash
python -c "import csv; print(sum(1 for _ in csv.reader(open('pagos_plano.csv'))) - 1)"
```

El resultado debe ser `5000`.

Si el archivo no existe, regenerarlo:

```bash
python c1_s1_b2_generar_datos.py
```

La semilla es `987654` y no debe modificarse. Garantiza que todos los
participantes trabajen sobre datos identicos, condicion necesaria para comparar
resultados durante la revision en vivo.

---

### 3. Herramienta de diagramacion

La primera parte del taller se resuelve en papel o en herramienta de
diagramacion. Cualquiera de estas opciones es valida:

- Papel y lapiz, fotografiado para la entrega
- Cualquier herramienta de diagramas de propósito general
- PlantUML, si se desea versionar el modelo como texto

Los diagramas del curso se generan con PlantUML y con la biblioteca `diagrams`.
El archivo `c1_s2_b0_diagramas.py` los reproduce. No es requisito para el
participante.

---

### 4. Instalacion de las herramientas de diagramacion (opcional)

Solo para quien desee reproducir o modificar los diagramas del curso.

```bash
pip install diagrams
```

Requiere ademas dos dependencias del sistema operativo:

| Dependencia | Windows | macOS | Linux |
|---|---|---|---|
| Graphviz | `winget install graphviz` | `brew install graphviz` | `apt install graphviz` |
| Java | `winget install Microsoft.OpenJDK.21` | `brew install openjdk` | `apt install default-jre` |

El archivo `plantuml.jar` se descarga desde `https://plantuml.com/download` y se
coloca en el mismo directorio que el script.

---

### 5. Lista de verificacion

- [ ] El entorno virtual se activa correctamente
- [ ] `pagos_plano.csv` existe y contiene 5000 filas
- [ ] Se cuenta con una herramienta para dibujar el modelo
- [ ] Se conserva la ficha de seis puntos de SQLite elaborada en la sesion 1.1

---

### 6. Continuidad con la sesion anterior

La sesion 1.1 cerro con un hallazgo: la columna `comercio` del archivo plano
contiene diecisiete valores distintos que corresponden a siete comercios reales.
Toda agregacion sobre esa columna produce un resultado incorrecto.

La sesion 1.2 responde a la pregunta que ese hallazgo dejo abierta: que estructura
de datos impide que un mismo comercio quede registrado bajo varias escrituras.
