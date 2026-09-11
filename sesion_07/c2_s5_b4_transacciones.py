"""
c2_s5_b4_transacciones.py
Transacciones, reversion y manejo de errores desde Python.

Puntos de la sesion que este script ejercita:
    - que hace psycopg con la transaccion cuando no se le indica nada
    - confirmacion, reversion y puntos de guardado
    - por que una excepcion deja la conexion inutilizable
    - como distinguir los errores del motor y actuar en consecuencia
    - medicion del efecto de un indice desde Python

Requisitos: base pagos cargada, tabla transacciones_volumen, .env
Ejecucion:  python c2_s5_b4_transacciones.py
"""

import os
import time

import psycopg
from dotenv import load_dotenv

load_dotenv()


def cadena():
    return (f"host={os.getenv('PGHOST', 'localhost')} "
            f"port={os.getenv('PGPORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DB')} "
            f"user={os.getenv('POSTGRES_USER')} "
            f"password={os.getenv('POSTGRES_PASSWORD')}")


def titulo(texto):
    print("\n" + "=" * 70 + f"\n{texto}\n" + "=" * 70)


# =====================================================================
# Bloque 1. El comportamiento predeterminado
# =====================================================================

def bloque_1_predeterminado():
    titulo("Bloque 1: que hace psycopg si no se le indica nada")

    print("""
  psycopg 3 abre una transaccion en cuanto se ejecuta la primera
  sentencia, y NO la confirma sola. Hay tres formas de cerrarla:

    conexion.commit()          confirma de forma explicita
    conexion.rollback()        revierte de forma explicita
    salir del bloque with      confirma si no hubo excepcion,
                               revierte si la hubo

  El error clasico consiste en ejecutar un INSERT, cerrar el programa y
  no encontrar el dato. La transaccion nunca se confirmo.
""")

    with psycopg.connect(cadena()) as conexion:
        conexion.execute("DROP TABLE IF EXISTS pagos.demo_tx")
        conexion.execute(
            "CREATE TABLE pagos.demo_tx (id INT PRIMARY KEY, nota TEXT)")
        conexion.commit()

    # Insercion sin confirmar, revirtiendo a proposito.
    conexion = psycopg.connect(cadena())
    conexion.execute("INSERT INTO pagos.demo_tx VALUES (1, 'sin confirmar')")
    print(f"  Dentro de la transaccion: "
          f"{conexion.execute('SELECT COUNT(*) FROM pagos.demo_tx').fetchone()[0]} fila")
    conexion.rollback()
    print(f"  Despues del rollback:     "
          f"{conexion.execute('SELECT COUNT(*) FROM pagos.demo_tx').fetchone()[0]} filas")
    conexion.close()

    # Con el bloque with, la confirmacion es automatica al salir sin error.
    with psycopg.connect(cadena()) as conexion:
        conexion.execute("INSERT INTO pagos.demo_tx VALUES (2, 'confirmada')")

    with psycopg.connect(cadena()) as conexion:
        total = conexion.execute(
            "SELECT COUNT(*) FROM pagos.demo_tx").fetchone()[0]
    print(f"  Tras salir del bloque with: {total} fila confirmada")


# =====================================================================
# Bloque 2. Todo o nada
# =====================================================================

def bloque_2_todo_o_nada():
    titulo("Bloque 2: la transferencia que falla a la mitad")

    with psycopg.connect(cadena()) as conexion:
        conexion.execute("DROP TABLE IF EXISTS pagos.saldos")
        conexion.execute("""
            CREATE TABLE pagos.saldos (
                id_cuenta INT PRIMARY KEY,
                saldo NUMERIC(12,2) NOT NULL CHECK (saldo >= 0))
        """)
        conexion.execute("INSERT INTO pagos.saldos VALUES (1, 1000), (2, 500)")

    def estado(conexion, etiqueta):
        filas = conexion.execute(
            "SELECT id_cuenta, saldo FROM pagos.saldos ORDER BY id_cuenta"
        ).fetchall()
        print(f"  {etiqueta:<24} {filas}")

    # Caso que funciona.
    with psycopg.connect(cadena()) as conexion:
        estado(conexion, "Antes:")
        conexion.execute("UPDATE pagos.saldos SET saldo = saldo - 300 WHERE id_cuenta = 1")
        conexion.execute("UPDATE pagos.saldos SET saldo = saldo + 300 WHERE id_cuenta = 2")
        estado(conexion, "Transferencia de 300:")

    # Caso que falla en el segundo paso.
    print()
    try:
        with psycopg.connect(cadena()) as conexion:
            conexion.execute(
                "UPDATE pagos.saldos SET saldo = saldo - 5000 WHERE id_cuenta = 1")
            estado(conexion, "Cargo aplicado:")
            # Esta linea nunca se alcanza: el CHECK ya rechazo el cargo.
            conexion.execute(
                "UPDATE pagos.saldos SET saldo = saldo + 5000 WHERE id_cuenta = 2")
    except psycopg.errors.CheckViolation as error:
        print(f"  Error del motor: {str(error).splitlines()[0]}")

    with psycopg.connect(cadena()) as conexion:
        estado(conexion, "Despues del error:")

    print("""
  El bloque with revirtio la transaccion completa al propagarse la
  excepcion. El dinero no desaparecio de una cuenta sin llegar a la
  otra.

  Sin transaccion, con confirmacion despues de cada sentencia, el primer
  cargo habria quedado aplicado y el abono no.
""")


# =====================================================================
# Bloque 3. La conexion inutilizable
# =====================================================================

def bloque_3_conexion_abortada():
    titulo("Bloque 3: por que la conexion deja de responder tras un error")

    conexion = psycopg.connect(cadena())
    try:
        conexion.execute("SELECT 1")
        conexion.execute("SELECT * FROM tabla_que_no_existe")
    except psycopg.errors.UndefinedTable as error:
        print(f"  Primer error: {str(error).splitlines()[0]}")

    # La transaccion quedo abortada. Cualquier sentencia posterior falla.
    try:
        conexion.execute("SELECT 1")
    except psycopg.errors.InFailedSqlTransaction as error:
        print(f"  Segundo error: {str(error).splitlines()[0]}")

    conexion.rollback()
    print(f"  Tras rollback, la conexion responde: "
          f"{conexion.execute('SELECT 1').fetchone()[0]}")
    conexion.close()

    print("""
  Una vez que una sentencia falla, PostgreSQL marca la transaccion como
  abortada y rechaza todo lo demas hasta que se revierta.

  Es una fuente frecuente de confusion: el mensaje de la segunda
  sentencia no dice nada sobre la causa real, que fue la primera.

  Dos formas de manejarlo:
    rollback explicito en el bloque except
    un punto de guardado antes de la sentencia que puede fallar
""")


# =====================================================================
# Bloque 4. Puntos de guardado
# =====================================================================

def bloque_4_puntos_de_guardado():
    titulo("Bloque 4: revertir una parte sin perder el resto")

    with psycopg.connect(cadena()) as conexion:
        conexion.execute("DELETE FROM pagos.demo_tx")
        conexion.execute("INSERT INTO pagos.demo_tx VALUES (1, 'primera')")

        # transaction() anidado crea un punto de guardado.
        try:
            with conexion.transaction():
                conexion.execute("INSERT INTO pagos.demo_tx VALUES (2, 'segunda')")
                # Llave duplicada: falla y revierte solo hasta el punto.
                conexion.execute("INSERT INTO pagos.demo_tx VALUES (1, 'repetida')")
        except psycopg.errors.UniqueViolation:
            print("  El bloque anidado fallo y se revirtio solo el.")

        conexion.execute("INSERT INTO pagos.demo_tx VALUES (3, 'tercera')")

    with psycopg.connect(cadena()) as conexion:
        filas = conexion.execute(
            "SELECT id, nota FROM pagos.demo_tx ORDER BY id").fetchall()
    print(f"  Resultado final: {filas}")

    print("""
  Las filas 1 y 3 quedaron confirmadas. La 2 se perdio junto con el
  error, porque estaba dentro del bloque anidado.

  Es el patron util para una carga por lotes en la que algunos
  registros pueden venir mal y no se quiere perder el resto.
""")


# =====================================================================
# Bloque 5. Distinguir los errores del motor
# =====================================================================

def bloque_5_tipos_de_error():
    titulo("Bloque 5: no todos los errores se tratan igual")

    print("""
  psycopg expone una jerarquia de excepciones que corresponde con los
  codigos de error de PostgreSQL. Distinguirlos permite decidir que
  hacer, en lugar de capturar todo con un except generico.

    UniqueViolation        el registro ya existe. Puede ser esperado.
    ForeignKeyViolation    la referencia no existe. Dato mal formado.
    CheckViolation         valor fuera del dominio. Dato invalido.
    NotNullViolation       falta un campo obligatorio.
    UndefinedTable         error de programacion, no de datos.
    SerializationFailure   conflicto de concurrencia. Conviene reintentar.
    OperationalError       problema de conexion. Conviene reintentar.

  El criterio practico: los errores de datos se registran y se descartan;
  los de concurrencia y conexion se reintentan; los de programacion se
  propagan.
""")

    casos = [
        ("Llave duplicada",
         "INSERT INTO pagos.demo_tx VALUES (1, 'repetida')"),
        ("Restriccion CHECK",
         "INSERT INTO pagos.saldos VALUES (9, -100)"),
        ("Campo obligatorio",
         "INSERT INTO pagos.saldos (id_cuenta) VALUES (10)"),
        ("Tabla inexistente",
         "SELECT * FROM pagos.no_existe"),
    ]

    for etiqueta, sentencia in casos:
        conexion = psycopg.connect(cadena())
        try:
            conexion.execute(sentencia)
            conexion.rollback()
        except psycopg.Error as error:
            print(f"  {etiqueta:<22} {type(error).__name__:<24} "
                  f"sqlstate {error.sqlstate}")
        finally:
            conexion.close()

    print("""
  El atributo sqlstate contiene el codigo del estandar. Es estable entre
  versiones y sirve para clasificar sin depender del texto del mensaje,
  que cambia con el idioma y con la version.
""")


# =====================================================================
# Bloque 6. Medir el efecto de un indice desde Python
# =====================================================================

def bloque_6_medicion():
    titulo("Bloque 6: medir el efecto de un indice")

    consulta = """
        SELECT COUNT(*), SUM(monto)
        FROM pagos.transacciones_volumen
        WHERE id_tarjeta = %s
          AND fecha_hora BETWEEN %s AND %s
    """
    parametros = (42, "2026-03-01", "2026-03-31")

    def medir(conexion, repeticiones=5):
        """Se mide varias veces y se toma el minimo.

        El promedio incorpora ruido del sistema operativo. El minimo se
        aproxima mejor al costo real de la consulta.
        """
        tiempos = []
        for _ in range(repeticiones):
            inicio = time.perf_counter()
            conexion.execute(consulta, parametros).fetchone()
            tiempos.append(time.perf_counter() - inicio)
        return min(tiempos) * 1000

    with psycopg.connect(cadena()) as conexion:
        conexion.autocommit = True

        indices = conexion.execute("""
            SELECT indexname FROM pg_indexes
            WHERE schemaname = 'pagos' AND tablename = 'transacciones_volumen'
        """).fetchall()
        for (nombre,) in indices:
            conexion.execute(f"DROP INDEX pagos.{nombre}")
        conexion.execute("ANALYZE pagos.transacciones_volumen")

        sin_indice = medir(conexion)
        print(f"  Sin indice: {sin_indice:8.1f} ms")

        conexion.execute("""
            CREATE INDEX idx_medicion
            ON pagos.transacciones_volumen (id_tarjeta, fecha_hora)
        """)
        conexion.execute("ANALYZE pagos.transacciones_volumen")

        con_indice = medir(conexion)
        print(f"  Con indice: {con_indice:8.1f} ms")
        print(f"  Relacion:   {sin_indice / con_indice:8.1f} veces")

        tamano = conexion.execute(
            "SELECT pg_size_pretty(pg_relation_size('pagos.idx_medicion'))"
        ).fetchone()[0]
        print(f"  Costo en espacio del indice: {tamano}")

    print("""
  Advertencia sobre la medicion: la primera ejecucion incluye la lectura
  de bloques desde disco, y las siguientes los encuentran en memoria. Por
  eso se repite y se toma el minimo.

  Una medicion honesta declara cuantas repeticiones hizo y que estadistico
  reporta. Un solo cronometraje no dice gran cosa.
""")


def limpiar():
    with psycopg.connect(cadena()) as conexion:
        conexion.execute("DROP TABLE IF EXISTS pagos.demo_tx")
        conexion.execute("DROP TABLE IF EXISTS pagos.saldos")


if __name__ == "__main__":
    bloque_1_predeterminado()
    bloque_2_todo_o_nada()
    bloque_3_conexion_abortada()
    bloque_4_puntos_de_guardado()
    bloque_5_tipos_de_error()
    bloque_6_medicion()
    limpiar()
    print("\nTablas de demostracion eliminadas.")
