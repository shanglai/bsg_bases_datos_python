"""
c3_s2_b1_verifica.py
Comprueba que el servidor de MongoDB admite todo lo que usa la sesion.

La sesion 3.2 usa capacidades que no todos los servidores compatibles
con el protocolo de MongoDB implementan: etapas de agregacion, indices
parciales, validacion de esquema y la estructura del plan de ejecucion.

Este script las prueba una por una y reporta cuales estan disponibles.
Se ejecuta antes de la sesion, sobre una coleccion temporal que se
elimina al terminar.

Requisitos: .env con las variables de MongoDB
Ejecucion:  python c3_s2_b1_verifica.py
"""

import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(override=True)
PRUEBA = "verificacion_temporal"


def uri_mongo():
    usuario = quote_plus(os.getenv("MONGO_USER", ""))
    clave = quote_plus(os.getenv("MONGO_PASSWORD", ""))
    return (f"mongodb://{usuario}:{clave}"
            f"@{os.getenv('MONGO_HOST', 'localhost')}:"
            f"{os.getenv('MONGO_PORT', '27017')}/?authSource=admin")


def probar(etiqueta, funcion):
    try:
        funcion()
        print(f"  OK   {etiqueta}")
        return True
    except Exception as error:
        mensaje = str(error).split("full error")[0][:70]
        print(f"  NO   {etiqueta:<34} {mensaje}")
        return False


def main():
    cliente = MongoClient(uri_mongo(), serverSelectionTimeoutMS=5000)
    base = cliente[os.getenv("MONGO_DB", "pagos")]

    print(f"Servidor: {cliente.server_info()['version']}\n")

    base.drop_collection(PRUEBA)
    coleccion = base[PRUEBA]
    coleccion.insert_many([
        {"_id": 1, "g": "a", "v": 10.0, "tags": ["x", "y"], "sub": {"n": 1}},
        {"_id": 2, "g": "a", "v": 20.0, "tags": ["y"], "sub": {"n": 2}},
        {"_id": 3, "g": "b", "v": 30.0, "tags": ["x"], "sub": {"n": 3}},
    ])

    print("Etapas y acumuladores de agregacion")
    etapas = {
        "$group con varios acumuladores":
            [{"$group": {"_id": "$g", "s": {"$sum": "$v"}, "n": {"$sum": 1}}}],
        "$avg, $min, $max":
            [{"$group": {"_id": None, "a": {"$avg": "$v"},
                         "mi": {"$min": "$v"}, "ma": {"$max": "$v"}}}],
        "$push y $addToSet":
            [{"$group": {"_id": "$g", "p": {"$push": "$v"},
                         "a": {"$addToSet": "$g"}}}],
        "$unwind":
            [{"$unwind": "$tags"}],
        "$unwind con preserveNullAndEmptyArrays":
            [{"$unwind": {"path": "$tags", "preserveNullAndEmptyArrays": True}}],
        "$project con expresiones":
            [{"$project": {"d": {"$multiply": ["$v", 2]},
                           "c": {"$cond": [{"$gt": ["$v", 15]}, "alto", "bajo"]}}}],
        "$addFields":
            [{"$addFields": {"x": 1}}],
        "$lookup":
            [{"$lookup": {"from": PRUEBA, "localField": "g",
                          "foreignField": "g", "as": "r"}}],
        "$facet":
            [{"$facet": {"a": [{"$count": "c"}]}}],
        "$count":
            [{"$count": "total"}],
    }
    disponibles = sum(
        probar(nombre, lambda t=tuberia: list(coleccion.aggregate(t)))
        for nombre, tuberia in etapas.items()
    )

    print("\nIndices")
    indices = 0
    indices += probar("create_index simple",
                      lambda: coleccion.create_index("g", name="i1"))
    indices += probar("create_index compuesto",
                      lambda: coleccion.create_index([("g", 1), ("v", -1)],
                                                     name="i2"))
    indices += probar("create_index sobre campo anidado",
                      lambda: coleccion.create_index("sub.n", name="i3"))
    indices += probar("create_index multiclave, sobre arreglo",
                      lambda: coleccion.create_index("tags", name="i4"))
    indices += probar("create_index unico",
                      lambda: coleccion.create_index("v", unique=True,
                                                     name="i5"))
    indices += probar("create_index parcial",
                      lambda: coleccion.create_index(
                          "v", name="i6",
                          partialFilterExpression={"v": {"$gt": 15}}))
    indices += probar("index_information",
                      lambda: coleccion.index_information())

    print("\nPlan de ejecucion")

    def explain_con_estructura():
        resultado = base.command("explain", {"find": PRUEBA, "filter": {"g": "a"}},
                                 verbosity="executionStats")
        if "queryPlanner" not in resultado:
            raise RuntimeError("la respuesta no trae queryPlanner")
        if "winningPlan" not in resultado["queryPlanner"]:
            raise RuntimeError("queryPlanner no trae winningPlan")
        if "executionStats" not in resultado:
            raise RuntimeError("la respuesta no trae executionStats")

    planes = probar("explain con winningPlan y executionStats",
                    explain_con_estructura)

    print("\nValidacion de esquema")

    def crear_validada():
        base.drop_collection("verificacion_validada")
        base.create_collection(
            "verificacion_validada",
            validator={"$jsonSchema": {
                "bsonType": "object",
                "required": ["v"],
                "properties": {"v": {"bsonType": ["double", "int"]}},
            }},
            validationLevel="strict", validationAction="error")

    def rechaza_invalido():
        try:
            base["verificacion_validada"].insert_one({"v": "texto"})
        except Exception:
            return
        raise RuntimeError("el documento invalido fue aceptado")

    validacion = probar("create_collection con $jsonSchema", crear_validada)
    if validacion:
        validacion = probar("el validador rechaza un tipo incorrecto",
                            rechaza_invalido)

    base.drop_collection(PRUEBA)
    base.drop_collection("verificacion_validada")

    print("\n" + "=" * 60)
    total = len(etapas)
    print(f"Etapas de agregacion: {disponibles} de {total}")
    print(f"Indices:              {indices} de 7")
    print(f"Plan de ejecucion:    {'disponible' if planes else 'NO disponible'}")
    print(f"Validacion:           {'disponible' if validacion else 'NO disponible'}")

    if disponibles == total and indices == 7 and planes and validacion:
        print("\nEl entorno admite todo lo que usa la sesion 3.2.")
    else:
        print("\nFaltan capacidades. Con la imagen oficial mongo:7 deberian")
        print("estar todas. Si alguna falla, revisar la version del servidor.")

    cliente.close()


if __name__ == "__main__":
    main()
