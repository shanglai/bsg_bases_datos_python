"""
c2_s2_b3_pandas_polars.py
Lectura de resultados hacia pandas y hacia Polars.

Puntos de la sesion que este script ejercita:
    - lectura con pandas.read_sql sobre un motor de SQLAlchemy
    - lectura con polars.read_database y read_database_uri
    - que ocurre con el tipo NUMERIC al cruzar hacia el dataframe
    - donde conviene agregar: en el motor o en el dataframe

Requisitos:
    pip install "psycopg[binary]" python-dotenv sqlalchemy pandas polars
    pip install connectorx        (opcional, para read_database_uri)
    base cargada con c2_s1_b4_carga.py

Ejecucion: python c2_s2_b3_pandas_polars.py
"""

import os
import time
from decimal import Decimal

import pandas as pd
import polars as pl
import psycopg
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


# =====================================================================
# Conexiones
#
# Tres formas distintas de nombrar el mismo servidor, porque cada
# biblioteca espera un formato propio.
# =====================================================================

def credenciales():
    return {
        "host": os.getenv("PGHOST", "localhost"),
        "port": os.getenv("PGPORT", "5432"),
        "db": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
    }


def cadena_psycopg():
    c = credenciales()
    return (f"host={c['host']} port={c['port']} dbname={c['db']} "
            f"user={c['user']} password={c['password']}")


def uri_sqlalchemy():
    """URI para SQLAlchemy.

    El prefijo debe ser postgresql+psycopg, con el nombre del
    controlador declarado de forma explicita.

    Una URI que diga solo postgresql:// hace que SQLAlchemy 2.0 busque
    psycopg2, que es el controlador de la generacion anterior y no esta
    instalado en este entorno. El error resultante es
    ModuleNotFoundError: No module named 'psycopg2', y es confuso porque
    el codigo nunca menciona psycopg2.
    """
    c = credenciales()
    return (f"postgresql+psycopg://{c['user']}:{c['password']}"
            f"@{c['host']}:{c['port']}/{c['db']}")


def uri_connectorx():
    """URI para connectorx, que no usa SQLAlchemy y espera el prefijo simple."""
    c = credenciales()
    return (f"postgresql://{c['user']}:{c['password']}"
            f"@{c['host']}:{c['port']}/{c['db']}")


CONSULTA_RESUMEN = """
    SELECT c.nombre                AS comercio,
           c.ciudad,
           COUNT(*)                AS operaciones,
           SUM(t.monto)            AS importe_total,
           ROUND(AVG(t.monto), 2)  AS ticket_promedio
    FROM pagos.transacciones t
    JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
    JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
    WHERE t.estatus = 'APROBADA'
    GROUP BY c.nombre, c.ciudad
    ORDER BY importe_total DESC
"""


# =====================================================================
# Bloque 1. Lectura con pandas
# =====================================================================

def bloque_1_pandas():
    print("=== Bloque 1: lectura con pandas ===")

    motor = create_engine(uri_sqlalchemy())
    df = pd.read_sql(CONSULTA_RESUMEN, motor)

    print(f"\nForma del resultado: {df.shape}")
    print(df.to_string(index=False))

    print("\nTipos que dedujo pandas:")
    print(df.dtypes.to_string())
    print()


# =====================================================================
# Bloque 2. Lectura con Polars
#
# Polars ofrece dos caminos, y no son equivalentes.
# =====================================================================

def bloque_2_polars():
    print("=== Bloque 2: lectura con Polars ===")

    # Camino 1: read_database sobre una conexion ya abierta.
    # Reutiliza la conexion de psycopg y no requiere dependencias extra.
    with psycopg.connect(cadena_psycopg()) as conexion:
        df_conexion = pl.read_database(CONSULTA_RESUMEN, conexion)

    print("\nread_database sobre conexion de psycopg:")
    print(df_conexion)

    # Camino 2: read_database_uri, que delega en connectorx o en ADBC.
    # Es mas rapido en volumenes altos porque lee en paralelo, pero
    # exige instalar una dependencia adicional.
    try:
        df_uri = pl.read_database_uri(CONSULTA_RESUMEN, uri_connectorx(),
                                      engine="connectorx")
        print(f"\nread_database_uri con connectorx: {df_uri.shape}")
    except Exception as error:
        print(f"\nread_database_uri no disponible: {type(error).__name__}")
        print("Instalar con: pip install connectorx")
    print()


# =====================================================================
# Bloque 3. El hallazgo de la sesion
#
# En la sesion 2.1 se declaro monto como NUMERIC(12,2), con el argumento
# de que el punto flotante no representa importes de forma exacta.
#
# Ese argumento sigue siendo valido dentro del motor. Al cruzar hacia el
# dataframe, cada biblioteca decide por su cuenta que tipo asignar, y la
# garantia no siempre sobrevive el cruce.
# =====================================================================

def bloque_3_el_tipo_al_cruzar():
    print("=== Bloque 3: que pasa con NUMERIC al llegar al dataframe ===")

    consulta = "SELECT monto FROM pagos.transacciones"

    # Valor de referencia: la suma calculada por el motor.
    with psycopg.connect(cadena_psycopg()) as conexion:
        exacta = conexion.execute(
            "SELECT SUM(monto) FROM pagos.transacciones").fetchone()[0]
    print(f"\nSuma calculada por el motor: {exacta}  (tipo {type(exacta).__name__})")

    # pandas
    motor = create_engine(uri_sqlalchemy())
    df = pd.read_sql(consulta, motor)
    suma_pandas = float(df["monto"].sum())
    print(f"\npandas.read_sql")
    print(f"  tipo de la columna: {df['monto'].dtype}")
    print(f"  suma: {suma_pandas}")
    print(f"  el mismo valor con veinte decimales: {suma_pandas:.20f}")

    # Polars sobre conexion de psycopg
    with psycopg.connect(cadena_psycopg()) as conexion:
        dfp = pl.read_database(consulta, conexion)
    print(f"\npolars.read_database sobre psycopg")
    print(f"  tipo de la columna: {dfp['monto'].dtype}")
    print(f"  suma: {dfp['monto'].sum()}")

    print("""
Observaciones:

  pandas convierte NUMERIC a punto flotante de 64 bits. La garantia de
  aritmetica decimal exacta que se establecio en la sesion 2.1 termina
  en la frontera del dataframe.

  Con cinco mil filas la diferencia no alcanza a manifestarse al
  redondear a dos decimales. La representacion interna, sin embargo, ya
  no es exacta, como muestran los veinte decimales impresos arriba.

  Polars sobre una conexion de psycopg conserva el tipo decimal.

  Otras rutas de lectura toman decisiones distintas: connectorx entrega
  un decimal con escala diferente, y el controlador ADBC puede entregar
  la columna como texto. Conviene verificar el tipo despues de leer, en
  lugar de suponerlo.
""")


# =====================================================================
# Bloque 4. Donde conviene agregar
#
# La consecuencia practica del bloque anterior.
# =====================================================================

def bloque_4_donde_agregar():
    print("=== Bloque 4: agregar en el motor o en el dataframe ===")

    motor = create_engine(uri_sqlalchemy())

    # Opcion A. Traer todo y agregar en pandas.
    inicio = time.perf_counter()
    todo = pd.read_sql("""
        SELECT c.nombre AS comercio, t.monto
        FROM pagos.transacciones t
        JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
        JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
        WHERE t.estatus = 'APROBADA'
    """, motor)
    resumen_pandas = todo.groupby("comercio")["monto"].agg(["count", "sum"])
    tiempo_a = time.perf_counter() - inicio

    # Opcion B. Agregar en el motor y traer el resultado.
    inicio = time.perf_counter()
    resumen_motor = pd.read_sql(CONSULTA_RESUMEN, motor)
    tiempo_b = time.perf_counter() - inicio

    print(f"\n  Traer {len(todo)} filas y agregar en pandas: {tiempo_a:.3f} s")
    print(f"  Agregar en el motor y traer {len(resumen_motor)} filas: {tiempo_b:.3f} s")

    print("""
Criterio de decision:

  Agregar en el motor cuando el resultado es mucho mas pequeno que el
  origen, cuando el calculo es una agregacion estandar, y cuando el
  valor es monetario y conviene que la aritmetica ocurra en NUMERIC.

  Traer al dataframe cuando el analisis requiere operaciones que SQL no
  expresa con comodidad, cuando el resultado alimenta un modelo o una
  grafica, o cuando se van a explorar muchas variantes sobre el mismo
  conjunto.

  Con cinco mil filas la diferencia de tiempo es menor. El criterio no
  se sostiene en el tiempo medido hoy, sino en el volumen que tendra el
  sistema en produccion.
""")


# =====================================================================
# Bloque 5. Parametros tambien en el dataframe
#
# La practica de la sesion 2.1 se mantiene: los valores variables se
# pasan como parametros, tambien cuando el destino es un dataframe.
# =====================================================================

def bloque_5_parametros():
    print("=== Bloque 5: lectura parametrizada ===")

    consulta = """
        SELECT c.nombre, COUNT(*) AS operaciones, SUM(t.monto) AS importe
        FROM pagos.transacciones t
        JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
        JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
        WHERE c.ciudad = %(ciudad)s AND t.estatus = %(estatus)s
        GROUP BY c.nombre
        ORDER BY importe DESC
    """

    with psycopg.connect(cadena_psycopg()) as conexion:
        df = pd.read_sql(consulta, conexion,
                         params={"ciudad": "Ciudad de Mexico",
                                 "estatus": "APROBADA"})
    print(f"\n{df.to_string(index=False)}")

    print("""
  pandas admite el parametro params y lo entrega al controlador. La
  construccion de la condicion por concatenacion de cadenas es tan
  incorrecta aqui como lo era en la sesion 2.1.
""")


# =====================================================================
# Bloque 6. Escritura de resultados hacia la base
# =====================================================================

def bloque_6_escritura():
    print("=== Bloque 6: escribir el resultado de vuelta ===")

    motor = create_engine(uri_sqlalchemy())
    resumen = pd.read_sql(CONSULTA_RESUMEN, motor)

    resumen.to_sql("resumen_comercio", motor, schema="pagos",
                   if_exists="replace", index=False)
    print(f"\n  pandas.to_sql escribio {len(resumen)} filas en "
          f"pagos.resumen_comercio")

    comprobacion = pd.read_sql(
        "SELECT COUNT(*) AS filas FROM pagos.resumen_comercio", motor)
    print(f"  Comprobacion: {comprobacion['filas'][0]} filas en la tabla")

    print("""
  Advertencias sobre to_sql:

    if_exists='replace' elimina la tabla y la vuelve a crear. La
    estructura resultante la deduce pandas de los tipos del dataframe,
    de modo que no lleva llaves, ni restricciones, ni indices.

    Una tabla de resultados es aceptable asi. Una tabla del modelo no:
    su estructura se declara con DDL, como en la sesion 2.1.

    index=False evita que el indice del dataframe se escriba como una
    columna adicional. Es un error frecuente al omitirlo.
""")


if __name__ == "__main__":
    bloque_1_pandas()
    bloque_2_polars()
    bloque_3_el_tipo_al_cruzar()
    bloque_4_donde_agregar()
    bloque_5_parametros()
    bloque_6_escritura()
