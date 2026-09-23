"""
c3_s3_b8_solucionario.py
Solucionario del taller de la sesion 3.3.

Documento para el instructor. NO se entrega al participante.

ADVERTENCIA SOBRE ESTE SOLUCIONARIO

Los talleres anteriores tenian respuestas correctas. Este no. Las partes
C y E admiten varias respuestas defendibles, y lo que se evalua es el
argumento.

Este archivo contiene, para esas partes, los ELEMENTOS que debe tener
una respuesta completa, no la respuesta. Un participante que llegue a
una conclusion distinta con un argumento solido obtiene calificacion
completa.

Requisitos: ambos motores activos con el caso cargado
Ejecucion:  python c3_s3_b8_solucionario.py
"""

import os
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


def punto(clave, enunciado):
    print("\n" + "-" * 72 + f"\n{clave}. {enunciado}\n" + "-" * 72)


# =====================================================================

def parte_a(conexion, coleccion):
    titulo("PARTE A. VERIFICAR LA COMPARACION")

    punto("A3", "Tasa de contracargo por comercio")

    sql = """
        SELECT c.nombre,
               COUNT(*) AS aprobadas,
               COUNT(cc.id_contracargo) AS contracargos,
               ROUND(100.0 * COUNT(cc.id_contracargo) / COUNT(*), 3) AS tasa
        FROM pagos.transacciones t
        JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
        JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
        LEFT JOIN pagos.contracargos cc ON cc.id_transaccion = t.id_transaccion
        WHERE t.estatus = 'APROBADA'
        GROUP BY c.nombre ORDER BY tasa DESC
    """
    tuberia = [
        {"$match": {"estatus": "APROBADA"}},
        {"$group": {"_id": "$comercio.nombre",
                    "aprobadas": {"$sum": 1},
                    "contracargos": {"$sum": {"$cond": [
                        {"$eq": ["$tiene_contracargo", True]}, 1, 0]}}}},
    ]

    resultado_sql = {n: (a, c) for n, a, c, _ in conexion.execute(sql).fetchall()}
    resultado_mongo = {d["_id"]: (d["aprobadas"], d["contracargos"])
                       for d in coleccion.aggregate(tuberia)}

    print(f"\n  {'Comercio':<20} {'PostgreSQL':>18} {'MongoDB':>18}")
    coinciden = True
    for nombre in sorted(resultado_sql, key=lambda n: -resultado_sql[n][0]):
        a, b = resultado_sql[nombre], resultado_mongo.get(nombre, (0, 0))
        if a != b:
            coinciden = False
        print(f"  {nombre:<20} {str(a):>18} {str(b):>18}")
    print(f"\n  Coinciden: {'si' if coinciden else 'NO'}")

    print("""
  Nota de diseno que conviene señalar: en MongoDB la existencia del
  contracargo se resolvio con el campo booleano tiene_contracargo, que
  la sesion 3.1 incorporo al documento.

  Si el contracargo viviera en otra coleccion, haria falta $lookup, y
  ademas se perderia la garantia de que ambos se escriban juntos. Fue
  una decision de modelado tomada para evitar una transaccion
  multidocumento.

  En PostgreSQL la misma pregunta se resuelve con LEFT JOIN, sin haber
  tenido que anticipar nada al modelar.
""")

    punto("A4", "Operaciones de alto monto con riesgo alto")
    sql = """
        SELECT t.id_transaccion, t.monto, c.nombre AS comercio,
               t.autorizacion#>>'{emisor,nombre}' AS emisor
        FROM pagos.transacciones t
        JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
        JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
        WHERE (t.autorizacion#>>'{riesgo,puntaje}')::INT > 80
        ORDER BY t.monto DESC LIMIT 5
    """
    print("\n  PostgreSQL:")
    for fila in conexion.execute(sql).fetchall():
        print(f"    {fila[0]}  {float(fila[1]):>12,.2f}  {fila[2]:<18} {fila[3]}")

    print("\n  MongoDB:")
    for d in coleccion.aggregate([
        {"$match": {"autorizacion.riesgo.puntaje": {"$gt": 80}}},
        {"$sort": {"monto": -1}}, {"$limit": 5},
        {"$project": {"monto": 1, "comercio": "$comercio.nombre",
                      "emisor": "$autorizacion.emisor.nombre"}},
    ]):
        print(f"    {d['_id']}  {d['monto']:>12,.2f}  "
              f"{d['comercio']:<18} {d['emisor']}")

    print("""
  A5. Cual resulto mas breve:

    A3 es mas breve en MongoDB, y solo porque el modelo incorporo el
    booleano. Sin esa decision previa, seria mas largo.

    A4 es mas breve en MongoDB. PostgreSQL necesita #>> y una conversion
    de tipo explicita; MongoDB compara directamente porque el puntaje se
    almaceno como numero.

  El punto a extraer: la brevedad depende del MODELO, no del motor. Un
  modelo relacional que incorporara los mismos campos seria igual de
  breve, y pagaria los mismos costos.
""")


def parte_b(conexion, coleccion):
    titulo("PARTE B. LOS COSTOS QUE NO SE VEN")

    punto("B1", "Por que el comercio termina con dos nombres")
    print("""
  Explicacion esperada:

    El nombre del comercio esta incorporado en cada documento. La
    correccion recorre documentos uno por uno y NO es atomica entre
    ellos. Si el proceso se interrumpe, unos quedan corregidos y otros
    no.

    Ninguna consulta lo advierte porque no hay restriccion que exija que
    todos los documentos con el mismo comercio.id tengan el mismo
    nombre. Una agrupacion por nombre lo reporta como dos comercios
    distintos, y el resultado parece razonable.

  Es el mismo fenomeno del archivo plano de la sesion 1.1, donde el
  mismo comercio aparecia bajo tres escrituras. La diferencia es que
  alla era un defecto del origen y aqui es una consecuencia del modelo.
""")

    punto("B2", "Dos mecanismos y lo que cede cada uno")
    print("""
  Cualquier par de estos es aceptable:

    Transacciones multidocumento.
      Cede: exige conjunto de replicas aun en un solo nodo, tiene limite
      de duracion y de tamano, y encarece la escritura.

    Referenciar en lugar de incorporar, con $lookup.
      Cede: devuelve el problema de las combinaciones que la
      denormalizacion evitaba, y $lookup cuesta mas que un JOIN
      optimizado.

    Escribir por lotes con reintento idempotente.
      Cede: no evita el estado intermedio, solo acota su duracion. Entre
      un lote y otro la coleccion sigue siendo inconsistente.

    Validacion de esquema.
      Cede: no resuelve este caso. La validacion verifica la forma de
      cada documento, no la consistencia entre documentos. Es importante
      que el participante lo note.

  Respuesta que NO obtiene el punto: "usar validacion de esquema". No
  aplica al problema.
""")

    punto("B3", "Tamano en disco")
    tamano_sql = conexion.execute("""
        SELECT pg_size_pretty(SUM(pg_total_relation_size(c.oid)))
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'pagos' AND c.relkind = 'r'
    """).fetchone()[0]
    print(f"\n  PostgreSQL, seis tablas: {tamano_sql}")
    try:
        est = coleccion.database.command("collstats", COLECCION)
        print(f"  MongoDB, una coleccion:  "
              f"{est.get('storageSize', 0) / 1024 / 1024:.1f} MB")
    except Exception:
        print("  MongoDB: collstats no disponible en este servidor")

    print("""
  La explicacion importa mas que el numero: el documento repite el
  nombre del comercio, la ciudad, el nombre del cliente y su correo en
  cada operacion.

  Con cinco mil documentos la cifra es anecdotica. El ejercicio consiste
  en extrapolar: con quinientos millones, es presupuesto.
""")

    punto("B4 y B5", "Migrar de vuelta, y la asimetria")
    print("""
  Pasos para migrar de MongoDB hacia un modelo relacional:

    1. Descubrir el esquema. El modelo documental no lo declara, de modo
       que hay que averiguar que formas conviven, con $type y con
       inventario de claves.
    2. Decidir que hacer con los documentos que no encajan.
    3. Reconstruir los catalogos a partir de los valores repetidos, que
       es el trabajo de la sesion 1.2.
    4. Resolver las inconsistencias entre documentos que comparten
       entidad, como las dos versiones del nombre de B1.
    5. Declarar el DDL y cargar.

  La asimetria:

    Salir del modelo relacional es barato porque el esquema ya esta
    declarado y la denormalizacion es una decision deliberada. La sesion
    3.1 lo hizo en un script.

    Entrar es caro porque hay que descubrir el esquema en lugar de
    leerlo, y porque los datos que no encajan ya estan dentro.

  Consecuencia practica, que es lo que se evalua: cuando la decision no
  es clara, conviene empezar por el modelo estricto. Es la opcion con
  salida mas barata.
""")


def parte_c():
    titulo("PARTE C. ESCENARIOS")

    print("""
  Recordatorio para la revision: no hay respuesta unica. Se evalua que
  el argumento use los criterios del curso y que declare lo que cede.

  Abajo se indica la respuesta que el escenario favorece y, mas
  importante, QUE DEBE APARECER en cualquier respuesta completa.
""")

    punto("C1", "Expedientes clinicos")
    print("""
  Favorece: PostgreSQL con JSONB.

  Elementos que debe contener la respuesta:
    datos del paciente compartidos y que se corrigen con frecuencia, de
      modo que la denormalizacion cobraria caro
    obligaciones regulatorias de trazabilidad, que piden garantias del
      motor y no de la aplicacion
    la variabilidad esta acotada a los campos por especialidad, que es
      exactamente el caso de JSONB

  Respuesta contraria aceptable: MongoDB, si el argumento reconoce que
  hay que declarar validacion de esquema desde el inicio y resolver la
  consistencia del paciente por referencia y no por incorporacion.
""")

    punto("C2", "Catalogo de comercio electronico")
    print("""
  Favorece: MongoDB.

  Elementos que debe contener:
    los atributos difieren por categoria y el conjunto no se conoce de
      antemano
    se lee mucho mas de lo que se escribe
    la ficha se muestra completa, que es leer el agregado entero
    no hay integridad referencial critica entre productos

  Este escenario es importante porque da el resultado CONTRARIO al caso
  de pagos con los mismos criterios. Conviene señalarlo en la revision:
  demuestra que los criterios funcionan y que la respuesta no es una
  preferencia.
""")

    punto("C3", "Telemetria de vehiculos")
    print("""
  Favorece: ninguno de los dos del todo.

  Elementos que debe contener:
    el volumen y el patron de agregacion temporal apuntan a un almacen
      analitico columnar, que es el capitulo 4
    casi nunca se lee un registro individual, de modo que la ventaja del
      documento no aplica
    la estructura varia por modelo, lo que descarta un esquema rigido

  La mejor respuesta reconoce que la pregunta esta mal planteada si solo
  se admiten dos opciones. Un participante que lo diga merece el punto
  completo.

  Respuestas aceptables entre los dos: MongoDB para la ingesta y un
  almacen analitico para el analisis, que es una arquitectura comun.
""")

    punto("C4", "Pagos a cien veces el volumen, en tres regiones")
    print("""
  No hay favorito claro. Lo que se evalua es que el argumento NO se
  resuelva con "MongoDB escala".

  Elementos que debe contener:
    comprobar que el volumen excede de verdad lo que un servidor
      sostiene, antes de usar el reparto horizontal como argumento
    PostgreSQL con replicas de lectura y particionado cubre mucho mas
      volumen del que se supone
    la operacion en tres regiones plantea un problema distinto, de
      latencia y de residencia de datos, que ninguno de los dos resuelve
      solo
    las obligaciones de integridad del caso no desaparecen al crecer

  Respuesta que no obtiene el punto: cambiar de motor solo por el
  volumen, sin haber estimado el volumen.
""")

    punto("C5", "Nomina")
    print("""
  Favorece: PostgreSQL, con claridad.

  Elementos que debe contener:
    estructura estable, que no aprovecha la flexibilidad
    montos que deben cuadrar al centavo, que exige NUMERIC y no float
    obligaciones fiscales, que piden garantias del motor
    veinte personas consultando, que es SQL conocido por el area

  Es el escenario mas claro del conjunto, y sirve para calibrar: si
  alguien elige MongoDB aqui, conviene revisar si entendio los
  criterios.
""")


def parte_d():
    titulo("PARTE D. EL ARGUMENTO EN CONTRA")

    print("""
  D1. "MongoDB es para datos no estructurados."
      NO RESISTE. El caso tiene estructura clara. Lo que varia es una
      porcion acotada, y la sesion 2.4 mostro que JSONB la absorbe sin
      renunciar al resto. La evidencia esta en la pregunta 4 de la
      comparacion, donde ambos aceptaron el metodo nuevo.

  D2. "MongoDB es mas rapido."
      NO RESISTE como afirmacion general. Las mediciones del curso no lo
      permiten, por las cinco razones que enumera el script de
      comparacion. Una respuesta completa cita al menos tres.

  D3. "No hay que definir esquema, se avanza mas rapido."
      PARCIALMENTE VALIDO. Es cierto al inicio y es el costo diferido
      mas caro. La sesion 3.2 mostro que la validacion se puede agregar
      despues, y que agregarla sobre datos historicos es un problema
      aparte. Se valora que reconozca ambas cosas.

  D4. "PostgreSQL no escala."
      NO RESISTE como esta formulado. Escala en vertical y con replicas
      hasta volumenes muy altos. El reparto horizontal automatico si es
      una diferencia real, y aplica cuando el volumen excede un
      servidor. Una respuesta completa distingue las dos cosas.

  D5. "Ya tenemos MongoDB, conviene usarlo."
      VALIDO, y no tecnico. El costo de operar un motor que el equipo ya
      conoce es real y se puede cuantificar. Lo que se evalua es que el
      participante lo declare como criterio organizacional y no lo
      disfrace de argumento tecnico.

  El patron a enseñar: cuatro de los cinco argumentos mas repetidos no
  resisten, y el que si resiste no es tecnico.
""")


def parte_e():
    titulo("PARTE E. LA MATRIZ")

    print("""
  E1 y E2. Matriz del caso de pagos

  La version resuelta esta en c3_s3_b4_matriz.md, seccion 5. El
  participante debe llegar a una conclusion propia, no copiarla.

  Elementos que debe contener una matriz completa:

    las siete preguntas respondidas sobre el caso concreto, no en
      general
    una decision explicita
    QUE SE CEDE al elegir
    QUE HARIA CAMBIAR la decision

  Los dos ultimos renglones concentran la evaluacion. Una matriz sin
  ellos esta incompleta aunque la decision sea la misma que la del
  instructor.

  Errores frecuentes a vigilar:

    Declarar que no se cede nada. Siempre se cede algo. Si el
    participante no lo encuentra, no examino el problema.

    Poner como condicion de cambio algo que nunca va a ocurrir. La
    condicion debe ser verificable y plausible.

    Responder las preguntas con generalidades del tipo "depende del
    caso". El caso esta dado.

  E3. La matriz del motor descartado

    Este punto es el que mas cuesta y el que mas enseña. Obliga a
    sustentar el descarte, no solo la eleccion.

    Una respuesta completa reconoce que el motor descartado TAMBIEN
    habria funcionado, y explica por que el otro funciona mejor para
    este caso. Descartar un motor diciendo que "no sirve" es el error a
    corregir.
""")


def criterios():
    titulo("CRITERIOS DE CALIFICACION")
    print("""
  Este taller se califica distinto de los anteriores.

  NO se evalua
    haber elegido el mismo motor que el instructor
    haber llegado a la misma conclusion que el material

  SI se evalua
    que el argumento use los criterios del curso
    que cite evidencia de lo observado, no afirmaciones generales
    que declare que se cede
    que identifique que haria cambiar la decision

  Parte A, 15 por ciento
    A2 exige al menos tres razones. El error a vigilar es que reporten
    los tiempos como si fueran una comparacion de desempeno.

  Parte B, 20 por ciento
    B1 y B5 concentran el valor.
    En B2, la validacion de esquema NO es una respuesta valida: no
    resuelve consistencia entre documentos.

  Parte C, 30 por ciento
    C2 debe dar el resultado contrario a C1 y C5. Si un participante
    elige lo mismo para los tres, no esta aplicando los criterios.
    En C3, reconocer que la pregunta esta mal planteada merece el punto
    completo.
    En C4, resolver con "MongoDB escala" no obtiene el punto.

  Parte D, 20 por ciento
    Se evalua que distinga criterio de consigna. D5 es el unico valido y
    no es tecnico.

  Parte E, 15 por ciento
    Los dos ultimos renglones de la matriz.
    E3 es el punto que mas enseña: sustentar el descarte.

  Nota para el instructor

    Si todo el grupo llega a la misma conclusion en los cinco
    escenarios, algo salio mal: los escenarios estan diseñados para
    apuntar a lados distintos. Conviene revisar si el grupo esta
    razonando o repitiendo.
""")


def main():
    cliente = MongoClient(uri_mongo(), serverSelectionTimeoutMS=5000)
    coleccion = cliente[os.getenv("MONGO_DB", "pagos")][COLECCION]

    if coleccion.count_documents({}) == 0:
        raise SystemExit("Coleccion vacia. Ejecuta c3_s1_b3_carga.py")

    with psycopg.connect(cadena_postgres()) as conexion:
        parte_a(conexion, coleccion)
        parte_b(conexion, coleccion)

    parte_c()
    parte_d()
    parte_e()
    criterios()
    cliente.close()


if __name__ == "__main__":
    main()
