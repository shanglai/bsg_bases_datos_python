"""
c2_s1_b4_carga.py
Carga del caso de estudio en PostgreSQL.

Aplica el modelo de c2_s1_b3_ddl_postgres.sql y carga las seis tablas a
partir de pagos_plano.csv, el archivo de la sesion 1.1.

Puntos de la sesion que este script ejercita:
    - conexion con psycopg 3
    - credenciales leidas del entorno, nunca escritas en el codigo
    - carga masiva con COPY
    - una sola transaccion para las seis tablas
    - recuperacion de las identidades generadas por el motor

Requisitos:
    pip install "psycopg[binary]" python-dotenv
    archivo .env en el directorio, a partir de c2_s1_b2_env_ejemplo.txt
    pagos_plano.csv en el directorio
    contenedor de PostgreSQL en ejecucion

Ejecucion: python c2_s1_b4_carga.py
"""

import csv
import os
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ARCHIVO_CSV = Path("pagos_plano.csv")
ARCHIVO_DDL = Path("c2_s1_b3_ddl_postgres.sql")


# =====================================================================
# Credenciales
# =====================================================================

def cadena_de_conexion():
    """Construye la cadena de conexion a partir del entorno.

    load_dotenv lee el archivo .env y coloca sus valores en las
    variables de entorno del proceso. Ningun valor sensible aparece en
    este archivo, de modo que el codigo puede versionarse sin riesgo.

    Si una variable falta, el script se detiene con un mensaje claro en
    lugar de intentar la conexion con un valor vacio.
    """
    load_dotenv()

    requeridas = ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"]
    faltantes = [v for v in requeridas if not os.getenv(v)]
    if faltantes:
        raise SystemExit(
            "Faltan variables de entorno: " + ", ".join(faltantes) +
            "\nCopia c2_s1_b2_env_ejemplo.txt como .env y completa los valores."
        )

    return (
        f"host={os.getenv('PGHOST', 'localhost')} "
        f"port={os.getenv('PGPORT', '5432')} "
        f"dbname={os.getenv('POSTGRES_DB')} "
        f"user={os.getenv('POSTGRES_USER')} "
        f"password={os.getenv('POSTGRES_PASSWORD')}"
    )


# =====================================================================
# Normalizacion de valores, heredada de la sesion 1.2
# =====================================================================

def normalizar_nombre(valor):
    limpio = " ".join(valor.split())
    limpio = limpio.replace("Nortenio", "Norteno").replace("NORTENIO", "NORTENO")
    return limpio.title()


def normalizar_categoria(valor):
    equivalencias = {
        "farm": "Farmacia", "farmacia": "Farmacia",
        "super": "Supermercado", "supermercado": "Supermercado",
        "restaurante": "Restaurante",
        "ropa": "Ropa", "vestimenta": "Ropa",
        "combustible": "Combustible",
        "electro": "Electronica", "electronica": "Electronica",
        "viajes": "Viajes",
    }
    return equivalencias.get(valor.strip().lower(), valor.strip().title())


# =====================================================================
# Extraccion de catalogos
# =====================================================================

def extraer_catalogos(filas):
    comercios, terminales, clientes, tarjetas = (
        OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict())

    for fila in filas:
        nombre = normalizar_nombre(fila["comercio"])
        if nombre not in comercios:
            comercios[nombre] = (nombre,
                                 normalizar_categoria(fila["categoria_comercio"]),
                                 fila["ciudad_comercio"].strip())

        clave_terminal = (nombre, fila["terminal"].strip())
        if clave_terminal not in terminales:
            terminales[clave_terminal] = clave_terminal

        correo = fila["correo_cliente"].strip().lower()
        if correo not in clientes:
            clientes[correo] = (fila["cliente"].strip(), correo)

        clave_tarjeta = (correo, fila["tarjeta_ultimos4"].strip(),
                         fila["marca_tarjeta"].strip())
        if clave_tarjeta not in tarjetas:
            tarjetas[clave_tarjeta] = clave_tarjeta

    print(f"Catalogos: {len(comercios)} comercios, {len(terminales)} terminales, "
          f"{len(clientes)} clientes, {len(tarjetas)} tarjetas")
    return comercios, terminales, clientes, tarjetas


# =====================================================================
# Carga
# =====================================================================

def aplicar_ddl(conexion):
    """Crea el esquema y las seis tablas."""
    conexion.execute(ARCHIVO_DDL.read_text(encoding="utf-8"))
    print("Estructura creada.")


def cargar_comercios(cursor, comercios):
    """Insercion con RETURNING para recuperar la identidad generada.

    Las llaves las genera el motor, no el codigo de Python. RETURNING
    devuelve el valor asignado en la misma sentencia, sin necesidad de
    una segunda consulta.
    """
    mapa = {}
    for nombre, datos in comercios.items():
        cursor.execute(
            """INSERT INTO pagos.comercios (nombre, categoria, ciudad)
               VALUES (%s, %s, %s) RETURNING id_comercio""",
            datos,
        )
        mapa[nombre] = cursor.fetchone()[0]
    return mapa


def cargar_terminales(cursor, terminales, mapa_comercios):
    mapa = {}
    for clave in terminales:
        nombre_comercio, codigo = clave
        cursor.execute(
            """INSERT INTO pagos.terminales (id_comercio, codigo)
               VALUES (%s, %s) RETURNING id_terminal""",
            (mapa_comercios[nombre_comercio], codigo),
        )
        mapa[clave] = cursor.fetchone()[0]
    return mapa


def cargar_clientes(cursor, clientes):
    mapa = {}
    for correo, datos in clientes.items():
        cursor.execute(
            """INSERT INTO pagos.clientes (nombre, correo)
               VALUES (%s, %s) RETURNING id_cliente""",
            datos,
        )
        mapa[correo] = cursor.fetchone()[0]
    return mapa


def cargar_tarjetas(cursor, tarjetas, mapa_clientes):
    mapa = {}
    for clave in tarjetas:
        correo, ultimos4, marca = clave
        cursor.execute(
            """INSERT INTO pagos.tarjetas (id_cliente, ultimos4, marca)
               VALUES (%s, %s, %s) RETURNING id_tarjeta""",
            (mapa_clientes[correo], ultimos4, marca),
        )
        mapa[clave] = cursor.fetchone()[0]
    return mapa


def cargar_transacciones(cursor, filas, mapa_terminales, mapa_tarjetas):
    """Carga masiva con COPY.

    COPY es el mecanismo de carga masiva de PostgreSQL. Frente a cinco
    mil sentencias INSERT independientes, reduce el numero de viajes
    entre el cliente y el servidor y evita analizar la misma sentencia
    una y otra vez.

    La diferencia se vuelve determinante en la sesion 2.5, donde el
    volumen es mucho mayor.
    """
    with cursor.copy(
        """COPY pagos.transacciones
           (id_transaccion, fecha_hora, id_terminal, id_tarjeta,
            monto, moneda, estatus, metodo_captura)
           FROM STDIN"""
    ) as copia:
        for fila in filas:
            nombre_comercio = normalizar_nombre(fila["comercio"])
            correo = fila["correo_cliente"].strip().lower()

            copia.write_row((
                fila["id_transaccion"],
                datetime.strptime(fila["fecha_hora"], "%Y-%m-%d %H:%M:%S"),
                mapa_terminales[(nombre_comercio, fila["terminal"].strip())],
                mapa_tarjetas[(correo, fila["tarjeta_ultimos4"].strip(),
                               fila["marca_tarjeta"].strip())],
                # Decimal, no float. El tipo del lado de Python debe
                # corresponder con NUMERIC del lado del motor.
                Decimal(fila["monto"]),
                fila["moneda"],
                fila["estatus"],
                fila["metodo_captura"],
            ))


def cargar_contracargos(cursor, filas):
    pendientes = [(f["id_transaccion"],) for f in filas if f["contracargo"] == "S"]
    cursor.executemany(
        "INSERT INTO pagos.contracargos (id_transaccion) VALUES (%s)",
        pendientes,
    )
    return len(pendientes)


# =====================================================================
# Verificacion
# =====================================================================

def verificar(conexion, filas_origen):
    print("\n--- Verificacion ---")
    with conexion.cursor() as cursor:
        for tabla in ["comercios", "terminales", "clientes", "tarjetas",
                      "transacciones", "contracargos"]:
            cursor.execute(f"SELECT COUNT(*) FROM pagos.{tabla}")
            print(f"  {tabla:<16} {cursor.fetchone()[0]:>6}")

        cursor.execute("SELECT COUNT(*) FROM pagos.transacciones")
        total = cursor.fetchone()[0]
        print(f"\nOrigen: {filas_origen}   Destino: {total}   "
              f"Coincidencia: {'si' if total == filas_origen else 'NO'}")

        cursor.execute("""
            SELECT c.nombre, COUNT(*) AS operaciones, SUM(t.monto) AS importe
            FROM pagos.transacciones t
            JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
            JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
            WHERE t.estatus = 'APROBADA'
            GROUP BY c.nombre
            ORDER BY importe DESC
        """)
        print("\nImporte aprobado por comercio:")
        for nombre, operaciones, importe in cursor.fetchall():
            print(f"  {nombre:<22} {operaciones:>5}  {importe:>14,.2f}")


# =====================================================================

def main():
    if not ARCHIVO_CSV.exists():
        raise SystemExit(
            "Falta pagos_plano.csv. Ejecuta c1_s1_b2_generar_datos.py")
    if not ARCHIVO_DDL.exists():
        raise SystemExit("Falta c2_s1_b3_ddl_postgres.sql en este directorio.")

    with ARCHIVO_CSV.open(encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    print(f"Filas leidas del origen: {len(filas)}")

    comercios, terminales, clientes, tarjetas = extraer_catalogos(filas)

    # El bloque with abre una transaccion. Al salir sin error, psycopg
    # confirma; ante cualquier excepcion, revierte. La base nunca queda
    # a medio cargar.
    with psycopg.connect(cadena_de_conexion()) as conexion:
        aplicar_ddl(conexion)

        with conexion.cursor() as cursor:
            mapa_comercios = cargar_comercios(cursor, comercios)
            mapa_terminales = cargar_terminales(cursor, terminales, mapa_comercios)
            mapa_clientes = cargar_clientes(cursor, clientes)
            mapa_tarjetas = cargar_tarjetas(cursor, tarjetas, mapa_clientes)

            cargar_transacciones(cursor, filas, mapa_terminales, mapa_tarjetas)
            n_contracargos = cargar_contracargos(cursor, filas)
            print(f"Contracargos cargados: {n_contracargos}")

        verificar(conexion, len(filas))

    print("\nCarga completa.")


if __name__ == "__main__":
    main()
