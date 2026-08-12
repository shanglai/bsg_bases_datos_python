# c1_s1_b1_instalacion.md
## Preparacion del entorno de trabajo

**Sesion 1.1 | Bases de Datos y SQL con Python | BSG Institute**

Esta guia se completa **antes** de la primera sesion. El tiempo estimado es de
30 a 45 minutos. Si algo falla, la seccion final describe la ruta alternativa.

---

### 1. Que se instala en esta sesion

La sesion 1.1 trabaja con **SQLite**, que es un motor embebido: no hay servidor
que levantar ni servicio que administrar, la base de datos completa vive en un
solo archivo. Ademas, el modulo `sqlite3` ya viene incluido en la biblioteca
estandar de Python, de modo que no requiere instalacion.

Los motores que si requieren contenedor (PostgreSQL, MongoDB y Redis) se instalan
a partir de la sesion 2.1. Se pide dejar listo el motor de contenedores desde hoy
para que ninguna sesion posterior se consuma en instalacion.

---

### 2. Requisitos

| Componente | Version minima | Como se verifica |
|---|---|---|
| Python | 3.11 | `python --version` |
| pip | reciente | `pip --version` |
| Motor de contenedores | vigente | `docker --version` |
| Editor o entorno de cuadernos | cualquiera | VS Code, JupyterLab o similar |

Memoria recomendada: 8 GB. Con 4 GB el trabajo local es posible en la sesion 1.1,
pero se vuelve limitado a partir del capitulo 2.

---

### 3. Paso a paso

#### 3.1 Verificar Python

```bash
python --version
```

El resultado debe indicar 3.11 o superior. Si el comando `python` no responde,
probar con `python3`.

#### 3.2 Crear el entorno virtual del curso

Se trabaja dentro de un entorno virtual para que las bibliotecas del curso no
interfieran con otros proyectos del equipo.

```bash
mkdir curso_bd_python
cd curso_bd_python
python -m venv .venv
```

Activarlo:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS o Linux
source .venv/bin/activate
```

El indicador `(.venv)` al inicio de la linea confirma que esta activo.

#### 3.3 Instalar las bibliotecas de esta sesion

```bash
pip install pandas polars
```

Estas dos bibliotecas se usan desde la sesion 2.2 en adelante. Se instalan hoy
para verificar que el entorno funciona.

#### 3.4 Verificar el modulo sqlite3

```bash
python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

Cualquier version igual o superior a 3.35 es suficiente para el curso.

#### 3.5 Dejar listo el motor de contenedores

Instalar Docker Desktop, o bien Podman Desktop o Rancher Desktop si la politica
de la organizacion restringe el primero. Verificar con:

```bash
docker --version
docker run --rm hello-world
```

El segundo comando descarga una imagen minima y la ejecuta. Si responde con el
mensaje de bienvenida, el entorno esta listo para el capitulo 2.

---

### 4. Preparar los datos del caso de estudio

Descargar los archivos de la sesion en el directorio `curso_bd_python` y ejecutar:

```bash
python c1_s1_b2_generar_datos.py
```

Debe producir dos archivos:

- `pagos_plano.csv`, el extracto operativo en formato plano
- `pagos.db`, la base SQLite con una sola tabla llamada `movimientos`

Verificar la carga:

```bash
python c1_s1_b3_primer_contacto.py
```

La salida debe iniciar con `Transacciones en la base: 5000`.

---

### 5. Ruta alternativa

Si el equipo no permite la instalacion local, el curso provee un cuaderno remoto
equivalente. Consideraciones:

- El estado del cuaderno remoto no persiste entre sesiones, de modo que los datos
  se regeneran al inicio de cada clase con el mismo script y la misma semilla.
- La semilla del generador es `987654` y es identica en ambas rutas, por lo que
  todos los participantes obtienen exactamente los mismos datos.

---

### 6. Lista de verificacion

Marcar cada punto antes de la sesion:

- [ ] `python --version` responde 3.11 o superior
- [ ] El entorno virtual se activa correctamente
- [ ] `pandas` y `polars` quedaron instalados
- [ ] `docker run --rm hello-world` responde con el mensaje de bienvenida
- [ ] `python c1_s1_b2_generar_datos.py` produce los dos archivos
- [ ] `python c1_s1_b3_primer_contacto.py` reporta 5000 transacciones

---

### 7. Problemas frecuentes

| Sintoma | Causa probable | Accion |
|---|---|---|
| `python` no se reconoce como comando | Python no esta en la variable PATH | Reinstalar marcando la opcion de agregar al PATH, o usar `python3` |
| El entorno virtual no se activa en PowerShell | Politica de ejecucion restringida | Ejecutar `Set-ExecutionPolicy -Scope Process RemoteSigned` |
| `docker` no responde | El servicio no esta iniciado | Abrir la aplicacion de escritorio y esperar a que el estado sea activo |
| El generador falla al escribir | Falta de permisos en el directorio | Ejecutar desde una carpeta del perfil del usuario |
