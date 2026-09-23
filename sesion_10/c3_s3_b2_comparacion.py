"""
c3_s3_b2_comparacion.py
La misma pregunta, en los dos motores.

Todo el curso llevo los mismos datos por dos caminos. Esta sesion los
pone lado a lado sobre las mismas cinco preguntas, para que la eleccion
deje de ser una impresion y pase a ser una comparacion.

Regla de la sesion: cada pregunta se resuelve en ambos motores, se
verifica que el resultado coincida, y despues se compara el esfuerzo.

Requisitos: PostgreSQL con la columna autorizacion, MongoDB con la
    coleccion operaciones, archivo .env con ambos motores
Ejecucion:  python c3_s3_b2_comparacion.py
"""

import os
import time
from urllib.parse import quote_plus

import psycopg
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(override=True)
COLECCION = "operaciones"


def cadena_postgres():
    return (f"host={os.getenv('PGHOST', 'localhost')} "
            f"port={os.getenv('PGPORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DB')} "
            f"user={os.getenv('POSTGRES_USER')} "
            f"password={os.getenv('POSTGRES_PASSWORD')}")


def uri_mongo():
    usuario = quote_plus(os.getenv("MONGO_USER", ""))
    clave = quote_plus(os.getenv("MONGO_PASSWORD", ""))
    return (f"mongodb://{usuario}:{clave}"
            f"@{os.getenv('MONGO_HOST', 'localhost')}:"
            f"{os.getenv('MONGO_PORT', '27017')}/?authSource=admin")


def titulo(texto):
    print("\n" + "=" * 72 + f"\n{texto}\n" + "=" * 72)


def comparar(etiqueta, resultado_sql, resultado_mongo, tolerancia=0.01):
    """Verifica que ambos motores devuelvan lo mismo.

    La comparacion se hace sobre valores redondeados, porque el monto
    quedo como NUMERIC en PostgreSQL y como float en MongoDB. Esa
    diferencia de tipo se arrastra desde la sesion 3.1 y es en si misma
    uno de los criterios de decision.
    """
    a = {k: round(float(v), 2) for k, v in resultado_sql.items()}
    b = {k: round(float(v), 2) for k, v in resultado_mongo.items()}

    faltantes = set(a) ^ set(b)
    difieren = [k for k in set(a) & set(b) if abs(a[k] - b[k]) > tolerancia]

    print(f"\n  {'Clave':<24} {'PostgreSQL':>16} {'MongoDB':>16}  ")
    for clave in sorted(set(a) | set(b), key=lambda k: -a.get(k, 0)):
        marca = "" if clave not in difieren and clave not in faltantes else "  <-- difiere"
        print(f"  {str(clave)[:24]:<24} {a.get(clave, 0):>16,.2f} "
              f"{b.get(clave, 0):>16,.2f}{marca}")

    if not faltantes and not difieren:
        print(f"\n  Los dos motores coinciden en {len(a)} claves.")
    else:
        print(f"\n  ATENCION: {len(faltantes)} claves ausentes, "
              f"{len(difieren)} valores distintos.")
    return not faltantes and not difieren


def medir(funcion, repeticiones=5):
    """Minimo de varias repeticiones, conforme al criterio de la sesion 2.5."""
    tiempos = []
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        funcion()
        tiempos.append(time.perf_counter() - inicio)
    return min(tiempos) * 1000


# =====================================================================
# Pregunta 1. Importe por comercio
#
# La pregunta mas comun del caso. Ambos motores la resuelven sin
# dificultad, y ahi esta el punto: para lo habitual, los dos sirven.
# =====================================================================

def pregunta_1(conexion, coleccion):
    titulo("Pregunta 1: importe aprobado por comercio")

    print("""
  PostgreSQL necesita dos combinaciones para llegar del hecho al nombre
  del comercio. MongoDB lo tiene incorporado en el documento.
""")

    sql = """
        SELECT c.nombre, SUM(t.monto) AS importe
        FROM pagos.transacciones t
        JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
        JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
        WHERE t.estatus = 'APROBADA'
        GROUP BY c.nombre
    """
    tuberia = [
        {"$match": {"estatus": "APROBADA"}},
        {"$group": {"_id": "$comercio.nombre", "importe": {"$sum": "$monto"}}},
    ]

    resultado_sql = {n: i for n, i in conexion.execute(sql).fetchall()}
    resultado_mongo = {d["_id"]: d["importe"]
                       for d in coleccion.aggregate(tuberia)}
    comparar("importe por comercio", resultado_sql, resultado_mongo)

    print(f"\n  PostgreSQL: {medir(lambda: conexion.execute(sql).fetchall()):6.1f} ms")
    print(f"  MongoDB:    {medir(lambda: list(coleccion.aggregate(tuberia))):6.1f} ms")

    print("""
  ADVERTENCIA SOBRE ESTOS DOS NUMEROS

  No constituyen una comparacion de desempeno, y presentarlos como tal
  seria incorrecto. Cinco razones:

    1. No resuelven el mismo trabajo. PostgreSQL recompone la operacion
       con dos combinaciones; MongoDB lee un dato ya incorporado. La
       diferencia mide el MODELO, no el motor.

    2. Los indices no son equivalentes. PostgreSQL tiene los del
       capitulo 2; la coleccion, los que se hayan creado en la 3.2.

    3. El volumen es pequeno para ambos. Cinco mil registros caben en
       memoria y la medicion refleja la cache.

    4. La configuracion predeterminada de cada contenedor es distinta:
       memoria asignada, paralelismo, politicas de escritura.

    5. Ambos corren en el mismo equipo compitiendo por los mismos
       recursos.

  Lo unico que se puede afirmar: con este modelo, esta consulta, este
  volumen y este equipo, uno tardo mas que el otro.

  Quien salga de esta sesion diciendo que un motor es mas rapido que el
  otro no entendio el ejercicio. La sesion trata de criterios de
  seleccion, no de velocidad.

  Conclusion de esta pregunta: empate. Para la consulta habitual del
  caso, ambos responden de forma directa.
""")


# =====================================================================
# Pregunta 2. Buscar dentro del documento
# =====================================================================

def pregunta_2(conexion, coleccion):
    titulo("Pregunta 2: senales de riesgo, dentro del documento")

    print("""
  Contar cuantas veces aparece cada senal de riesgo. El dato vive dentro
  de un arreglo, dentro de un objeto anidado.

  Es la pregunta para la que existe el modelo documental.
""")

    sql = """
        SELECT senal, COUNT(*) AS veces
        FROM pagos.transacciones,
             jsonb_array_elements_text(
                 COALESCE(autorizacion#>'{riesgo,senales}', '[]'::jsonb)) AS senal
        GROUP BY senal
    """
    tuberia = [
        {"$unwind": "$autorizacion.riesgo.senales"},
        {"$group": {"_id": "$autorizacion.riesgo.senales",
                    "veces": {"$sum": 1}}},
    ]

    resultado_sql = {s: v for s, v in conexion.execute(sql).fetchall()}
    resultado_mongo = {d["_id"]: d["veces"]
                       for d in coleccion.aggregate(tuberia)}
    comparar("senales de riesgo", resultado_sql, resultado_mongo)

    print("""
  Ambos lo resuelven, con sintaxis distinta:

    PostgreSQL   jsonb_array_elements_text expande el arreglo a filas
    MongoDB      $unwind hace lo mismo

  Diferencia de forma: en PostgreSQL hace falta COALESCE, porque la
  funcion falla sobre un campo ausente. En MongoDB, $unwind simplemente
  descarta esos documentos, lo cual es mas comodo y mas peligroso.

  Conclusion: empate tecnico, ventaja de legibilidad para MongoDB.
""")


# =====================================================================
# Pregunta 3. El dato que cambia
# =====================================================================

def pregunta_3(conexion, coleccion):
    titulo("Pregunta 3: corregir el nombre de un comercio")

    print("""
  Una falta de ortografia en el nombre de un comercio. Hay que
  corregirla en todas las operaciones donde aparezca.
""")

    filas = conexion.execute("""
        SELECT COUNT(*) FROM pagos.comercios WHERE nombre = 'Super Norteno'
    """).fetchone()[0]
    documentos = coleccion.count_documents({"comercio.nombre": "Super Norteno"})

    print(f"  PostgreSQL: {filas} fila del catalogo")
    print(f"  MongoDB:    {documentos} documentos")

    print("""
    -- PostgreSQL
    UPDATE pagos.comercios SET nombre = 'Super Nortenio'
    WHERE nombre = 'Super Norteno';

    # MongoDB
    coleccion.update_many({"comercio.nombre": "Super Norteno"},
                          {"$set": {"comercio.nombre": "Super Nortenio"}})

  Dos diferencias, y la segunda importa mas que la primera:

    Volumen. Una fila contra mas de mil quinientos documentos.

    Atomicidad. El UPDATE de PostgreSQL es una sola operacion: se aplica
    completa o no se aplica. El update_many de MongoDB NO es atomico
    entre documentos: si el proceso se interrumpe, unos quedan
    corregidos y otros no, sin forma de revertir.

  Conclusion: ventaja clara de PostgreSQL. Es la contrapartida directa
  de la denormalizacion que hizo comoda la pregunta 1.
""")


# =====================================================================
# Pregunta 4. La estructura que no se conoce de antemano
# =====================================================================

def pregunta_4(conexion, coleccion):
    titulo("Pregunta 4: un metodo de captura nuevo")

    print("""
  Llega un metodo de captura nuevo, con campos que ningun mensaje tenia
  antes. Que hay que hacer en cada motor para aceptarlo.
""")

    nuevo = {
        "version": "2.2",
        "captura": {
            "metodo": "BIOMETRICO",
            "modalidad": "huella",
            "calidad_muestra": 0.94,
            "dispositivo_biometrico": "BIO-4410",
        },
        "emisor": {"nombre": "BANORTE", "pais": "MX"},
    }

    import json
    conexion.execute("""
        UPDATE pagos.transacciones SET autorizacion = %s::jsonb
        WHERE id_transaccion = 'TRX0000001'
    """, (json.dumps(nuevo),))
    print("  PostgreSQL: aceptado, sin alterar la tabla.")

    coleccion.update_one({"_id": "TRX0000001"},
                         {"$set": {"autorizacion": nuevo}})
    print("  MongoDB:    aceptado, sin cambio alguno.")

    campos_sql = conexion.execute("""
        SELECT COUNT(DISTINCT campo)
        FROM pagos.transacciones,
             jsonb_object_keys(autorizacion->'captura') AS campo
    """).fetchone()[0]
    print(f"\n  Campos distintos en el bloque captura: {campos_sql}")

    print("""
  Conclusion: empate. Este es el punto que suele sorprender.

  El argumento habitual a favor de MongoDB es que acepta estructura
  variable sin migracion. PostgreSQL con JSONB hace exactamente lo
  mismo, como se vio en la sesion 2.4.

  La diferencia no esta en si se puede, sino en DONDE vive la parte
  variable. En PostgreSQL es una columna dentro de un modelo estricto.
  En MongoDB es todo el documento.
""")

    # Se restablece el mensaje original para no alterar el caso.
    conexion.rollback()


# =====================================================================
# Pregunta 5. La garantia
# =====================================================================

def pregunta_5(conexion, coleccion):
    titulo("Pregunta 5: un monto que no es un numero")

    print("""
  Un sistema de origen envia el monto como texto. Que hace cada motor.
""")

    try:
        conexion.execute("""
            INSERT INTO pagos.transacciones
              (id_transaccion, fecha_hora, id_terminal, id_tarjeta,
               monto, moneda, estatus, metodo_captura)
            VALUES ('TRXMALO', NOW(), 1, 1, 'mil pesos', 'MXN',
                    'APROBADA', 'CHIP')
        """)
        print("  PostgreSQL: ACEPTADO")
    except psycopg.Error as error:
        conexion.rollback()
        print(f"  PostgreSQL: RECHAZADO ({type(error).__name__})")

    coleccion.delete_one({"_id": "TRXMALO"})
    coleccion.insert_one({"_id": "TRXMALO", "monto": "mil pesos",
                          "estatus": "APROBADA"})
    print("  MongoDB:    ACEPTADO")

    suma = list(coleccion.aggregate([
        {"$match": {"estatus": "APROBADA"}},
        {"$group": {"_id": None, "importe": {"$sum": "$monto"},
                    }},
    ]))[0]["importe"]
    documentos = coleccion.count_documents({"estatus": "APROBADA"})
    print(f"\n  Suma en MongoDB: {suma:,.2f} sobre {documentos} documentos")
    print("  El valor de texto se ignoro al sumar, y el documento si se conto.")

    coleccion.delete_one({"_id": "TRXMALO"})

    print("""
  Conclusion: ventaja de PostgreSQL por omision, empate si se declara
  validacion de esquema en MongoDB.

  El matiz importa. MongoDB PUEDE rechazarlo, como se vio en la sesion
  3.2. La diferencia es que en PostgreSQL la garantia existe desde que
  se declara la tabla, y en MongoDB existe cuando alguien decide
  declararla.

  En un equipo con rotacion, o con varios sistemas escribiendo sobre la
  misma coleccion, esa diferencia de por omision es el criterio.
""")


# =====================================================================
# Resumen
# =====================================================================

def resumen():
    titulo("RESUMEN DE LAS CINCO PREGUNTAS")
    print("""
  Pregunta                              Ventaja
  ------------------------------------  ---------------------------
  1. Importe por comercio               empate
  2. Senales dentro del documento       empate, legibilidad a Mongo
  3. Corregir un dato compartido        PostgreSQL, con claridad
  4. Estructura nueva sin migracion     empate
  5. Rechazar un dato mal formado       PostgreSQL por omision

  Lo que este ejercicio deja establecido:

    Ninguno gana en todo. La eleccion depende de que preguntas domina el
    sistema, no de cual motor es mejor.

    El argumento mas repetido a favor del modelo documental, la
    estructura variable, resulta un empate. PostgreSQL con JSONB ya lo
    resuelve.

    Las diferencias reales estan en donde vive la parte variable, en
    quien garantiza la consistencia, y en el costo de corregir datos
    incorporados.
""")


def main():
    cliente = MongoClient(uri_mongo(), serverSelectionTimeoutMS=5000)
    coleccion = cliente[os.getenv("MONGO_DB", "pagos")][COLECCION]

    if coleccion.count_documents({}) == 0:
        raise SystemExit("Coleccion vacia. Ejecuta c3_s1_b3_carga.py")

    with psycopg.connect(cadena_postgres()) as conexion:
        pregunta_1(conexion, coleccion)
        pregunta_2(conexion, coleccion)
        pregunta_3(conexion, coleccion)
        pregunta_4(conexion, coleccion)
        pregunta_5(conexion, coleccion)
        conexion.rollback()

    resumen()
    cliente.close()


if __name__ == "__main__":
    main()
