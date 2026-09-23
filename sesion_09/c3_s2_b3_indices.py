"""
c3_s2_b3_indices.py
Indices y validacion de esquema en MongoDB.

Dos temas que responden a lo que la sesion 3.1 dejo abierto:

    Si la coleccion no tiene esquema, como se consulta con eficiencia.
    Si el motor no valida nada, como se recupera algo de control.

Requisitos: coleccion operaciones cargada, .env presente
Ejecucion:  python c3_s2_b3_indices.py
"""

import os
import time
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import OperationFailure, WriteError

load_dotenv(override=True)
COLECCION = "operaciones"


def uri_mongo():
    usuario = quote_plus(os.getenv("MONGO_USER", ""))
    clave = quote_plus(os.getenv("MONGO_PASSWORD", ""))
    return (f"mongodb://{usuario}:{clave}"
            f"@{os.getenv('MONGO_HOST', 'localhost')}:"
            f"{os.getenv('MONGO_PORT', '27017')}/?authSource=admin")


def titulo(texto):
    print("\n" + "=" * 70 + f"\n{texto}\n" + "=" * 70)


def plan(coleccion, filtro):
    """Devuelve el plan de una consulta, con estadisticas de ejecucion.

    Detalle importante: cursor.explain() de PyMongo usa la verbosidad
    predeterminada, que NO incluye executionStats. Sin ese bloque no hay
    documentos examinados ni tiempo real, que son justo las cifras que
    sirven para decidir.

    Por eso se invoca el comando explain de forma explicita con
    verbosity="executionStats".
    """
    resultado = coleccion.database.command(
        "explain",
        {"find": coleccion.name, "filter": filtro},
        verbosity="executionStats",
    )
    return resumen_plan(resultado)


def resumen_plan(explicacion):
    """Extrae del plan lo que interesa: etapas y documentos leidos.

    El plan completo es extenso. Estas cifras son las que se usan para
    decidir.
    """
    planificador = explicacion.get("queryPlanner", {})
    ganador = planificador.get("winningPlan")

    if not ganador:
        # Algunas versiones y algunos servidores compatibles devuelven
        # otra estructura. En ese caso se reportan las claves recibidas,
        # para que el participante sepa donde buscar.
        return {"etapas": "estructura no reconocida",
                "claves_del_plan": sorted(explicacion.keys())}

    etapas = []
    actual = ganador
    while isinstance(actual, dict):
        if "stage" in actual:
            etapas.append(actual["stage"])
        actual = actual.get("inputStage")

    ejecucion = explicacion.get("executionStats", {})
    return {
        "etapas": " -> ".join(etapas) if etapas else "sin etapas",
        "devueltos": ejecucion.get("nReturned"),
        "examinados": ejecucion.get("totalDocsExamined"),
        "claves_leidas": ejecucion.get("totalKeysExamined"),
        "ms": ejecucion.get("executionTimeMillis"),
    }


# =====================================================================
# Bloque 1. El indice que siempre existe
# =====================================================================

def bloque_1_indice_de_id(coleccion):
    titulo("Bloque 1: el indice de _id")

    print("\n  Indices actuales:")
    for nombre, definicion in coleccion.index_information().items():
        print(f"    {nombre:<28} {definicion.get('key')}")

    print("""
  Toda coleccion tiene un indice unico sobre _id. Se crea sola, no se
  puede eliminar, y es la razon de que buscar por _id sea inmediato.

  La sesion 3.1 aprovecho esto al usar el identificador de la
  transaccion como _id: evito un indice adicional y volvio la carga
  idempotente.
""")


# =====================================================================
# Bloque 2. Crear indices y medir
# =====================================================================

def bloque_2_crear_y_medir(coleccion):
    titulo("Bloque 2: el efecto de un indice")

    # Se eliminan los indices del ejercicio, si quedaron de una corrida
    # anterior. El de _id no se puede eliminar.
    for nombre in list(coleccion.index_information()):
        if nombre != "_id_":
            coleccion.drop_index(nombre)

    filtro = {"comercio.ciudad": "Merida", "estatus": "APROBADA"}

    print("\n  Sin indice:")
    print(f"    {plan(coleccion, filtro)}")

    coleccion.create_index([("comercio.ciudad", ASCENDING),
                            ("estatus", ASCENDING)],
                           name="idx_ciudad_estatus")
    print("\n  Con indice compuesto sobre (comercio.ciudad, estatus):")
    print(f"    {plan(coleccion, filtro)}")

    print("""
  Las cifras que importan del plan:

    COLLSCAN         recorrio la coleccion completa
    IXSCAN           uso un indice
    FETCH            fue al documento tras consultar el indice
    PROJECTION_COVERED  se resolvio solo con el indice

    totalDocsExamined  documentos leidos
    nReturned          documentos devueltos

  Cuando examinados es mucho mayor que devueltos, hay trabajo
  desperdiciado. Es el mismo diagnostico de la sesion 2.5, con otros
  nombres.

  El orden de las columnas sigue la misma regla que en PostgreSQL:
  igualdad primero, rango al final.
""")


# =====================================================================
# Bloque 3. Indices sobre campos anidados y arreglos
# =====================================================================

def bloque_3_anidados_y_arreglos(coleccion):
    titulo("Bloque 3: campos anidados y arreglos")

    coleccion.create_index("autorizacion.emisor.nombre", name="idx_emisor")
    print("\n  Indice sobre un campo anidado de tres niveles:")
    print(f"    {plan(coleccion, {'autorizacion.emisor.nombre': 'BANORTE'})}")

    coleccion.create_index("autorizacion.riesgo.senales", name="idx_senales")
    print("\n  Indice sobre un arreglo (indice multiclave):")
    print(f"    {plan(coleccion, {'autorizacion.riesgo.senales': 'geo_inusual'})}")

    print("""
  Dos capacidades que PostgreSQL resuelve de otra forma:

    El indice sobre campo anidado usa la misma notacion de punto de la
    consulta. En PostgreSQL haria falta un indice de expresion sobre
    JSONB, como en la sesion 2.4.

    El indice sobre un arreglo se llama multiclave: MongoDB crea una
    entrada por cada elemento. Buscar un valor dentro del arreglo usa
    el indice de forma directa.

  Limitacion del indice multiclave: un indice compuesto puede incluir a
  lo mas UN campo de tipo arreglo. Con dos, MongoDB rechaza la
  creacion.
""")


# =====================================================================
# Bloque 4. Indices parciales y de texto
# =====================================================================

def bloque_4_otros_indices(coleccion):
    titulo("Bloque 4: indices parciales y unicos")

    try:
        coleccion.create_index(
            [("monto", DESCENDING)],
            name="idx_montos_altos",
            partialFilterExpression={"monto": {"$gt": 10000}},
        )
        print("\n  Indice parcial creado sobre los montos mayores a 10000.")
        print(f"    {plan(coleccion, {'monto': {'$gt': 20000}})}")
    except OperationFailure as error:
        print(f"\n  El servidor no admite indices parciales: "
              f"{str(error)[:60]}")

    print("""
  El indice parcial solo indexa los documentos que cumplen la
  condicion. Ocupa menos y se mantiene mas barato.

  Requisito: la consulta debe garantizar que solo busca dentro de ese
  subconjunto. Una consulta sobre monto mayor a 5000 NO puede usarlo,
  porque incluiria documentos que el indice no contiene.

  Es el mismo mecanismo del indice parcial de PostgreSQL, visto en la
  sesion 2.5.
""")

    print("  Indice unico: la garantia que si se puede declarar.")
    prueba = coleccion.database["prueba_unico"]
    prueba.drop()
    prueba.create_index("folio", unique=True)
    prueba.insert_one({"folio": "A-001"})
    try:
        prueba.insert_one({"folio": "A-001"})
    except Exception as error:
        print(f"    Segundo insert rechazado: {type(error).__name__}")
    prueba.drop()

    print("""
  El indice unico es la unica forma de exigir unicidad sobre un campo
  que no sea _id. Es la contraparte de UNIQUE en SQL, y se declara como
  indice en lugar de como restriccion.
""")


# =====================================================================
# Bloque 5. Validacion de esquema
# =====================================================================

def bloque_5_validacion(base):
    titulo("Bloque 5: recuperar el control sobre la estructura")

    print("""
  La sesion 3.1 mostro que MongoDB acepta un monto que sea texto, y que
  $sum lo ignora en silencio.

  La validacion de esquema recupera parte de ese control: se declara
  que forma deben tener los documentos y el motor rechaza los que no la
  cumplen.
""")

    nombre = "operaciones_validadas"
    base.drop_collection(nombre)

    esquema = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "monto", "estatus", "comercio"],
            "properties": {
                "monto": {
                    "bsonType": ["double", "int", "long", "decimal"],
                    "minimum": 0,
                    "description": "Debe ser numerico y no negativo",
                },
                "estatus": {
                    "enum": ["APROBADA", "RECHAZADA", "REVERSADA"],
                    "description": "Debe pertenecer al dominio declarado",
                },
                "comercio": {
                    "bsonType": "object",
                    "required": ["nombre"],
                    "properties": {
                        "nombre": {"bsonType": "string"},
                    },
                },
            },
        }
    }

    base.create_collection(nombre, validator=esquema,
                           validationLevel="strict",
                           validationAction="error")
    validada = base[nombre]
    print(f"  Coleccion {nombre} creada con validador.\n")

    casos = [
        ("Documento correcto",
         {"_id": "OK1", "monto": 100.0, "estatus": "APROBADA",
          "comercio": {"nombre": "Cafe Aurora"}}),
        ("Monto de tipo texto",
         {"_id": "E1", "monto": "mil pesos", "estatus": "APROBADA",
          "comercio": {"nombre": "Cafe Aurora"}}),
        ("Estatus fuera del dominio",
         {"_id": "E2", "monto": 100.0, "estatus": "PENDIENTE",
          "comercio": {"nombre": "Cafe Aurora"}}),
        ("Monto negativo",
         {"_id": "E3", "monto": -50.0, "estatus": "APROBADA",
          "comercio": {"nombre": "Cafe Aurora"}}),
        ("Falta un campo obligatorio",
         {"_id": "E4", "monto": 100.0, "estatus": "APROBADA"}),
        ("Comercio sin nombre",
         {"_id": "E5", "monto": 100.0, "estatus": "APROBADA",
          "comercio": {"ciudad": "Merida"}}),
    ]

    for etiqueta, documento in casos:
        try:
            validada.insert_one(documento)
            print(f"    ACEPTADO   {etiqueta}")
        except (WriteError, OperationFailure):
            print(f"    RECHAZADO  {etiqueta}")

    print(f"\n  Documentos en la coleccion: {validada.count_documents({})}")

    print("""
  Lo que la validacion si recupera:

    tipos de dato
    campos obligatorios
    dominios de valores, con enum
    rangos numericos
    estructura de subdocumentos

  Lo que NO recupera:

    referencias entre colecciones. No existen llaves foraneas y nada
    impide apuntar a un documento que no existe.

  Dos parametros que conviene conocer:

    validationLevel "strict" valida toda escritura.
    validationLevel "moderate" valida las inserciones y solo las
      actualizaciones de documentos que ya cumplian. Sirve para
      introducir validacion en una coleccion con datos historicos
      irregulares.

    validationAction "error" rechaza.
    validationAction "warn" registra en la bitacora y deja pasar. Util
      para medir cuanto incumpliria antes de activar el rechazo.

  Diferencia de fondo con PostgreSQL: aqui la validacion es OPCIONAL y
  se agrega despues. En el modelo relacional es obligatoria desde que
  se declara la tabla. Esa diferencia es el argumento central de la
  sesion 3.3.
""")

    base.drop_collection(nombre)


def main():
    cliente = MongoClient(uri_mongo(), serverSelectionTimeoutMS=5000)
    base = cliente[os.getenv("MONGO_DB", "pagos")]
    coleccion = base[COLECCION]

    if coleccion.count_documents({}) == 0:
        raise SystemExit(
            "La coleccion esta vacia. Ejecuta primero c3_s1_b3_carga.py")

    bloque_1_indice_de_id(coleccion)
    bloque_2_crear_y_medir(coleccion)
    bloque_3_anidados_y_arreglos(coleccion)
    bloque_4_otros_indices(coleccion)
    bloque_5_validacion(base)

    cliente.close()


if __name__ == "__main__":
    main()
