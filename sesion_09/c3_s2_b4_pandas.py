"""
c3_s2_b4_pandas.py
Del documento al dataframe.

La sesion 2.2 llevo resultados de PostgreSQL hacia pandas y Polars, y
encontro que el tipo NUMERIC no sobrevive el cruce. Aqui se hace lo
mismo desde MongoDB, con un problema distinto: el documento es anidado
y el dataframe es plano.

Requisitos: coleccion operaciones cargada, .env presente
    pip install pymongo pandas
Ejecucion:  python c3_s2_b4_pandas.py
"""

import os
from urllib.parse import quote_plus

import pandas as pd
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


# =====================================================================
# Bloque 1. El documento anidado no cabe en una tabla
# =====================================================================

def bloque_1_anidamiento(coleccion):
    titulo("Bloque 1: el documento es anidado, el dataframe es plano")

    df = pd.DataFrame(list(coleccion.find().limit(100)))
    print(f"\n  Forma: {df.shape}")
    print(f"  Columnas: {list(df.columns)}")
    print(f"\n  El contenido de 'comercio' en la primera fila:")
    print(f"    {df['comercio'][0]}")
    print(f"    tipo: {type(df['comercio'][0]).__name__}")

    print("""
  pandas acepta el documento, pero deja los subdocumentos como
  diccionarios dentro de la celda. Esa columna no sirve para agrupar,
  filtrar ni graficar.

  Tres formas de resolverlo, de menos a mas recomendable.
""")


# =====================================================================
# Bloque 2. Aplanar en el cliente
# =====================================================================

def bloque_2_aplanar_cliente(coleccion):
    titulo("Bloque 2: aplanar en el cliente con json_normalize")

    documentos = list(coleccion.find().limit(500))
    df = pd.json_normalize(documentos)

    print(f"\n  Forma: {df.shape}")
    print(f"  Algunas columnas generadas:")
    for columna in list(df.columns)[:14]:
        print(f"    {columna}")

    print("""
  json_normalize convierte cada nivel de anidamiento en una columna con
  nombre compuesto por puntos.

  Dos problemas:

    Genera una columna por cada campo que exista en ALGUN documento. Con
    esquema variable, el resultado tiene muchas columnas y muchos nulos.
    Es el mismo fenomeno de la sesion 2.4, ahora en el dataframe.

    Los arreglos no se aplanan: quedan como listas dentro de la celda.
""")

    columnas_con_nulos = (df.isna().mean() > 0.5).sum()
    print(f"  Columnas con mas de la mitad de valores nulos: "
          f"{columnas_con_nulos} de {df.shape[1]}")


# =====================================================================
# Bloque 3. Aplanar en el servidor
# =====================================================================

def bloque_3_aplanar_servidor(coleccion):
    titulo("Bloque 3: aplanar en el servidor con $project")

    tuberia = [
        {"$match": {"estatus": "APROBADA"}},
        {"$project": {
            "_id": 1,
            "fecha_hora": 1,
            "monto": 1,
            "metodo_captura": 1,
            "comercio": "$comercio.nombre",
            "ciudad": "$comercio.ciudad",
            "categoria": "$comercio.categoria",
            "marca": "$tarjeta.marca",
            "emisor": "$autorizacion.emisor.nombre",
            "puntaje_riesgo": "$autorizacion.riesgo.puntaje",
        }},
    ]
    df = pd.DataFrame(list(coleccion.aggregate(tuberia)))

    print(f"\n  Forma: {df.shape}")
    print(f"  Columnas: {list(df.columns)}")
    print(f"\n{df.head(3).to_string(index=False)}")

    print("""
  El documento llega ya plano y con los campos que hacen falta. Es la
  forma recomendable por tres razones:

    viaja menos por la red
    el dataframe nace con la forma correcta, sin transformacion posterior
    la lista de columnas queda declarada de forma explicita, de modo que
      un documento con campos extra no cambia el resultado

  Es el mismo criterio de la sesion 2.2: mover el trabajo hacia donde
  viven los datos.
""")

    print("  Tipos que dedujo pandas:")
    print("   ", df.dtypes.to_dict())


# =====================================================================
# Bloque 4. Agregar en el servidor
# =====================================================================

def bloque_4_agregar_servidor(coleccion):
    titulo("Bloque 4: traer el resultado, no los datos")

    df = pd.DataFrame(list(coleccion.aggregate([
        {"$match": {"estatus": "APROBADA"}},
        {"$group": {
            "_id": {"ciudad": "$comercio.ciudad",
                    "captura": "$metodo_captura"},
            "operaciones": {"$sum": 1},
            "importe": {"$sum": "$monto"},
            "ticket": {"$avg": "$monto"},
        }},
    ])))

    # El _id compuesto llega como diccionario y hay que expandirlo.
    df = pd.concat([pd.json_normalize(df["_id"]), df.drop(columns=["_id"])],
                   axis=1)
    df = df.sort_values("importe", ascending=False)

    print(f"\n  Forma: {df.shape}")
    print(f"\n{df.head(8).to_string(index=False)}")

    print("""
  Cuando el _id del grupo es compuesto, llega como un diccionario. La
  forma directa de expandirlo es json_normalize sobre esa columna.

  Alternativa que evita el paso: agregar un $project despues del $group
  que suba los campos del _id al primer nivel.
""")

    print("  Con $project posterior, el dataframe nace plano:")
    df2 = pd.DataFrame(list(coleccion.aggregate([
        {"$match": {"estatus": "APROBADA"}},
        {"$group": {"_id": {"ciudad": "$comercio.ciudad",
                            "captura": "$metodo_captura"},
                    "operaciones": {"$sum": 1}}},
        {"$project": {"_id": 0,
                      "ciudad": "$_id.ciudad",
                      "captura": "$_id.captura",
                      "operaciones": 1}},
    ])))
    print(f"    columnas: {list(df2.columns)}")


# =====================================================================
# Bloque 5. El tipo del monto, otra vez
# =====================================================================

def bloque_5_tipos(coleccion):
    titulo("Bloque 5: el tipo del monto, tercera vez")

    resultado = list(coleccion.aggregate([
        {"$match": {"estatus": "APROBADA"}},
        {"$group": {"_id": None, "importe": {"$sum": "$monto"}}},
    ]))
    suma_servidor = resultado[0]["importe"]

    df = pd.DataFrame(list(coleccion.find({"estatus": "APROBADA"},
                                          {"monto": 1})))
    suma_pandas = df["monto"].sum()

    print(f"\n  Suma calculada en MongoDB : {suma_servidor!r}")
    print(f"  Suma calculada en pandas  : {suma_pandas!r}")
    print(f"  Tipo de la columna        : {df['monto'].dtype}")

    print("""
  Recorrido del mismo dato a lo largo del curso:

    Sesion 2.1  se declaro NUMERIC(12,2) para tener aritmetica exacta
    Sesion 2.2  pandas lo convirtio a float64 al leer de PostgreSQL
    Sesion 3.1  la carga a MongoDB lo almaceno como float de BSON
    Sesion 3.2  aqui ya no hay nada que perder: nacio flotante

  Conclusion aplicable: la decision sobre el tipo se toma UNA vez, en el
  almacenamiento, y todo lo que viene despues la hereda. Recuperarla mas
  adelante no es posible.

  Si el importe debe ser exacto, se almacena como Decimal128 en BSON y
  se maneja con Decimal en Python.
""")


def main():
    cliente = MongoClient(uri_mongo(), serverSelectionTimeoutMS=5000)
    coleccion = cliente[os.getenv("MONGO_DB", "pagos")][COLECCION]

    if coleccion.count_documents({}) == 0:
        raise SystemExit(
            "La coleccion esta vacia. Ejecuta primero c3_s1_b3_carga.py")

    bloque_1_anidamiento(coleccion)
    bloque_2_aplanar_cliente(coleccion)
    bloque_3_aplanar_servidor(coleccion)
    bloque_4_agregar_servidor(coleccion)
    bloque_5_tipos(coleccion)

    cliente.close()


if __name__ == "__main__":
    main()
