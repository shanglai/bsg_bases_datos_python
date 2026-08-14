"""
c1_s2_b3_migracion.py
Migracion del archivo plano hacia el modelo normalizado.

Toma pagos_plano.csv, producido en la sesion 1.1, y construye
pagos_normalizado.db con las seis entidades definidas en
c1_s2_b2_ddl_modelo.sql

El script esta dividido en cuatro etapas que corresponden al diagrama
c1_s2_d3_proceso_normalizacion.png

Requisitos:
    pagos_plano.csv en el directorio actual
    c1_s2_b2_ddl_modelo.sql en el directorio actual

Ejecucion: python c1_s2_b3_migracion.py
"""

import csv
import sqlite3
from collections import OrderedDict
from pathlib import Path

ARCHIVO_CSV = Path("pagos_plano.csv")
ARCHIVO_DDL = Path("c1_s2_b2_ddl_modelo.sql")
ARCHIVO_DB = Path("pagos_normalizado.db")


# =====================================================================
# Etapa 0. Normalizacion de valores de texto
# =====================================================================

def normalizar_nombre(valor):
    """Unifica las variantes de escritura de un mismo valor.

    En el archivo plano, un mismo comercio aparece como
    'Super Norteno', 'SUPER NORTENO' y 'Super Nortenio'. La funcion
    reduce esas variantes a una sola forma.

    Esta funcion resuelve el caso presente. No previene el problema de
    fondo: una variante nueva de escritura volveria a producir duplicados.
    La prevencion proviene de la restriccion UNIQUE del modelo, no del
    codigo de carga.
    """
    limpio = " ".join(valor.split())
    limpio = limpio.replace("Nortenio", "Norteno").replace("NORTENIO", "NORTENO")
    return limpio.title()


def normalizar_categoria(valor):
    """Unifica las variantes de categoria a una forma canonica."""
    equivalencias = {
        "farm": "Farmacia",
        "farmacia": "Farmacia",
        "super": "Supermercado",
        "supermercado": "Supermercado",
        "restaurante": "Restaurante",
        "ropa": "Ropa",
        "vestimenta": "Ropa",
        "combustible": "Combustible",
        "electro": "Electronica",
        "electronica": "Electronica",
        "viajes": "Viajes",
    }
    return equivalencias.get(valor.strip().lower(), valor.strip().title())


# =====================================================================
# Etapa 1. Lectura del archivo plano
# =====================================================================

def leer_archivo_plano():
    with ARCHIVO_CSV.open(encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    print(f"Etapa 1. Filas leidas del archivo plano: {len(filas)}")
    return filas


# =====================================================================
# Etapa 2. Extraccion de catalogos
#
# Cada catalogo se construye a partir de los valores distintos de la
# columna correspondiente. El identificador se asigna en el orden de
# primera aparicion, de modo que el resultado es reproducible.
# =====================================================================

def extraer_comercios(filas):
    comercios = OrderedDict()
    for fila in filas:
        nombre = normalizar_nombre(fila["comercio"])
        if nombre not in comercios:
            comercios[nombre] = {
                "id_comercio": len(comercios) + 1,
                "nombre": nombre,
                "categoria": normalizar_categoria(fila["categoria_comercio"]),
                "ciudad": fila["ciudad_comercio"].strip(),
            }
    print(f"Etapa 2. Comercios identificados: {len(comercios)}")
    return comercios


def extraer_terminales(filas, comercios):
    """La llave natural de una terminal es compuesta.

    El codigo de terminal se repite entre comercios de la misma ciudad:
    'TPV01-CIU' aparece tanto en Farmacia Del Sol como en Boutique Iris.
    Identificar la terminal solo por su codigo fusionaria terminales de
    comercios distintos y atribuiria transacciones al comercio equivocado.

    Este es el tipo de hallazgo que produce el ejercicio de modelado y
    que el archivo plano mantenia oculto.
    """
    terminales = OrderedDict()
    for fila in filas:
        codigo = fila["terminal"].strip()
        nombre_comercio = normalizar_nombre(fila["comercio"])
        clave = (nombre_comercio, codigo)
        if clave not in terminales:
            terminales[clave] = {
                "id_terminal": len(terminales) + 1,
                "id_comercio": comercios[nombre_comercio]["id_comercio"],
                "codigo": codigo,
            }
    print(f"Etapa 2. Terminales identificadas: {len(terminales)}")
    return terminales


def extraer_clientes(filas):
    """El correo se usa como identificador natural del cliente.

    El nombre no sirve para ese proposito: dos personas distintas
    pueden llamarse igual. La eleccion de la columna que identifica
    de forma univoca a una entidad es una decision de modelado.
    """
    clientes = OrderedDict()
    for fila in filas:
        correo = fila["correo_cliente"].strip().lower()
        if correo not in clientes:
            clientes[correo] = {
                "id_cliente": len(clientes) + 1,
                "nombre": fila["cliente"].strip(),
                "correo": correo,
            }
    print(f"Etapa 2. Clientes identificados: {len(clientes)}")
    return clientes


def extraer_tarjetas(filas, clientes):
    """Una tarjeta se identifica por la combinacion de cliente y ultimos4.

    Los ultimos cuatro digitos por si solos no son unicos entre clientes
    distintos, de modo que la llave natural es compuesta.
    """
    tarjetas = OrderedDict()
    for fila in filas:
        correo = fila["correo_cliente"].strip().lower()
        clave = (correo, fila["tarjeta_ultimos4"].strip(), fila["marca_tarjeta"].strip())
        if clave not in tarjetas:
            tarjetas[clave] = {
                "id_tarjeta": len(tarjetas) + 1,
                "id_cliente": clientes[correo]["id_cliente"],
                "ultimos4": clave[1],
                "marca": clave[2],
            }
    print(f"Etapa 2. Tarjetas identificadas: {len(tarjetas)}")
    return tarjetas


# =====================================================================
# Etapa 3. Construccion de la tabla de hechos
# =====================================================================

def construir_transacciones(filas, terminales, tarjetas):
    transacciones = []
    contracargos = []

    for fila in filas:
        correo = fila["correo_cliente"].strip().lower()
        clave_tarjeta = (correo, fila["tarjeta_ultimos4"].strip(),
                         fila["marca_tarjeta"].strip())

        transacciones.append({
            "id_transaccion": fila["id_transaccion"],
            "fecha_hora": fila["fecha_hora"],
            "id_terminal": terminales[(normalizar_nombre(fila["comercio"]),
                                       fila["terminal"].strip())]["id_terminal"],
            "id_tarjeta": tarjetas[clave_tarjeta]["id_tarjeta"],
            "monto": float(fila["monto"]),
            "moneda": fila["moneda"],
            "estatus": fila["estatus"],
            "metodo_captura": fila["metodo_captura"],
        })

        if fila["contracargo"] == "S":
            contracargos.append({
                "id_contracargo": len(contracargos) + 1,
                "id_transaccion": fila["id_transaccion"],
                # El archivo plano no conserva la fecha del contracargo.
                "fecha_contracargo": None,
            })

    print(f"Etapa 3. Transacciones preparadas: {len(transacciones)}")
    print(f"Etapa 3. Contracargos preparados: {len(contracargos)}")
    return transacciones, contracargos


# =====================================================================
# Etapa 4. Carga y verificacion
# =====================================================================

def crear_base():
    if ARCHIVO_DB.exists():
        ARCHIVO_DB.unlink()

    conexion = sqlite3.connect(ARCHIVO_DB)
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.executescript(ARCHIVO_DDL.read_text(encoding="utf-8"))
    print("Etapa 4. Estructura creada a partir del archivo DDL.")
    return conexion


def cargar(conexion, comercios, terminales, clientes, tarjetas,
           transacciones, contracargos):
    """La carga se realiza dentro de una sola transaccion.

    El orden importa: las tablas referenciadas se cargan antes que las
    que las referencian. Si alguna llave foranea no resuelve, el motor
    rechaza la operacion completa y la base queda como estaba.
    """
    cursor = conexion.cursor()

    cursor.executemany(
        "INSERT INTO comercios VALUES (:id_comercio, :nombre, :categoria, :ciudad)",
        list(comercios.values()))
    cursor.executemany(
        "INSERT INTO terminales VALUES (:id_terminal, :id_comercio, :codigo)",
        list(terminales.values()))
    cursor.executemany(
        "INSERT INTO clientes VALUES (:id_cliente, :nombre, :correo)",
        list(clientes.values()))
    cursor.executemany(
        "INSERT INTO tarjetas VALUES (:id_tarjeta, :id_cliente, :ultimos4, :marca)",
        list(tarjetas.values()))
    cursor.executemany(
        """INSERT INTO transacciones VALUES
           (:id_transaccion, :fecha_hora, :id_terminal, :id_tarjeta,
            :monto, :moneda, :estatus, :metodo_captura)""",
        transacciones)
    cursor.executemany(
        """INSERT INTO contracargos VALUES
           (:id_contracargo, :id_transaccion, :fecha_contracargo)""",
        contracargos)

    conexion.commit()
    print("Etapa 4. Carga confirmada.")


def verificar(conexion, filas_origen):
    """Comprobaciones minimas de que la migracion no perdio informacion."""
    cursor = conexion.cursor()
    print("\n--- Verificacion ---")

    cursor.execute("SELECT COUNT(*) FROM transacciones")
    total = cursor.fetchone()[0]
    print(f"Transacciones en origen: {filas_origen}")
    print(f"Transacciones en destino: {total}")
    print(f"Coincidencia: {'si' if total == filas_origen else 'NO'}")

    cursor.execute("""
        SELECT ROUND(SUM(monto), 2) FROM transacciones WHERE estatus = 'APROBADA'
    """)
    print(f"Importe aprobado en destino: {cursor.fetchone()[0]}")

    print("\nVolumen por comercio, ya sin variantes de escritura:")
    cursor.execute("""
        SELECT c.nombre, COUNT(*) AS operaciones
        FROM transacciones t
        JOIN terminales te ON te.id_terminal = t.id_terminal
        JOIN comercios  c  ON c.id_comercio  = te.id_comercio
        GROUP BY c.nombre
        ORDER BY operaciones DESC
    """)
    for nombre, operaciones in cursor.fetchall():
        print(f"  {nombre:<22} {operaciones:>5}")


def main():
    if not ARCHIVO_CSV.exists():
        raise SystemExit(
            "Falta pagos_plano.csv. Ejecuta primero c1_s1_b2_generar_datos.py")
    if not ARCHIVO_DDL.exists():
        raise SystemExit("Falta c1_s2_b2_ddl_modelo.sql en este directorio.")

    filas = leer_archivo_plano()

    comercios = extraer_comercios(filas)
    terminales = extraer_terminales(filas, comercios)
    clientes = extraer_clientes(filas)
    tarjetas = extraer_tarjetas(filas, clientes)

    transacciones, contracargos = construir_transacciones(filas, terminales, tarjetas)

    conexion = crear_base()
    cargar(conexion, comercios, terminales, clientes, tarjetas,
           transacciones, contracargos)
    verificar(conexion, len(filas))
    conexion.close()

    print(f"\nBase normalizada escrita: {ARCHIVO_DB}")


if __name__ == "__main__":
    main()
