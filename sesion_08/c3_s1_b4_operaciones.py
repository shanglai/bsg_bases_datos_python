"""
c3_s1_b4_operaciones.py
Operaciones sobre la coleccion: insercion, consulta, actualizacion y borrado.

Cada bloque contrasta la operacion de MongoDB con su equivalente en SQL,
para apoyarse en lo que el grupo ya sabe del capitulo 2.

Requisitos: coleccion cargada con c3_s1_b3_carga.py, .env presente
Ejecucion:  python c3_s1_b4_operaciones.py
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING, MongoClient

load_dotenv()
COLECCION = "operaciones"


def uri_mongo():
    return (f"mongodb://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}"
            f"@{os.getenv('MONGO_HOST', 'localhost')}:"
            f"{os.getenv('MONGO_PORT', '27017')}/?authSource=admin")


def titulo(texto):
    print("\n" + "=" * 70 + f"\n{texto}\n" + "=" * 70)


# =====================================================================
# Bloque 1. Vocabulario
# =====================================================================

def bloque_1_vocabulario(base):
    titulo("Bloque 1: el vocabulario, contra el que ya se conoce")

    print("""
  SQL                        MongoDB
  -------------------------  --------------------------------
  base de datos              base de datos
  tabla                      coleccion
  fila                       documento
  columna                    campo
  llave primaria             _id
  esquema declarado con DDL  no hay. La coleccion nace con el
                             primer documento insertado
""")

    print(f"  Colecciones existentes: {base.list_collection_names()}")
    print(f"  Documentos en {COLECCION}: "
          f"{base[COLECCION].count_documents({})}")

    # No hay CREATE TABLE. La coleccion aparece al insertar.
    base["coleccion_efimera"].insert_one({"nota": "existo desde ahora"})
    print(f"  Tras un insert: {sorted(base.list_collection_names())}")
    base["coleccion_efimera"].drop()


# =====================================================================
# Bloque 2. Consulta
# =====================================================================

def bloque_2_consulta(base):
    titulo("Bloque 2: consultar")
    coleccion = base[COLECCION]

    # find_one equivale a SELECT ... LIMIT 1
    documento = coleccion.find_one({"estatus": "RECHAZADA"})
    print(f"\n  find_one: {documento['_id']}, {documento['comercio']['nombre']}")

    # La proyeccion equivale a la lista de columnas del SELECT.
    # 0 excluye, 1 incluye. _id se incluye salvo que se excluya.
    print("\n  Proyeccion, equivalente a SELECT id, monto, comercio:")
    for d in coleccion.find({"estatus": "APROBADA"},
                            {"_id": 1, "monto": 1, "comercio.nombre": 1}).limit(3):
        print(f"    {d}")

    # Acceso a campos anidados con notacion de punto.
    print("\n  Filtro sobre campo anidado (comercio.ciudad):")
    print(f"    {coleccion.count_documents({'comercio.ciudad': 'Merida'})} "
          f"operaciones en Merida")

    # Operadores de comparacion.
    print("\n  Operadores de comparacion:")
    consultas = {
        "$gt   monto > 20000": {"monto": {"$gt": 20000}},
        "$gte  monto >= 20000": {"monto": {"$gte": 20000}},
        "$in   marca en lista": {"tarjeta.marca": {"$in": ["AMEX", "VISA"]}},
        "$ne   estatus != APROBADA": {"estatus": {"$ne": "APROBADA"}},
        "$exists  trae bloque riesgo": {"autorizacion.riesgo": {"$exists": True}},
    }
    for etiqueta, filtro in consultas.items():
        print(f"    {etiqueta:<32} {coleccion.count_documents(filtro):>6}")

    # Varias condiciones. Sin operador, se combinan con Y.
    print("\n  Condiciones combinadas:")
    filtro = {"estatus": "APROBADA",
              "comercio.categoria": "Electronica",
              "monto": {"$gt": 15000}}
    print(f"    Electronica aprobada de mas de 15000: "
          f"{coleccion.count_documents(filtro)}")

    # O explicito.
    filtro = {"$or": [{"metodo_captura": "QR"},
                      {"metodo_captura": "CONTACTLESS"}]}
    print(f"    QR o CONTACTLESS: {coleccion.count_documents(filtro)}")

    # Ordenamiento y limite.
    print("\n  Las tres operaciones de mayor monto:")
    for d in coleccion.find({"estatus": "APROBADA"}).sort(
            "monto", DESCENDING).limit(3):
        print(f"    {d['_id']}  {d['monto']:>12,.2f}  "
              f"{d['comercio']['nombre']}")

    print("""
  Equivalencias con SQL:

    find(filtro, proyeccion)   SELECT proyeccion FROM ... WHERE filtro
    sort(campo, DESCENDING)    ORDER BY campo DESC
    limit(n)                   LIMIT n
    skip(n)                    OFFSET n
    count_documents(filtro)    SELECT COUNT(*) ... WHERE filtro
""")


# =====================================================================
# Bloque 3. Insercion
# =====================================================================

def bloque_3_insercion(base):
    titulo("Bloque 3: insertar")
    coleccion = base[COLECCION]

    antes = coleccion.count_documents({})

    nuevo = {
        "_id": "TRXDEMO001",
        "fecha_hora": datetime(2026, 7, 1, 12, 30, 0),
        "monto": 1234.56,
        "moneda": "MXN",
        "estatus": "APROBADA",
        "metodo_captura": "QR",
        "tiene_contracargo": False,
        "comercio": {"id": 1, "nombre": "Cafe Aurora",
                     "categoria": "Restaurante", "ciudad": "Guadalajara"},
        "cliente": {"id": 1, "nombre": "Demo Demo", "correo": "demo@correo.mx"},
        "tarjeta": {"id": 1, "ultimos4": "0000", "marca": "VISA"},
        "autorizacion": {"version": "2.1",
                         "captura": {"metodo": "QR", "aplicacion": "CoDi"}},
    }
    resultado = coleccion.insert_one(nuevo)
    print(f"\n  insert_one -> _id insertado: {resultado.inserted_id}")

    # El esquema flexible en accion: un documento con campos que ningun
    # otro tiene, en la misma coleccion.
    coleccion.insert_one({
        "_id": "TRXDEMO002",
        "monto": 500,
        "estatus": "APROBADA",
        "campo_que_nadie_mas_tiene": "aqui esta",
        "estructura_distinta": {"nivel": {"profundo": [1, 2, 3]}},
    })
    print("  Segundo documento insertado, con campos que ningun otro tiene.")
    print("  MongoDB no lo rechaza: no hay esquema que validar.")

    print(f"\n  Documentos: {antes} -> {coleccion.count_documents({})}")

    print("""
  Comparacion con el capitulo 2:

    En PostgreSQL, un INSERT con una columna inexistente falla. Aqui el
    documento entra sin objecion.

    Es la ventaja y el riesgo del modelo, en la misma linea. La sesion
    3.3 evalua cuando esa flexibilidad compensa lo que se cede.
""")


# =====================================================================
# Bloque 4. Actualizacion
# =====================================================================

def bloque_4_actualizacion(base):
    titulo("Bloque 4: actualizar")
    coleccion = base[COLECCION]

    # $set modifica campos. Sin $set, el documento se REEMPLAZA entero.
    coleccion.update_one({"_id": "TRXDEMO001"},
                         {"$set": {"estatus": "REVERSADA"}})
    documento = coleccion.find_one({"_id": "TRXDEMO001"})
    print(f"\n  update_one con $set -> estatus: {documento['estatus']}")
    print(f"  El resto del documento sigue completo: "
          f"{len(documento)} campos")

    # El error clasico: omitir $set reemplaza el documento entero.
    coleccion.insert_one({"_id": "TRXDEMO003", "monto": 100,
                          "estatus": "APROBADA", "moneda": "MXN"})
    coleccion.replace_one({"_id": "TRXDEMO003"}, {"estatus": "REVERSADA"})
    documento = coleccion.find_one({"_id": "TRXDEMO003"})
    print(f"\n  replace_one -> el documento quedo con {len(documento)} campos: "
          f"{sorted(documento.keys())}")
    print("  El monto y la moneda desaparecieron. Es el error mas comun.")

    # Actualizacion de campo anidado, con notacion de punto.
    coleccion.update_one(
        {"_id": "TRXDEMO001"},
        {"$set": {"comercio.categoria": "Cafeteria"}})
    documento = coleccion.find_one({"_id": "TRXDEMO001"})
    print(f"\n  Campo anidado actualizado: "
          f"{documento['comercio']['categoria']}")

    # Otros operadores de actualizacion.
    coleccion.update_one({"_id": "TRXDEMO001"}, {"$inc": {"monto": 100}})
    coleccion.update_one({"_id": "TRXDEMO001"}, {"$unset": {"moneda": ""}})
    documento = coleccion.find_one({"_id": "TRXDEMO001"})
    print(f"  $inc -> monto: {documento['monto']}")
    print(f"  $unset -> tiene moneda: {'moneda' in documento}")

    # update_many alcanza varios documentos.
    resultado = coleccion.update_many(
        {"comercio.nombre": "Cafe Aurora"},
        {"$set": {"comercio.revisado": True}})
    print(f"\n  update_many -> documentos modificados: "
          f"{resultado.modified_count}")

    print("""
  Punto de la sesion:

    Ese update_many es la contrapartida de la denormalizacion. En el
    modelo relacional, cambiar un atributo del comercio era modificar
    UNA fila del catalogo. Aqui son cientos de documentos.

    Y no es atomico entre documentos: si el proceso se interrumpe a la
    mitad, unos quedan actualizados y otros no.
""")


# =====================================================================
# Bloque 5. Borrado
# =====================================================================

def bloque_5_borrado(base):
    titulo("Bloque 5: borrar")
    coleccion = base[COLECCION]

    resultado = coleccion.delete_one({"_id": "TRXDEMO002"})
    print(f"\n  delete_one -> eliminados: {resultado.deleted_count}")

    resultado = coleccion.delete_many({"_id": {"$regex": "^TRXDEMO"}})
    print(f"  delete_many -> eliminados: {resultado.deleted_count}")

    # Deshacer el cambio del bloque anterior.
    coleccion.update_many({"comercio.nombre": "Cafe Aurora"},
                          {"$unset": {"comercio.revisado": ""}})

    print(f"\n  Documentos restantes: {coleccion.count_documents({})}")

    print("""
  Advertencia:

    delete_many({}) con filtro vacio elimina TODA la coleccion sin
    pedir confirmacion. No hay equivalente de la transaccion que la
    sesion 2.5 uso para revertir.

    MongoDB si ofrece transacciones multidocumento desde la version 4,
    con requisitos de configuracion que se revisan en la sesion 3.2.
""")


# =====================================================================
# Bloque 6. Lo que MongoDB si garantiza
# =====================================================================

def bloque_6_garantias(base):
    titulo("Bloque 6: que si garantiza el motor")
    coleccion = base[COLECCION]

    from pymongo.errors import DuplicateKeyError

    # La unicidad de _id si se aplica.
    documento = coleccion.find_one()
    try:
        coleccion.insert_one({"_id": documento["_id"], "nota": "repetido"})
    except DuplicateKeyError as error:
        print(f"\n  Insercion con _id repetido rechazada: "
              f"{type(error).__name__}")

    print("""
  Lo que el motor garantiza sin configuracion adicional:

    _id unico dentro de la coleccion
    la escritura de UN documento es atomica: se aplica completa o no
    los tipos de BSON se conservan al leer

  Lo que NO garantiza:

    que un campo exista
    que un campo tenga un tipo determinado
    que un valor pertenezca a un dominio
    que una referencia a otra coleccion resuelva

  Los tres primeros se pueden recuperar con validacion de esquema, que
  se revisa en la sesion 3.2. El cuarto no tiene equivalente: no existen
  llaves foraneas.
""")


def main():
    cliente = MongoClient(uri_mongo())
    base = cliente[os.getenv("MONGO_DB", "pagos")]

    if base[COLECCION].count_documents({}) == 0:
        raise SystemExit(
            "La coleccion esta vacia. Ejecuta primero c3_s1_b3_carga.py")

    bloque_1_vocabulario(base)
    bloque_2_consulta(base)
    bloque_3_insercion(base)
    bloque_4_actualizacion(base)
    bloque_5_borrado(base)
    bloque_6_garantias(base)

    cliente.close()


if __name__ == "__main__":
    main()
