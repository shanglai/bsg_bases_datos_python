"""
c3_s1_b3_carga.py
Carga del caso de estudio en MongoDB.

Toma los datos que ya viven en PostgreSQL y los escribe en MongoDB con
una forma distinta. Ese cambio de forma es el contenido de la sesion.

En el modelo relacional, una operacion vive repartida en cinco tablas y
se recompone con combinaciones. En el modelo documental, la operacion es
UN documento que se lee de una sola vez.

Ese documento no es una copia de la tabla: incorpora el comercio, el
cliente y la tarjeta que en el modelo relacional estaban en catalogos
separados. La decision de que incorporar y que dejar fuera se llama
denormalizacion, y es la decision central del modelado documental.

Requisitos:
    pip install pymongo "psycopg[binary]" python-dotenv
    base pagos en PostgreSQL con la columna autorizacion cargada
    contenedor de MongoDB en ejecucion
    archivo .env con las variables de ambos motores

Ejecucion: python c3_s1_b3_carga.py
"""

import os
from datetime import datetime
from decimal import Decimal

import psycopg
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

COLECCION = "operaciones"
LOTE = 1000


def cadena_postgres():
    return (f"host={os.getenv('PGHOST', 'localhost')} "
            f"port={os.getenv('PGPORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DB')} "
            f"user={os.getenv('POSTGRES_USER')} "
            f"password={os.getenv('POSTGRES_PASSWORD')}")


def uri_mongo():
    return (f"mongodb://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}"
            f"@{os.getenv('MONGO_HOST', 'localhost')}:"
            f"{os.getenv('MONGO_PORT', '27017')}/"
            f"?authSource=admin")


# =====================================================================
# La consulta de origen
#
# Recompone la operacion completa con cuatro combinaciones. Es
# exactamente el trabajo que el modelo documental evita al momento de
# leer, y que paga al momento de escribir.
# =====================================================================

CONSULTA_ORIGEN = """
    SELECT t.id_transaccion, t.fecha_hora, t.monto, t.moneda,
           t.estatus, t.metodo_captura, t.autorizacion,
           c.id_comercio, c.nombre AS comercio, c.categoria, c.ciudad,
           te.id_terminal, te.codigo AS terminal,
           cl.id_cliente, cl.nombre AS cliente, cl.correo,
           ta.id_tarjeta, ta.ultimos4, ta.marca,
           cc.id_contracargo IS NOT NULL AS tiene_contracargo
    FROM pagos.transacciones t
    JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
    JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
    JOIN pagos.tarjetas   ta ON ta.id_tarjeta  = t.id_tarjeta
    JOIN pagos.clientes   cl ON cl.id_cliente  = ta.id_cliente
    LEFT JOIN pagos.contracargos cc ON cc.id_transaccion = t.id_transaccion
    ORDER BY t.id_transaccion
"""


def construir_documento(fila):
    """Arma el documento a partir de una fila del resultado relacional.

    Tres decisiones de modelado, que se discuten en clase:

    1. El comercio, el cliente y la tarjeta se INCORPORAN al documento,
       en lugar de referenciarse. La consulta habitual siempre los
       necesita, de modo que incorporarlos evita cinco combinaciones.
       El costo es la redundancia: el nombre del comercio se repite en
       cada una de sus operaciones.

    2. Se conservan ademas los identificadores de origen. Permiten
       volver al modelo relacional y son la unica via para corregir un
       nombre de comercio en todas las operaciones.

    3. El mensaje de autorizacion entra tal cual, sin transformacion.
       Ya era un documento anidado dentro de PostgreSQL.

    El identificador de la transaccion se usa como _id. MongoDB exige
    que _id sea unico y lo indexa siempre, de modo que aprovecharlo
    evita un indice adicional y garantiza que la carga sea idempotente.
    """
    return {
        "_id": fila["id_transaccion"],
        "fecha_hora": fila["fecha_hora"],
        # El monto se convierte a float, que es el tipo numerico habitual
        # en BSON. La conversion PIERDE la exactitud decimal que la
        # sesion 2.1 establecio al declarar la columna como NUMERIC(12,2).
        #
        # Comprobado sobre este conjunto:
        #   suma en PostgreSQL, tipo NUMERIC : 10105599.87
        #   suma en MongoDB, tipo float      : 10105599.869999962
        #
        # Es el mismo fenomeno de la sesion 2.2 con pandas, ahora en el
        # almacenamiento y no solo en la lectura.
        #
        # BSON si ofrece Decimal128, que conserva la exactitud:
        #   from bson.decimal128 import Decimal128
        #   "monto": Decimal128(fila["monto"])
        # A cambio, los operadores de agregacion lo manejan con mas
        # restricciones y el valor llega a Python como Decimal128, no
        # como numero. La eleccion se discute en clase.
        "monto": float(fila["monto"]),
        "moneda": fila["moneda"],
        "estatus": fila["estatus"],
        "metodo_captura": fila["metodo_captura"],
        "tiene_contracargo": fila["tiene_contracargo"],

        "comercio": {
            "id": fila["id_comercio"],
            "nombre": fila["comercio"],
            "categoria": fila["categoria"],
            "ciudad": fila["ciudad"],
        },
        "terminal": {
            "id": fila["id_terminal"],
            "codigo": fila["terminal"],
        },
        "cliente": {
            "id": fila["id_cliente"],
            "nombre": fila["cliente"],
            "correo": fila["correo"],
        },
        "tarjeta": {
            "id": fila["id_tarjeta"],
            "ultimos4": fila["ultimos4"],
            "marca": fila["marca"],
        },

        "autorizacion": fila["autorizacion"],
    }


def leer_origen():
    with psycopg.connect(cadena_postgres()) as conexion:
        with conexion.cursor(row_factory=psycopg.rows.dict_row) as cursor:
            cursor.execute(CONSULTA_ORIGEN)
            return cursor.fetchall()


def cargar(documentos):
    cliente = MongoClient(uri_mongo())
    base = cliente[os.getenv("MONGO_DB", "pagos")]

    # La coleccion se elimina y se vuelve a crear. En MongoDB no hay
    # DDL: la coleccion existe desde el primer documento insertado.
    base[COLECCION].drop()
    print(f"Coleccion {COLECCION} vaciada.")

    for inicio in range(0, len(documentos), LOTE):
        base[COLECCION].insert_many(documentos[inicio:inicio + LOTE])
    print(f"Documentos insertados: {base[COLECCION].count_documents({})}")

    return cliente, base


def verificar(base):
    print("\n--- Verificacion ---")
    coleccion = base[COLECCION]

    total = coleccion.count_documents({})
    print(f"Documentos en la coleccion: {total}")

    print("\nUn documento completo se lee sin combinaciones:")
    documento = coleccion.find_one({"metodo_captura": "QR"})
    for clave in ["_id", "monto", "estatus"]:
        print(f"  {clave}: {documento[clave]}")
    print(f"  comercio.nombre: {documento['comercio']['nombre']}")
    print(f"  cliente.nombre:  {documento['cliente']['nombre']}")
    print(f"  autorizacion.captura.aplicacion: "
          f"{documento['autorizacion']['captura']['aplicacion']}")

    print("\nImporte aprobado por comercio, sin combinar nada:")
    resultado = coleccion.aggregate([
        {"$match": {"estatus": "APROBADA"}},
        {"$group": {"_id": "$comercio.nombre",
                    "operaciones": {"$sum": 1},
                    "importe": {"$sum": "$monto"}}},
        {"$sort": {"importe": -1}},
    ])
    for fila in resultado:
        print(f"  {fila['_id']:<20} {fila['operaciones']:>5}  "
              f"{fila['importe']:>14,.2f}")

    print("\nLa redundancia que introduce la denormalizacion:")
    repetidos = coleccion.aggregate([
        {"$group": {"_id": "$comercio.nombre", "veces": {"$sum": 1}}},
        {"$sort": {"veces": -1}},
        {"$limit": 3},
    ])
    for fila in repetidos:
        print(f"  El nombre '{fila['_id']}' se almacena "
              f"{fila['veces']} veces")

    print("""
  Corregir el nombre de un comercio implica actualizar todos esos
  documentos. En el modelo relacional era una sola fila del catalogo.

  Es la contrapartida directa de haber evitado las combinaciones.
""")


def main():
    print("Leyendo el origen desde PostgreSQL...")
    filas = leer_origen()
    print(f"Filas recuperadas: {len(filas)}")

    documentos = [construir_documento(f) for f in filas]
    print(f"Documentos construidos: {len(documentos)}")

    cliente, base = cargar(documentos)
    verificar(base)
    cliente.close()

    print("\nCarga en MongoDB completa.")


if __name__ == "__main__":
    main()
