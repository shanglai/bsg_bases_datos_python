"""
c2_s1_b5_parametros.py
Consultas parametrizadas y prevencion de inyeccion de codigo.

Esta demostracion se ejecuta contra la base ya cargada. Muestra tres
cosas en orden:

    1. que hace una consulta construida por concatenacion de cadenas
    2. que ocurre cuando el valor recibido esta compuesto con intencion
    3. como el parametro resuelve el problema de raiz

Requisitos: base cargada con c2_s1_b4_carga.py
Ejecucion:  python c2_s1_b5_parametros.py
"""

import os

import psycopg
from dotenv import load_dotenv


def cadena_de_conexion():
    load_dotenv()
    return (
        f"host={os.getenv('PGHOST', 'localhost')} "
        f"port={os.getenv('PGPORT', '5432')} "
        f"dbname={os.getenv('POSTGRES_DB')} "
        f"user={os.getenv('POSTGRES_USER')} "
        f"password={os.getenv('POSTGRES_PASSWORD')}"
    )


# =====================================================================
# Bloque 1. La forma incorrecta, con un valor normal
#
# Con una entrada ordinaria, la concatenacion funciona. Ese es
# justamente el motivo de que el error sobreviva tanto tiempo en el
# codigo: durante las pruebas no falla.
# =====================================================================

def bloque_1_concatenacion_con_valor_normal(conexion, ciudad):
    print("=== Bloque 1: concatenacion con un valor ordinario ===")

    consulta = (
        "SELECT COUNT(*) FROM pagos.comercios WHERE ciudad = '" + ciudad + "'"
    )
    print(f"Consulta enviada al motor:\n  {consulta}")

    with conexion.cursor() as cursor:
        cursor.execute(consulta)
        print(f"Resultado: {cursor.fetchone()[0]} comercios\n")


# =====================================================================
# Bloque 2. La misma forma, con un valor compuesto con intencion
#
# El valor deja de comportarse como dato y pasa a formar parte de la
# instruccion. El motor no distingue entre lo que escribio el
# desarrollador y lo que llego desde afuera: recibe una sola cadena.
# =====================================================================

def bloque_2_concatenacion_con_valor_hostil(conexion):
    print("=== Bloque 2: el valor se convierte en instruccion ===")

    # Este valor podria llegar de un formulario, de un parametro de URL
    # o de un archivo. El apostrofe cierra la cadena e inicia otra
    # condicion, siempre verdadera.
    ciudad = "Merida' OR '1'='1"

    consulta = (
        "SELECT COUNT(*) FROM pagos.comercios WHERE ciudad = '" + ciudad + "'"
    )
    print(f"Consulta enviada al motor:\n  {consulta}")

    with conexion.cursor() as cursor:
        cursor.execute(consulta)
        total = cursor.fetchone()[0]

    print(f"Resultado: {total} comercios")
    print("El filtro dejo de aplicarse. La consulta devuelve el catalogo")
    print("completo, no la ciudad solicitada.\n")


# =====================================================================
# Bloque 3. La forma correcta
#
# El marcador %s no es sustitucion de texto. psycopg envia la sentencia
# y los valores por caminos separados, y el motor nunca interpreta el
# valor como parte de la instruccion.
# =====================================================================

def bloque_3_parametros(conexion):
    print("=== Bloque 3: el mismo valor, pasado como parametro ===")

    for ciudad in ["Merida", "Merida' OR '1'='1"]:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM pagos.comercios WHERE ciudad = %s",
                (ciudad,),
            )
            total = cursor.fetchone()[0]
        print(f"  Valor recibido: {ciudad!r:<24} Resultado: {total}")

    print("\nEl segundo valor se busca de forma literal como nombre de")
    print("ciudad. No existe ninguna con ese nombre, de modo que el")
    print("resultado es cero.\n")


# =====================================================================
# Bloque 4. Que envia psycopg en realidad
#
# El metodo as_string muestra la sentencia tal como queda del lado del
# cliente. Sirve para comprobar que el valor viaja entrecomillado y
# escapado, sin capacidad de alterar la estructura.
# =====================================================================

def bloque_4_lo_que_viaja(conexion):
    print("=== Bloque 4: la sentencia tal como se construye ===")

    # En psycopg 3, el cursor ordinario no expone mogrify porque los
    # parametros no se interpolan del lado del cliente: viajan aparte,
    # en el protocolo. ClientCursor si lo hace, y sirve para inspeccionar
    # como quedaria el valor una vez escapado.
    with psycopg.ClientCursor(conexion) as cursor:
        sentencia = cursor.mogrify(
            "SELECT COUNT(*) FROM pagos.comercios WHERE ciudad = %s",
            ("Merida' OR '1'='1",),
        )
    print(f"  {sentencia}")
    print("  El apostrofe quedo duplicado. El valor completo es una sola")
    print("  cadena y no puede alterar la estructura de la sentencia.\n")


# =====================================================================
# Bloque 5. El limite del mecanismo
#
# Los parametros sustituyen valores, no identificadores. Un nombre de
# tabla o de columna no puede pasarse como parametro. Para esos casos
# se usa el modulo sql, que compone identificadores de forma segura.
# =====================================================================

def bloque_5_identificadores(conexion):
    print("=== Bloque 5: cuando lo variable es el nombre de una columna ===")

    from psycopg import sql

    for columna in ["ciudad", "categoria"]:
        consulta = sql.SQL(
            "SELECT {campo}, COUNT(*) FROM pagos.comercios GROUP BY {campo}"
        ).format(campo=sql.Identifier(columna))

        with conexion.cursor() as cursor:
            cursor.execute(consulta)
            resultados = cursor.fetchall()

        print(f"  Agrupado por {columna}: {len(resultados)} grupos")

    print("\n  sql.Identifier valida y entrecomilla el nombre. Un valor")
    print("  arbitrario no puede convertirse en instruccion.\n")


# =====================================================================
# Bloque 6. Consultas parametrizadas de uso cotidiano
# =====================================================================

def bloque_6_uso_cotidiano(conexion):
    print("=== Bloque 6: parametros en consultas reales ===")

    with conexion.cursor() as cursor:
        # Parametros posicionales.
        cursor.execute(
            """SELECT COUNT(*), SUM(monto)
               FROM pagos.transacciones
               WHERE estatus = %s AND monto >= %s""",
            ("APROBADA", 5000),
        )
        cantidad, importe = cursor.fetchone()
        print(f"  Aprobadas de 5000 o mas: {cantidad}, importe {importe:,.2f}")

        # Parametros nombrados. Convenientes cuando son varios o se
        # repiten dentro de la misma sentencia.
        cursor.execute(
            """SELECT c.nombre, COUNT(*) AS operaciones
               FROM pagos.transacciones t
               JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
               JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
               WHERE c.ciudad = %(ciudad)s AND t.metodo_captura = %(captura)s
               GROUP BY c.nombre
               ORDER BY operaciones DESC""",
            {"ciudad": "Ciudad de Mexico", "captura": "QR"},
        )
        for nombre, operaciones in cursor.fetchall():
            print(f"    {nombre:<22} {operaciones:>5}")

        # Una lista se pasa como un solo parametro con ANY.
        cursor.execute(
            """SELECT metodo_captura, COUNT(*)
               FROM pagos.transacciones
               WHERE metodo_captura = ANY(%s)
               GROUP BY metodo_captura
               ORDER BY 2 DESC""",
            (["QR", "CONTACTLESS", "CHIP"],),
        )
        print("\n  Por metodo de captura:")
        for metodo, total in cursor.fetchall():
            print(f"    {metodo:<14} {total:>5}")
    print()


if __name__ == "__main__":
    with psycopg.connect(cadena_de_conexion()) as conexion:
        bloque_1_concatenacion_con_valor_normal(conexion, "Merida")
        bloque_2_concatenacion_con_valor_hostil(conexion)
        bloque_3_parametros(conexion)
        bloque_4_lo_que_viaja(conexion)
        bloque_5_identificadores(conexion)
        bloque_6_uso_cotidiano(conexion)
