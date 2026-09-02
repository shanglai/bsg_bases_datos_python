"""
c2_s3_b3_ventanas_dataframe.py
La misma pregunta analitica, resuelta en tres lugares.

Toma un calculo del caso, el acumulado por tarjeta, y lo resuelve con
una funcion de ventana en SQL, con pandas y con Polars. El proposito no
es declarar un ganador, sino construir el criterio para decidir donde
conviene que ocurra el calculo.

Requisitos: base pagos cargada, .env presente
    pip install "psycopg[binary]" python-dotenv sqlalchemy pandas polars
Ejecucion: python c2_s3_b3_ventanas_dataframe.py
"""

import os
import time
import warnings

import pandas as pd
import polars as pl
import psycopg
from dotenv import load_dotenv
from sqlalchemy import create_engine

warnings.filterwarnings("ignore")
load_dotenv()


def cadena():
    return (f"host={os.getenv('PGHOST', 'localhost')} "
            f"port={os.getenv('PGPORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DB')} "
            f"user={os.getenv('POSTGRES_USER')} "
            f"password={os.getenv('POSTGRES_PASSWORD')}")


def uri():
    return (f"postgresql+psycopg://{os.getenv('POSTGRES_USER')}:"
            f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('PGHOST', 'localhost')}:"
            f"{os.getenv('PGPORT', '5432')}/{os.getenv('POSTGRES_DB')}")


def titulo(texto):
    print("\n" + "=" * 70 + f"\n{texto}\n" + "=" * 70)


# =====================================================================
# Bloque 1. El acumulado, resuelto en tres lugares
# =====================================================================

SQL_ACUMULADO = """
    SELECT id_transaccion, id_tarjeta, fecha_hora, monto,
           SUM(monto) OVER (PARTITION BY id_tarjeta ORDER BY fecha_hora)
               AS acumulado
    FROM pagos.transacciones
    WHERE estatus = 'APROBADA'
    ORDER BY id_tarjeta, fecha_hora
"""

SQL_DETALLE = """
    SELECT id_transaccion, id_tarjeta, fecha_hora, monto
    FROM pagos.transacciones
    WHERE estatus = 'APROBADA'
    ORDER BY id_tarjeta, fecha_hora
"""


def bloque_1_tres_lugares():
    titulo("Bloque 1: el acumulado por tarjeta, en tres lugares")

    motor = create_engine(uri())

    # Opcion A: la ventana la calcula el motor.
    inicio = time.perf_counter()
    en_sql = pd.read_sql(SQL_ACUMULADO, motor)
    t_sql = time.perf_counter() - inicio

    # Opcion B: se trae el detalle y pandas calcula el acumulado.
    inicio = time.perf_counter()
    detalle = pd.read_sql(SQL_DETALLE, motor)
    detalle["acumulado"] = (detalle.groupby("id_tarjeta")["monto"]
                            .cumsum())
    t_pandas = time.perf_counter() - inicio

    # Opcion C: lo mismo con Polars, mediante una expresion de ventana.
    inicio = time.perf_counter()
    with psycopg.connect(cadena()) as conexion:
        detalle_pl = pl.read_database(SQL_DETALLE, conexion)
    detalle_pl = detalle_pl.with_columns(
        pl.col("monto").cum_sum().over("id_tarjeta").alias("acumulado")
    )
    t_polars = time.perf_counter() - inicio

    print(f"\n  Ventana en el motor : {t_sql:.3f} s   {en_sql.shape}")
    print(f"  cumsum en pandas    : {t_pandas:.3f} s   {detalle.shape}")
    print(f"  cum_sum en Polars   : {t_polars:.3f} s   {detalle_pl.shape}")

    # Comprobacion de que los tres coinciden.
    ultimo_sql = en_sql.groupby("id_tarjeta")["acumulado"].last()
    ultimo_pd = detalle.groupby("id_tarjeta")["acumulado"].last()
    coinciden = (ultimo_sql.round(2) == ultimo_pd.round(2)).all()
    print(f"\n  Los resultados coinciden: {'si' if coinciden else 'NO'}")

    print("""
  Advertencia sobre los tiempos: incluyen costos de arranque que se
  pagan una sola vez, como abrir la conexion o inicializar la
  biblioteca. No constituyen una medicion de desempeno y no deben
  leerse como tal. Con cinco mil filas, cualquiera de los tres caminos
  responde de inmediato.

  Los tres llevan al mismo resultado. La eleccion no es de correccion
  sino de arquitectura, y depende de tres factores:

    volumen        cuantas filas hay que mover para calcular
    reutilizacion  si el resultado alimenta un solo consumidor o varios
    naturaleza     si el calculo se expresa con comodidad en SQL
""")


# =====================================================================
# Bloque 2. Equivalencias entre SQL y los dataframes
# =====================================================================

def bloque_2_equivalencias():
    titulo("Bloque 2: equivalencias")

    print("""
  Funcion de ventana         pandas                     Polars
  -------------------------  -------------------------  ----------------------
  SUM(x) OVER (PARTITION     groupby(g)[x].transform    col(x).sum()
    BY g)                      ('sum')                    .over(g)

  SUM(x) OVER (PARTITION     groupby(g)[x].cumsum()     col(x).cum_sum()
    BY g ORDER BY f)                                      .over(g)

  ROW_NUMBER() OVER          groupby(g).cumcount() + 1  int_range()
    (PARTITION BY g                                       .over(g)
     ORDER BY f)

  RANK() OVER                groupby(g)[x].rank         col(x).rank('min')
    (PARTITION BY g            (method='min')             .over(g)
     ORDER BY x)

  LAG(x) OVER                groupby(g)[x].shift(1)     col(x).shift(1)
    (PARTITION BY g                                       .over(g)
     ORDER BY f)

  AVG(x) OVER (... ROWS      groupby(g)[x].rolling(3)   col(x)
    BETWEEN 2 PRECEDING        .mean()                    .rolling_mean(3)
    AND CURRENT ROW)                                       .over(g)

  Observacion importante sobre pandas:

    transform devuelve una serie del mismo largo que el original y
    conserva el detalle, igual que la ventana en SQL.

    agg colapsa el grupo a una fila, igual que GROUP BY.

    Confundir ambos es el error equivalente al que abre esta sesion.
""")


# =====================================================================
# Bloque 3. El caso que conviene resolver en el motor
# =====================================================================

def bloque_3_conviene_motor():
    titulo("Bloque 3: cuando conviene el motor")

    motor = create_engine(uri())

    # La pregunta produce quince filas a partir de casi cuatro mil.
    consulta = """
        WITH aprobadas AS (
            SELECT id_transaccion, id_tarjeta, monto
            FROM pagos.transacciones WHERE estatus = 'APROBADA'
        ),
        con_estadistica AS (
            SELECT *,
                   AVG(monto)    OVER (PARTITION BY id_tarjeta) AS promedio,
                   STDDEV(monto) OVER (PARTITION BY id_tarjeta) AS desviacion,
                   COUNT(*)      OVER (PARTITION BY id_tarjeta) AS operaciones
            FROM aprobadas
        )
        SELECT id_transaccion, id_tarjeta, monto,
               ROUND(promedio, 2) AS promedio_tarjeta,
               ROUND((monto - promedio) / NULLIF(desviacion, 0), 2) AS desviaciones
        FROM con_estadistica
        WHERE operaciones >= 10 AND desviacion > 0
          AND (monto - promedio) / desviacion > 3
        ORDER BY desviaciones DESC
        LIMIT 15
    """

    inicio = time.perf_counter()
    resultado = pd.read_sql(consulta, motor)
    tiempo = time.perf_counter() - inicio

    print(f"\n  Operaciones fuera del patron de su tarjeta, primeras quince:")
    print(resultado.to_string(index=False))
    print(f"\n  Filas devueltas: {len(resultado)}   Tiempo: {tiempo:.3f} s")

    print("""
  La consulta recorre casi cuatro mil operaciones y devuelve quince.
  Todo el trabajo ocurre donde viven los datos y por la red viaja solo
  el resultado.

  Advertencia sobre la interpretacion: el criterio de tres desviaciones
  identifica valores atipicos respecto del propio historial de la
  tarjeta. Es un punto de partida para revision, no una deteccion de
  fraude. En este conjunto los datos son sinteticos, de modo que los
  patrones son los que introdujo el generador.
""")


# =====================================================================
# Bloque 4. El caso que conviene resolver en el dataframe
# =====================================================================

def bloque_4_conviene_dataframe():
    titulo("Bloque 4: cuando conviene el dataframe")

    motor = create_engine(uri())
    base = pd.read_sql(SQL_DETALLE, motor)

    print(f"\n  Un solo viaje trajo {len(base)} filas.")
    print("  Sobre ellas se exploran varias variantes sin volver al motor:\n")

    inicio = time.perf_counter()
    base["acumulado"] = base.groupby("id_tarjeta")["monto"].cumsum()
    base["posicion"] = base.groupby("id_tarjeta").cumcount() + 1
    base["anterior"] = base.groupby("id_tarjeta")["monto"].shift(1)
    base["movil_3"] = (base.groupby("id_tarjeta")["monto"]
                       .transform(lambda s: s.rolling(3, min_periods=1).mean()))
    base["pct_del_total"] = (base["monto"] /
                             base.groupby("id_tarjeta")["monto"].transform("sum"))
    tiempo = time.perf_counter() - inicio

    print(base.head(6).to_string(index=False))
    print(f"\n  Cinco calculos derivados: {tiempo:.3f} s, sin tocar la base.")

    print("""
  Aqui el dataframe gana. El costo de traer los datos se pago una vez y
  cada variante nueva es gratuita en terminos de red.

  Criterio que se desprende de los bloques 3 y 4:

    Motor      cuando el resultado es mucho menor que el origen, el
               calculo se expresa en SQL, y hay un solo consumidor.

    Dataframe  cuando se exploraran muchas variantes sobre el mismo
               conjunto, o cuando el calculo no se expresa con
               comodidad en SQL.
""")


# =====================================================================
# Bloque 5. Un limite de las funciones de ventana
# =====================================================================

def bloque_5_limite():
    titulo("Bloque 5: donde no alcanza la ventana")

    print("""
  Una funcion de ventana no puede usarse en WHERE ni en HAVING, porque
  ambos se evaluan antes que SELECT, que es donde nace la ventana.

  Esto es invalido:

      SELECT ciudad, nombre, SUM(monto) AS importe
      FROM ...
      WHERE ROW_NUMBER() OVER (PARTITION BY ciudad ORDER BY ...) = 1
      GROUP BY ciudad, nombre;

  El motor responde:
      window functions are not allowed in WHERE

  La solucion es calcular la ventana en una etapa y filtrar en la
  siguiente, con una CTE o una subconsulta:

      WITH ranking AS (
          SELECT ciudad, nombre, importe,
                 ROW_NUMBER() OVER (PARTITION BY ciudad
                                    ORDER BY importe DESC) AS posicion
          FROM importe_por_comercio
      )
      SELECT * FROM ranking WHERE posicion = 1;

  Esa necesidad es la razon practica de que las CTE y las funciones de
  ventana se enseñen juntas: casi toda consulta analitica util combina
  ambas.
""")

    with psycopg.connect(cadena()) as conexion:
        conexion.autocommit = True
        try:
            conexion.execute("""
                SELECT c.ciudad, c.nombre, SUM(t.monto)
                FROM pagos.transacciones t
                JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
                JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
                WHERE ROW_NUMBER() OVER (PARTITION BY c.ciudad
                                         ORDER BY SUM(t.monto) DESC) = 1
                GROUP BY c.ciudad, c.nombre
            """).fetchall()
        except psycopg.Error as error:
            print(f"  Error real del motor: {str(error).splitlines()[0]}")


if __name__ == "__main__":
    bloque_1_tres_lugares()
    bloque_2_equivalencias()
    bloque_3_conviene_motor()
    bloque_4_conviene_dataframe()
    bloque_5_limite()
