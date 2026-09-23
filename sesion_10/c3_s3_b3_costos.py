"""
c3_s3_b3_costos.py
Los tres costos que la comparacion directa no muestra.

La sesion anterior comparo cinco preguntas de consulta. Este modulo
examina lo que no se ve al consultar: el costo de mantener la
consistencia, el de operar cada motor, y el de cambiar de opinion.

Requisitos: ambos motores activos con el caso cargado
Ejecucion:  python c3_s3_b3_costos.py
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


# =====================================================================
# Costo 1. La consistencia
# =====================================================================

def costo_1_consistencia(conexion, coleccion):
    titulo("Costo 1: mantener la consistencia")

    print("""
  El nombre de un comercio vive en un solo lugar en PostgreSQL, y
  repetido en MongoDB. Eso ya se vio. Lo que falta examinar es que
  ocurre cuando la correccion falla a la mitad.
""")

    # Se simula una correccion interrumpida sobre un subconjunto.
    objetivo = "Cafe Aurora"
    total = coleccion.count_documents({"comercio.nombre": objetivo})
    print(f"  Documentos con '{objetivo}': {total}")

    # Solo se actualiza una parte, como si el proceso se hubiera cortado.
    algunos = [d["_id"] for d in
               coleccion.find({"comercio.nombre": objetivo}, {"_id": 1}).limit(100)]
    coleccion.update_many({"_id": {"$in": algunos}},
                          {"$set": {"comercio.nombre": "Cafe Aurora SA"}})

    # Se agrupa por el identificador del comercio, que NO cambio, para
    # exhibir que un mismo comercio quedo con dos nombres distintos.
    id_comercio = coleccion.find_one(
        {"comercio.nombre": objetivo})["comercio"]["id"]

    print("\n  Tras una correccion interrumpida a los 100 documentos,")
    print(f"  agrupando por comercio.id = {id_comercio}, que no cambio:")
    for documento in coleccion.aggregate([
        {"$match": {"comercio.id": id_comercio}},
        {"$group": {"_id": "$comercio.nombre", "documentos": {"$sum": 1}}},
        {"$sort": {"documentos": -1}},
    ]):
        print(f"    '{documento['_id']}': {documento['documentos']} documentos")

    print("""
  El mismo comercio, con el mismo identificador, aparece ahora con dos
  nombres distintos. Ninguna consulta lo advierte. Una agrupacion por
  nombre lo reporta como dos comercios.

  En PostgreSQL esto no puede ocurrir: el nombre vive en una fila y el
  UPDATE es atomico.
""")

    # Se restablece el estado original.
    coleccion.update_many({"comercio.nombre": "Cafe Aurora SA"},
                          {"$set": {"comercio.nombre": objetivo}})
    print("  Estado restablecido.")

    print("""
  Como se mitiga en MongoDB:

    Transacciones multidocumento, disponibles desde la version 4. Exigen
    conjunto de replicas, aun en un solo nodo, y tienen limite de
    duracion y de tamano.

    Referenciar en lugar de incorporar, con $lookup. Devuelve el
    problema de las combinaciones que la denormalizacion evitaba.

    Un identificador estable, como el comercio.id que este modelo
    conservo. Permite detectar la inconsistencia, aunque no impedirla.

  El criterio que se desprende: la denormalizacion es aceptable cuando
  el dato incorporado casi no cambia. Cuando cambia, el costo reaparece
  entero.
""")


# =====================================================================
# Costo 2. La operacion
# =====================================================================

def costo_2_operacion(conexion, coleccion):
    titulo("Costo 2: operar cada motor")

    print("\n  Tamano del caso en cada motor:")

    filas = conexion.execute("""
        SELECT pg_size_pretty(SUM(pg_total_relation_size(c.oid))) AS total
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'pagos' AND c.relkind = 'r'
    """).fetchone()[0]
    print(f"    PostgreSQL, seis tablas:  {filas}")

    try:
        estadisticas = coleccion.database.command("collstats", COLECCION)
        almacenado = estadisticas.get("storageSize", 0)
        indices = estadisticas.get("totalIndexSize", 0)
        print(f"    MongoDB, una coleccion:   "
              f"{almacenado / 1024 / 1024:.1f} MB de datos, "
              f"{indices / 1024 / 1024:.1f} MB de indices")
    except Exception as error:
        print(f"    MongoDB: no fue posible obtener collstats ({type(error).__name__})")

    print("""
  El documento repite el nombre del comercio, la ciudad, el nombre del
  cliente y su correo en cada operacion. Esa redundancia se paga en
  disco, en memoria y en respaldo.

  Con cinco mil documentos la cifra es anecdotica. Con quinientos
  millones, es una decision de presupuesto.
""")

    print("""
  Otros costos de operacion, que no se miden aqui pero se deciden igual:

    Conocimiento del equipo. SQL lo sabe mas gente que la canalizacion
    de agregacion. Con rotacion alta, eso pesa.

    Herramientas. DBeaver Community se conecta a PostgreSQL y no a
    MongoDB. Este mismo curso lo sufrio.

    Respaldo y recuperacion. Ambos lo resuelven, con procedimientos y
    vocabularios distintos que hay que aprender por separado.

    Dos motores en lugar de uno. Si el caso cabe en PostgreSQL con
    JSONB, operar solo ese motor tiene un valor que no aparece en
    ninguna comparacion de caracteristicas.
""")


# =====================================================================
# Costo 3. Cambiar de opinion
# =====================================================================

def costo_3_cambiar(conexion, coleccion):
    titulo("Costo 3: cambiar de opinion despues")

    print("""
  La pregunta que ninguna comparacion de caracteristicas responde:
  cuanto cuesta migrar si la decision resulta equivocada.
""")

    inicio = time.perf_counter()
    documentos = list(coleccion.find().limit(1000))
    lectura = time.perf_counter() - inicio

    print(f"  Leer 1000 documentos de MongoDB: {lectura * 1000:.0f} ms")
    print(f"  Extrapolado a 5000: {lectura * 5 * 1000:.0f} ms")

    print("""
  De MongoDB hacia PostgreSQL:

    Hay que inventar el esquema. El modelo documental no lo declara, de
    modo que primero hay que averiguar que formas conviven ahi dentro,
    con $type y jsonb_object_keys. Lo que en la sesion 1.2 fue un
    ejercicio de modelado, aqui es un ejercicio de arqueologia.

    Hay que resolver los datos que no encajan. El monto escrito como
    texto no entra en una columna NUMERIC, y hay que decidir que hacer
    con el.

    Hay que deshacer la denormalizacion, reconstruyendo los catalogos a
    partir de los valores repetidos. Es exactamente el trabajo de la
    sesion 1.2.

  De PostgreSQL hacia MongoDB:

    Es el camino que recorrio la sesion 3.1, en un script de doscientas
    lineas. El esquema ya estaba declarado y la denormalizacion fue una
    decision, no un descubrimiento.

  Asimetria a registrar: salir del modelo relacional es mas barato que
  entrar. Es un argumento a favor de empezar por el modelo estricto
  cuando la decision no es clara.
""")


# =====================================================================
# Lo que si es criterio, y lo que no
# =====================================================================

def criterios_falsos():
    titulo("Argumentos que NO son criterio")

    print("""
  Aparecen con frecuencia y no resisten el examen de este curso.

  "MongoDB es para datos no estructurados."
     El caso tiene estructura, y muy clara. Lo que varia es una parte
     acotada. La sesion 2.4 mostro que PostgreSQL absorbe esa parte con
     JSONB sin renunciar al resto.

  "MongoDB es mas rapido."
     Depende del modelo, de los indices, del volumen y de la consulta.
     Las mediciones de este curso no permiten afirmarlo, y ninguna
     medicion generica lo permite.

  "MongoDB escala y PostgreSQL no."
     PostgreSQL escala en vertical y con replicas de lectura hasta
     volumenes muy altos. El reparto horizontal automatico si es una
     diferencia real, y aplica cuando el volumen excede lo que cabe en
     un servidor. Conviene comprobar que ese es el caso antes de usarlo
     como argumento.

  "No hay que definir esquema, es mas rapido para empezar."
     Cierto, y es el costo diferido mas caro del modelo. La sesion 3.2
     mostro que la validacion se puede agregar despues, y tambien que
     agregarla sobre datos historicos es un problema aparte.

  "Ya tenemos MongoDB, aprovechemoslo."
     Este si es un criterio legitimo, aunque no tecnico. El costo de
     operar un motor que el equipo ya conoce es menor. Conviene
     declararlo como lo que es, y no disfrazarlo de argumento tecnico.
""")


def main():
    cliente = MongoClient(uri_mongo(), serverSelectionTimeoutMS=5000)
    coleccion = cliente[os.getenv("MONGO_DB", "pagos")][COLECCION]

    if coleccion.count_documents({}) == 0:
        raise SystemExit("Coleccion vacia. Ejecuta c3_s1_b3_carga.py")

    with psycopg.connect(cadena_postgres()) as conexion:
        costo_1_consistencia(conexion, coleccion)
        costo_2_operacion(conexion, coleccion)
        costo_3_cambiar(conexion, coleccion)

    criterios_falsos()
    cliente.close()


if __name__ == "__main__":
    main()
