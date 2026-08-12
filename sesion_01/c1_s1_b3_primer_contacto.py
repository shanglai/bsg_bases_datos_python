"""
c1_s1_b3_primer_contacto.py
Primer contacto con una base de datos desde Python.

Objetivo de la sesion 1.1: conectarse a un motor embebido y ejecutar consultas
usando la interfaz DB-API 2.0 de la biblioteca estandar. La misma interfaz se
reutiliza en la sesion 2.1 contra PostgreSQL, con otro controlador.

Requisito: haber ejecutado antes c1_s1_b2_generar_datos.py
Ejecucion: python c1_s1_b3_primer_contacto.py
"""

import sqlite3
from pathlib import Path

ARCHIVO_DB = Path("pagos.db")


def bloque_1_conexion_y_cursor():
    """La secuencia minima: conectar, obtener cursor, ejecutar, recuperar."""
    print("=== Bloque 1: conexion y cursor ===")

    conexion = sqlite3.connect(ARCHIVO_DB)
    cursor = conexion.cursor()

    cursor.execute("SELECT COUNT(*) FROM movimientos")
    total = cursor.fetchone()[0]
    print(f"Transacciones en la base: {total}")

    conexion.close()


def bloque_2_recorrer_resultados():
    """fetchone, fetchmany y fetchall resuelven necesidades distintas."""
    print("\n=== Bloque 2: formas de recuperar el resultado ===")

    with sqlite3.connect(ARCHIVO_DB) as conexion:
        cursor = conexion.cursor()
        cursor.execute("SELECT id_transaccion, comercio, monto FROM movimientos LIMIT 100")

        primera = cursor.fetchone()
        print(f"Primera fila: {primera}")

        siguientes = cursor.fetchmany(3)
        print(f"Siguientes tres: {siguientes}")

        restantes = cursor.fetchall()
        print(f"Filas restantes recuperadas: {len(restantes)}")


def bloque_3_filas_por_nombre():
    """row_factory permite acceder a las columnas por nombre."""
    print("\n=== Bloque 3: acceso por nombre de columna ===")

    with sqlite3.connect(ARCHIVO_DB) as conexion:
        conexion.row_factory = sqlite3.Row
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT comercio, ciudad_comercio, monto
            FROM movimientos
            ORDER BY monto DESC
            LIMIT 3
        """)
        for fila in cursor.fetchall():
            print(f"{fila['comercio']:<22} {fila['ciudad_comercio']:<18} {fila['monto']:>10.2f}")


def bloque_4_parametros():
    """Los valores variables se pasan como parametros, nunca concatenados.

    La concatenacion de cadenas en una consulta abre la puerta a la inyeccion
    de codigo. El controlador envia el valor por separado y el motor no lo
    interpreta como instruccion. Este punto se desarrolla en la sesion 2.1.
    """
    print("\n=== Bloque 4: consultas parametrizadas ===")

    ciudad = "Monterrey"
    monto_minimo = 3000

    with sqlite3.connect(ARCHIVO_DB) as conexion:
        cursor = conexion.cursor()

        # Forma correcta: marcadores de posicion y una tupla de valores.
        cursor.execute(
            """SELECT COUNT(*), ROUND(AVG(monto), 2)
               FROM movimientos
               WHERE ciudad_comercio = ? AND monto >= ?""",
            (ciudad, monto_minimo),
        )
        cantidad, promedio = cursor.fetchone()
        print(f"En {ciudad} por encima de {monto_minimo}: {cantidad} operaciones, "
              f"promedio {promedio}")

        # Forma correcta con parametros nombrados.
        cursor.execute(
            """SELECT COUNT(*) FROM movimientos
               WHERE estatus = :estatus AND contracargo = :contracargo""",
            {"estatus": "APROBADA", "contracargo": "S"},
        )
        print(f"Aprobadas con contracargo: {cursor.fetchone()[0]}")


def bloque_5_el_problema_del_archivo_plano():
    """Evidencia de por que este modelo no sirve todavia.

    El mismo comercio aparece bajo varias escrituras y su categoria tampoco es
    consistente. Cualquier agregacion sobre estas columnas produce un resultado
    incorrecto. Este hallazgo es el punto de partida de la sesion 1.2.
    """
    print("\n=== Bloque 5: el problema que deja abierta esta sesion ===")

    with sqlite3.connect(ARCHIVO_DB) as conexion:
        cursor = conexion.cursor()

        cursor.execute("SELECT COUNT(DISTINCT comercio) FROM movimientos")
        print(f"Valores distintos en la columna comercio: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(DISTINCT categoria_comercio) FROM movimientos")
        print(f"Valores distintos en la columna categoria_comercio: {cursor.fetchone()[0]}")

        print("\nVolumen por comercio, tal como esta hoy:")
        cursor.execute("""
            SELECT comercio, COUNT(*) AS operaciones
            FROM movimientos
            GROUP BY comercio
            ORDER BY operaciones DESC
            LIMIT 6
        """)
        for nombre, operaciones in cursor.fetchall():
            print(f"  {nombre:<22} {operaciones:>5}")

        print("\nPregunta para la sesion 1.2: cuantos comercios hay en realidad.")


if __name__ == "__main__":
    if not ARCHIVO_DB.exists():
        raise SystemExit("Falta pagos.db. Ejecuta primero c1_s1_b2_generar_datos.py")

    bloque_1_conexion_y_cursor()
    bloque_2_recorrer_resultados()
    bloque_3_filas_por_nombre()
    bloque_4_parametros()
    bloque_5_el_problema_del_archivo_plano()
