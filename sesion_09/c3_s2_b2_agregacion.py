"""
c3_s2_b2_agregacion.py
La canalizacion de agregacion de MongoDB.

La sesion 3.1 mostro find() para consultar documentos. La canalizacion
resuelve lo que find() no puede: agrupar, calcular, transformar la forma
del documento y combinar colecciones.

La idea es la misma de una tuberia de Unix: cada etapa recibe documentos,
los transforma y entrega el resultado a la siguiente.

Requisitos: coleccion operaciones cargada, .env presente
Ejecucion:  python c3_s2_b2_agregacion.py
"""

import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pymongo import MongoClient

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


def mostrar(resultado, limite=8):
    filas = list(resultado)
    for fila in filas[:limite]:
        print(f"    {fila}")
    if len(filas) > limite:
        print(f"    ... {len(filas) - limite} mas")
    print(f"    [{len(filas)} documentos]")
    return filas


# =====================================================================
# Bloque 1. Las etapas y su orden
# =====================================================================

def bloque_1_etapas(coleccion):
    titulo("Bloque 1: las etapas son una tuberia")

    print("""
  Etapa          Equivalente en SQL        Que hace
  -------------  ------------------------  --------------------------
  $match         WHERE                     filtra documentos
  $group         GROUP BY                  agrupa y acumula
  $sort          ORDER BY                  ordena
  $limit         LIMIT                     recorta
  $skip          OFFSET                    salta
  $project       la lista del SELECT       elige y calcula campos
  $unwind        no tiene equivalente      expande un arreglo a filas
  $lookup        LEFT JOIN                 combina con otra coleccion
  $count         COUNT(*)                  cuenta el resultado
  $facet         no tiene equivalente      varias tuberias a la vez
""")

    print("  Importe aprobado por comercio:")
    mostrar(coleccion.aggregate([
        {"$match": {"estatus": "APROBADA"}},
        {"$group": {"_id": "$comercio.nombre",
                    "operaciones": {"$sum": 1},
                    "importe": {"$sum": "$monto"}}},
        {"$sort": {"importe": -1}},
    ]))

    print("""
  A diferencia de SQL, el orden de las etapas lo decide quien escribe.
  SQL tiene un orden logico fijo, estudiado en la sesion 2.2. Aqui la
  tuberia se ejecuta en el orden en que se escribe.

  Consecuencia directa: $match va SIEMPRE lo mas temprano posible. Cada
  documento que se descarta ahi es trabajo que las etapas siguientes no
  hacen. Ponerlo al final produce el mismo resultado y recorre toda la
  coleccion.
""")


# =====================================================================
# Bloque 2. Acumuladores
# =====================================================================

def bloque_2_acumuladores(coleccion):
    titulo("Bloque 2: acumuladores")

    print("\n  Varias medidas en una sola pasada:")
    mostrar(coleccion.aggregate([
        {"$match": {"estatus": "APROBADA"}},
        {"$group": {
            "_id": "$comercio.ciudad",
            "operaciones": {"$sum": 1},
            "importe": {"$sum": "$monto"},
            "ticket_promedio": {"$avg": "$monto"},
            "minimo": {"$min": "$monto"},
            "maximo": {"$max": "$monto"},
        }},
        {"$sort": {"importe": -1}},
    ]))

    print("\n  $push y $addToSet construyen arreglos:")
    mostrar(coleccion.aggregate([
        {"$group": {"_id": "$comercio.ciudad",
                    "comercios": {"$addToSet": "$comercio.nombre"}}},
        {"$sort": {"_id": 1}},
    ]))

    print("""
  $push conserva los repetidos, $addToSet los elimina. El segundo
  equivale a un SELECT DISTINCT dentro del grupo.

  Advertencia de tamano: un documento de MongoDB no puede exceder 16 MB.
  Un $push sobre un grupo muy grande revienta ese limite. $addToSet
  sobre un campo de alta cardinalidad, tambien.
""")

    print("  Agrupacion por dos campos: el _id puede ser un documento.")
    mostrar(coleccion.aggregate([
        {"$match": {"estatus": "APROBADA"}},
        {"$group": {"_id": {"ciudad": "$comercio.ciudad",
                            "captura": "$metodo_captura"},
                    "operaciones": {"$sum": 1}}},
        {"$sort": {"operaciones": -1}},
        {"$limit": 5},
    ]))


# =====================================================================
# Bloque 3. $project y campos calculados
# =====================================================================

def bloque_3_project(coleccion):
    titulo("Bloque 3: $project transforma la forma del documento")

    print("\n  Aplanar el documento y calcular:")
    mostrar(coleccion.aggregate([
        {"$match": {"estatus": "APROBADA"}},
        {"$project": {
            "_id": 1,
            "comercio": "$comercio.nombre",
            "ciudad": "$comercio.ciudad",
            "monto": 1,
            "con_iva": {"$multiply": ["$monto", 1.16]},
            "categoria_monto": {
                "$cond": [{"$gt": ["$monto", 10000]}, "alto", "normal"]
            },
        }},
        {"$sort": {"monto": -1}},
        {"$limit": 5},
    ]))

    print("""
  $project hace tres cosas a la vez:

    incluye o excluye campos, como la lista del SELECT
    renombra, con "destino": "$origen"
    calcula, con operadores de expresion

  $addFields es su variante conservadora: agrega campos sin quitar los
  existentes. Conviene cuando solo se quiere enriquecer el documento.
""")

    print("  $addFields conserva todo lo demas:")
    documento = list(coleccion.aggregate([
        {"$limit": 1},
        {"$addFields": {"revisado": True}},
    ]))[0]
    print(f"    campos del documento: {len(documento)}")
    print(f"    incluye 'revisado': {'revisado' in documento}")


# =====================================================================
# Bloque 4. $unwind
# =====================================================================

def bloque_4_unwind(coleccion):
    titulo("Bloque 4: $unwind, la etapa sin equivalente en SQL")

    print("""
  Las senales de riesgo viven en un arreglo dentro del documento:

    autorizacion.riesgo.senales = ["geo_inusual", "monto_atipico"]

  Para contar cuantas veces aparece cada senal hay que convertir cada
  elemento del arreglo en un documento propio. Eso hace $unwind.
""")

    print("  Sin $unwind, el arreglo se agrupa como un todo:")
    mostrar(coleccion.aggregate([
        {"$match": {"autorizacion.riesgo.senales": {"$exists": True}}},
        {"$group": {"_id": "$autorizacion.riesgo.senales",
                    "veces": {"$sum": 1}}},
        {"$sort": {"veces": -1}},
        {"$limit": 4},
    ]), limite=4)

    print("\n  Con $unwind, una fila por senal:")
    mostrar(coleccion.aggregate([
        {"$match": {"autorizacion.riesgo.senales": {"$exists": True}}},
        {"$unwind": "$autorizacion.riesgo.senales"},
        {"$group": {"_id": "$autorizacion.riesgo.senales",
                    "veces": {"$sum": 1}}},
        {"$sort": {"veces": -1}},
    ]))

    print("""
  Dos advertencias sobre $unwind:

    Multiplica documentos. Una operacion con tres senales produce tres
    documentos. Cualquier conteo posterior cuenta operaciones repetidas,
    no operaciones distintas.

    Descarta los documentos cuyo arreglo este vacio o no exista, salvo
    que se declare preserveNullAndEmptyArrays.
""")

    total = coleccion.count_documents({})
    expandidos = len(list(coleccion.aggregate([
        {"$unwind": "$autorizacion.riesgo.senales"},
    ])))
    conservando = len(list(coleccion.aggregate([
        {"$unwind": {"path": "$autorizacion.riesgo.senales",
                     "preserveNullAndEmptyArrays": True}},
    ])))
    print(f"  Documentos originales:          {total}")
    print(f"  Tras $unwind:                   {expandidos}")
    print(f"  Tras $unwind conservando vacios: {conservando}")


# =====================================================================
# Bloque 5. $lookup
# =====================================================================

def bloque_5_lookup(base):
    titulo("Bloque 5: $lookup, la combinacion que si existe")

    coleccion = base[COLECCION]

    # Se construye una coleccion de catalogo para ilustrar la etapa.
    catalogo = base["catalogo_categorias"]
    catalogo.drop()
    catalogo.insert_many([
        {"_id": "Supermercado", "giro": 5411, "riesgo_base": 1},
        {"_id": "Farmacia", "giro": 5912, "riesgo_base": 1},
        {"_id": "Restaurante", "giro": 5812, "riesgo_base": 2},
        {"_id": "Ropa", "giro": 5651, "riesgo_base": 3},
        {"_id": "Combustible", "giro": 5541, "riesgo_base": 2},
        {"_id": "Electronica", "giro": 5732, "riesgo_base": 4},
        {"_id": "Viajes", "giro": 4722, "riesgo_base": 5},
    ])
    print(f"\n  Coleccion de catalogo creada: "
          f"{catalogo.count_documents({})} categorias")

    print("\n  Combinacion con el catalogo:")
    mostrar(coleccion.aggregate([
        {"$match": {"estatus": "APROBADA"}},
        {"$group": {"_id": "$comercio.categoria",
                    "operaciones": {"$sum": 1},
                    "importe": {"$sum": "$monto"}}},
        {"$lookup": {
            "from": "catalogo_categorias",
            "localField": "_id",
            "foreignField": "_id",
            "as": "catalogo",
        }},
        {"$unwind": "$catalogo"},
        {"$project": {
            "operaciones": 1,
            "importe": 1,
            "giro": "$catalogo.giro",
            "riesgo_base": "$catalogo.riesgo_base",
        }},
        {"$sort": {"importe": -1}},
    ]))

    print("""
  Diferencias importantes frente a un JOIN de SQL:

    $lookup devuelve un ARREGLO con las coincidencias, no filas
    combinadas. Por eso casi siempre va seguido de $unwind.

    Se comporta como LEFT JOIN: sin coincidencia, el arreglo queda
    vacio.

    No hay llaves foraneas que garanticen que la referencia resuelve.
    Un documento puede apuntar a una categoria que no existe y nada lo
    impide. Eso se vio en la sesion 3.1.

    El costo es considerable. Si el patron de acceso habitual exige
    $lookup en cada consulta, suele ser senal de que el modelo deberia
    incorporar ese dato en el documento.

  Criterio: $lookup para catalogos pequenos y consultas ocasionales.
  Para lo que se consulta siempre, incorporar.
""")


# =====================================================================
# Bloque 6. $facet
# =====================================================================

def bloque_6_facet(coleccion):
    titulo("Bloque 6: $facet, varias tuberias en un solo recorrido")

    resultado = list(coleccion.aggregate([
        {"$match": {"estatus": "APROBADA"}},
        {"$facet": {
            "por_ciudad": [
                {"$group": {"_id": "$comercio.ciudad",
                            "importe": {"$sum": "$monto"}}},
                {"$sort": {"importe": -1}},
                {"$limit": 3},
            ],
            "por_captura": [
                {"$group": {"_id": "$metodo_captura",
                            "operaciones": {"$sum": 1}}},
                {"$sort": {"operaciones": -1}},
            ],
            "totales": [
                {"$group": {"_id": None,
                            "operaciones": {"$sum": 1},
                            "importe": {"$sum": "$monto"}}},
            ],
        }},
    ]))[0]

    for nombre, filas in resultado.items():
        print(f"\n  {nombre}:")
        for fila in filas:
            print(f"    {fila}")

    print("""
  $facet ejecuta varias tuberias sobre el MISMO conjunto de entrada y
  devuelve un solo documento con todos los resultados.

  Sirve para armar un tablero completo en una sola ida al servidor, en
  lugar de tres consultas independientes.

  Limitacion: cada tuberia interna trabaja sobre lo que entro a $facet,
  de modo que el $match que antecede aplica a todas por igual.
""")


# =====================================================================
# Bloque 7. El orden importa
# =====================================================================

def bloque_7_orden(coleccion):
    titulo("Bloque 7: por que $match va primero")

    import time

    def medir(tuberia, repeticiones=3):
        tiempos = []
        for _ in range(repeticiones):
            inicio = time.perf_counter()
            list(coleccion.aggregate(tuberia))
            tiempos.append(time.perf_counter() - inicio)
        return min(tiempos) * 1000

    temprano = [
        {"$match": {"estatus": "APROBADA"}},
        {"$unwind": {"path": "$autorizacion.riesgo.senales",
                     "preserveNullAndEmptyArrays": True}},
        {"$group": {"_id": "$comercio.nombre", "n": {"$sum": 1}}},
    ]
    tardio = [
        {"$unwind": {"path": "$autorizacion.riesgo.senales",
                     "preserveNullAndEmptyArrays": True}},
        {"$match": {"estatus": "APROBADA"}},
        {"$group": {"_id": "$comercio.nombre", "n": {"$sum": 1}}},
    ]

    print(f"\n  $match antes de $unwind: {medir(temprano):7.1f} ms")
    print(f"  $match despues:          {medir(tardio):7.1f} ms")

    print("""
  Advertencia sobre la medicion: se reporta el minimo de tres
  repeticiones, conforme al criterio de la sesion 2.5. Con cinco mil
  documentos la diferencia es modesta.

  El punto no es el numero sino el principio: la etapa que reduce el
  conjunto va primero. Con volumen alto, la diferencia deja de ser
  modesta.

  MongoDB reordena algunas etapas por su cuenta, igual que el
  planificador de PostgreSQL. No conviene depender de eso: escribir la
  tuberia en el orden correcto es gratis y siempre funciona.
""")


def main():
    cliente = MongoClient(uri_mongo(), serverSelectionTimeoutMS=5000)
    base = cliente[os.getenv("MONGO_DB", "pagos")]
    coleccion = base[COLECCION]

    if coleccion.count_documents({}) == 0:
        raise SystemExit(
            "La coleccion esta vacia. Ejecuta primero c3_s1_b3_carga.py")

    bloque_1_etapas(coleccion)
    bloque_2_acumuladores(coleccion)
    bloque_3_project(coleccion)
    bloque_4_unwind(coleccion)
    bloque_5_lookup(base)
    bloque_6_facet(coleccion)
    bloque_7_orden(coleccion)

    cliente.close()


if __name__ == "__main__":
    main()
