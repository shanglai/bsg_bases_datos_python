"""
c2_s2_b7_solucionario.py
Solucionario del taller de la sesion 2.2, en un solo archivo.

Documento para el instructor. NO se entrega al participante.

Resuelve las partes A a F del taller c2_s2_b4_taller.md, ejecuta cada
consulta contra la base y contrasta el resultado obtenido.

Requisitos: base pagos cargada, archivo .env presente
Ejecucion:  python c2_s2_b7_solucionario.py
"""

import os
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
    print("\n" + "=" * 72 + f"\n{texto}\n" + "=" * 72)


def punto(clave, enunciado):
    print("\n" + "-" * 72)
    print(f"{clave}. {enunciado}")
    print("-" * 72)


def correr(conexion, sql, limite=8):
    """Ejecuta y muestra un resumen del resultado."""
    filas = conexion.execute(sql).fetchall()
    columnas = [d.name for d in conexion.cursor().description] if False else None
    for fila in filas[:limite]:
        print("   ", "  ".join(str(v) for v in fila))
    if len(filas) > limite:
        print(f"    ... {len(filas) - limite} filas mas")
    print(f"    [{len(filas)} filas]")
    return filas


# =====================================================================
# PARTE A. COMBINACIONES
# =====================================================================

A1 = """
SELECT t.id_transaccion, t.fecha_hora, c.nombre, c.ciudad, t.monto
FROM pagos.transacciones t
JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
WHERE t.estatus = 'APROBADA'
ORDER BY t.monto DESC
LIMIT 20
"""

A2 = """
SELECT c.nombre AS comercio, te.codigo AS terminal, COUNT(t.id_transaccion) AS operaciones
FROM pagos.terminales te
JOIN pagos.comercios c ON c.id_comercio = te.id_comercio
LEFT JOIN pagos.transacciones t ON t.id_terminal = te.id_terminal
GROUP BY c.nombre, te.codigo
ORDER BY operaciones DESC
"""

A3 = """
SELECT cl.nombre AS cliente, c.nombre AS comercio, t.monto
FROM pagos.contracargos cc
JOIN pagos.transacciones t ON t.id_transaccion = cc.id_transaccion
JOIN pagos.terminales te   ON te.id_terminal   = t.id_terminal
JOIN pagos.comercios  c    ON c.id_comercio    = te.id_comercio
JOIN pagos.tarjetas   ta   ON ta.id_tarjeta    = t.id_tarjeta
JOIN pagos.clientes   cl   ON cl.id_cliente    = ta.id_cliente
ORDER BY t.monto DESC
"""

A4 = """
SELECT COUNT(*) AS clientes_sin_rechazo
FROM pagos.clientes cl
WHERE NOT EXISTS (
    SELECT 1
    FROM pagos.tarjetas ta
    JOIN pagos.transacciones t ON t.id_tarjeta = ta.id_tarjeta
    WHERE ta.id_cliente = cl.id_cliente
      AND t.estatus = 'RECHAZADA'
)
"""


def parte_a(conexion):
    titulo("PARTE A. COMBINACIONES")

    punto("A1", "Veinte operaciones de mayor monto aprobado")
    correr(conexion, A1, limite=5)

    punto("A2", "Operaciones por terminal")
    print("""
  Nota de diseno: se usa LEFT JOIN desde terminales. Con INNER JOIN, una
  terminal sin operaciones desapareceria del resultado en lugar de
  aparecer con cero. Se usa COUNT(t.id_transaccion) y no COUNT(*),
  porque el segundo contaria la fila nula que produce el LEFT.
""")
    correr(conexion, A2, limite=5)

    punto("A3", "Operaciones con contracargo")
    print("""
  Nota de diseno: conviene partir de contracargos, que es la tabla mas
  pequena, y combinar hacia afuera. El resultado es identico partiendo
  de transacciones con INNER JOIN, pero la intencion se lee mejor asi.
""")
    correr(conexion, A3, limite=5)

    punto("A4", "Clientes sin ninguna operacion rechazada")
    correr(conexion, A4)
    print("""
  Solucion alternativa con combinacion externa:

    SELECT COUNT(*) FROM (
        SELECT cl.id_cliente
        FROM pagos.clientes cl
        JOIN pagos.tarjetas ta ON ta.id_cliente = cl.id_cliente
        JOIN pagos.transacciones t ON t.id_tarjeta = ta.id_tarjeta
        GROUP BY cl.id_cliente
        HAVING COUNT(*) FILTER (WHERE t.estatus = 'RECHAZADA') = 0
    ) x;

  Diferencia importante: esta version excluye a los clientes que no
  tienen ninguna operacion, mientras que NOT EXISTS los incluye. Ambas
  son defendibles; el participante debe declarar cual interpreto.
""")

    punto("A5", "Filtro en WHERE frente a filtro en ON")
    r1 = conexion.execute("""
        SELECT COUNT(*) FROM pagos.transacciones t
        LEFT JOIN pagos.contracargos cc ON cc.id_transaccion = t.id_transaccion
        WHERE cc.id_contracargo IS NULL
    """).fetchone()[0]
    r2 = conexion.execute("""
        SELECT COUNT(*) FROM pagos.transacciones t
        LEFT JOIN pagos.contracargos cc
               ON cc.id_transaccion = t.id_transaccion
              AND cc.id_contracargo IS NULL
    """).fetchone()[0]
    print(f"\n  Filtro en WHERE: {r1}")
    print(f"  Filtro en ON:    {r2}")
    print("""
  Explicacion:

    La condicion en ON se aplica MIENTRAS se arma la combinacion. Una
    fila de contracargos que no la cumpla simplemente no se empareja, y
    la transaccion sobrevive con nulos. El resultado conserva las 5000
    filas.

    La condicion en WHERE se aplica DESPUES de armada la combinacion, de
    modo que descarta filas del resultado. Devuelve solo las
    transacciones que quedaron sin pareja.

  Regla practica: en una combinacion externa, la condicion sobre la
  tabla del lado opcional va en ON. Ponerla en WHERE convierte el LEFT
  JOIN en un INNER JOIN de hecho.
""")


# =====================================================================
# PARTE B. AGREGACIONES
# =====================================================================

B1 = """
SELECT c.ciudad, t.metodo_captura, COUNT(*) AS operaciones, SUM(t.monto) AS importe
FROM pagos.transacciones t
JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
WHERE t.estatus = 'APROBADA'
GROUP BY c.ciudad, t.metodo_captura
ORDER BY importe DESC
"""

B2 = """
SELECT ta.marca,
       COUNT(*)                                            AS total,
       COUNT(*) FILTER (WHERE t.estatus = 'RECHAZADA')     AS rechazadas,
       ROUND(100.0 * COUNT(*) FILTER (WHERE t.estatus = 'RECHAZADA')
             / COUNT(*), 2)                                AS pct_rechazo
FROM pagos.transacciones t
JOIN pagos.tarjetas ta ON ta.id_tarjeta = t.id_tarjeta
GROUP BY ta.marca
ORDER BY pct_rechazo DESC
"""

B3 = """
SELECT c.nombre,
       COUNT(*)               AS operaciones,
       ROUND(AVG(t.monto), 2) AS ticket_promedio
FROM pagos.transacciones t
JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
WHERE t.estatus = 'APROBADA'
GROUP BY c.nombre
HAVING AVG(t.monto) > 1000 AND COUNT(*) > 300
ORDER BY ticket_promedio DESC
"""

B4 = """
SELECT DATE_TRUNC('month', t.fecha_hora)::DATE AS mes,
       COUNT(*)     AS operaciones,
       SUM(t.monto) AS importe
FROM pagos.transacciones t
WHERE t.estatus = 'APROBADA'
GROUP BY mes
ORDER BY mes
"""


def parte_b(conexion):
    titulo("PARTE B. AGREGACIONES")

    punto("B1", "Importe por ciudad y metodo de captura")
    correr(conexion, B1, limite=6)

    punto("B2", "Tasa de rechazo por marca, en una sola pasada")
    correr(conexion, B2)
    print("""
  La clausula FILTER es la forma del estandar. La alternativa portable es
  SUM(CASE WHEN ... THEN 1 ELSE 0 END), equivalente en resultado y algo
  menos legible.

  Punto a exigir: una sola pasada. Resolverlo con dos consultas y
  dividir en Python resuelve el numero pero no el ejercicio.
""")

    punto("B3", "Comercios con ticket alto y volumen alto")
    correr(conexion, B3)
    print("""
  Ambas condiciones van en HAVING porque ambas se evaluan sobre el grupo
  ya agregado. Ninguna puede ir en WHERE.
""")

    punto("B4", "Importe aprobado por mes")
    correr(conexion, B4)
    print("""
  DATE_TRUNC opera sobre el tipo TIMESTAMP declarado en la sesion 2.1.
  Si la columna fuera texto, como en SQLite, habria que recurrir a
  manipulacion de cadenas y el resultado no ordenaria de forma correcta
  al cruzar de ano.
""")

    punto("B5", "Por que falla la consulta con SUM en WHERE")
    print("""
  Falla porque WHERE se evalua ANTES que GROUP BY. En ese momento los
  grupos todavia no existen, de modo que SUM no puede calcularse.

  El motor lo reporta como:
    aggregate functions are not allowed in WHERE

  Correccion: la condicion sobre el agregado va en HAVING.

    SELECT c.nombre, SUM(t.monto) AS importe
    FROM pagos.transacciones t
    JOIN pagos.terminales te USING (id_terminal)
    JOIN pagos.comercios  c  USING (id_comercio)
    GROUP BY c.nombre
    HAVING SUM(t.monto) > 1000000;

  Detalle adicional: tampoco funciona HAVING importe > 1000000, porque
  el alias nace en SELECT, que se evalua despues de HAVING. Hay que
  repetir la expresion completa.
""")
    try:
        conexion.execute("""
            SELECT c.nombre, SUM(t.monto) FROM pagos.transacciones t
            JOIN pagos.terminales te USING (id_terminal)
            JOIN pagos.comercios c USING (id_comercio)
            WHERE SUM(t.monto) > 1000000 GROUP BY c.nombre
        """).fetchall()
    except psycopg.errors.GroupingError as error:
        print(f"  Error real del motor: {str(error).splitlines()[0]}")
        conexion.rollback()
    correr(conexion, """
        SELECT c.nombre, SUM(t.monto) AS importe
        FROM pagos.transacciones t
        JOIN pagos.terminales te USING (id_terminal)
        JOIN pagos.comercios  c  USING (id_comercio)
        GROUP BY c.nombre HAVING SUM(t.monto) > 1000000
        ORDER BY importe DESC
    """)


# =====================================================================
# PARTE C. SUBCONSULTAS
# =====================================================================

def parte_c(conexion):
    titulo("PARTE C. SUBCONSULTAS")

    punto("C1", "Operaciones que superan el triple del ticket promedio")
    correr(conexion, """
        SELECT id_transaccion, monto
        FROM pagos.transacciones
        WHERE estatus = 'APROBADA'
          AND monto > 3 * (SELECT AVG(monto) FROM pagos.transacciones
                           WHERE estatus = 'APROBADA')
        ORDER BY monto DESC
    """, limite=5)

    punto("C2", "Comercios con al menos cuatro terminales, con IN")
    correr(conexion, """
        SELECT nombre, ciudad FROM pagos.comercios
        WHERE id_comercio IN (
            SELECT id_comercio FROM pagos.terminales
            GROUP BY id_comercio HAVING COUNT(*) >= 4
        ) ORDER BY nombre
    """)

    punto("C3", "El mismo resultado con EXISTS")
    correr(conexion, """
        SELECT c.nombre, c.ciudad FROM pagos.comercios c
        WHERE EXISTS (
            SELECT 1 FROM pagos.terminales te
            WHERE te.id_comercio = c.id_comercio
            GROUP BY te.id_comercio HAVING COUNT(*) >= 4
        ) ORDER BY c.nombre
    """)
    print("""
  Comparacion:

    IN conviene cuando la subconsulta produce una lista pequena y
    estable, y cuando esa lista es independiente de la fila externa.

    EXISTS conviene cuando la condicion depende de la fila externa y
    cuando basta con saber si existe al menos una coincidencia. El motor
    puede detenerse en el primer acierto.

    Diferencia que importa: si la subconsulta de IN devuelve algun nulo,
    NOT IN deja de comportarse como se espera y no devuelve filas.
    NOT EXISTS no tiene ese problema. Es la razon principal para
    preferir EXISTS en las negaciones.

  Los planificadores modernos suelen reescribir ambas formas al mismo
  plan, de modo que la eleccion es de legibilidad y de correccion ante
  nulos, no de rendimiento.
""")

    punto("C4", "Promedio por ciudad del importe de sus comercios")
    correr(conexion, """
        SELECT ciudad, ROUND(AVG(importe), 2) AS promedio_por_comercio,
               COUNT(*) AS comercios
        FROM (
            SELECT c.ciudad, c.nombre, SUM(t.monto) AS importe
            FROM pagos.transacciones t
            JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
            JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
            WHERE t.estatus = 'APROBADA'
            GROUP BY c.ciudad, c.nombre
        ) AS por_comercio
        GROUP BY ciudad ORDER BY promedio_por_comercio DESC
    """)
    print("""
  Dos etapas de agregacion. La interna produce una fila por comercio; la
  externa promedia sobre esas filas.

  Error frecuente: intentar AVG(SUM(...)) en una sola consulta. El motor
  lo rechaza porque no se pueden anidar funciones de agregacion.
""")

    punto("C5", "Monto maximo de cada comercio con su operacion")
    print("""
  Por que no funciona SELECT c.nombre, MAX(t.monto), t.id_transaccion:

    Al agrupar por comercio, cada grupo contiene muchas transacciones.
    MAX colapsa la columna monto a un solo valor, pero id_transaccion no
    tiene forma de colapsarse: el motor no sabe cual de las filas del
    grupo deberia mostrar. PostgreSQL lo rechaza con el mensaje
    'column must appear in the GROUP BY clause or be used in an
    aggregate function'.

    Agregar id_transaccion al GROUP BY tampoco sirve: cada grupo pasaria
    a tener una sola fila y MAX dejaria de significar nada.

  Solucion con subconsulta:
""")
    correr(conexion, """
        SELECT c.nombre, t.id_transaccion, t.monto
        FROM pagos.transacciones t
        JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
        JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
        WHERE t.monto = (
            SELECT MAX(t2.monto)
            FROM pagos.transacciones t2
            JOIN pagos.terminales te2 ON te2.id_terminal = t2.id_terminal
            WHERE te2.id_comercio = c.id_comercio
        )
        ORDER BY t.monto DESC
    """)
    print("""
  Solucion con DISTINCT ON, propia de PostgreSQL, mas corta y mas rapida:

    SELECT DISTINCT ON (c.id_comercio) c.nombre, t.id_transaccion, t.monto
    FROM pagos.transacciones t
    JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
    JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
    ORDER BY c.id_comercio, t.monto DESC;

  En la sesion 2.3 este mismo problema se resuelve con ROW_NUMBER, que
  es la forma del estandar y la que conviene conocer.
""")


# =====================================================================
# PARTE D. LECTURA HACIA DATAFRAMES
# =====================================================================

def parte_d(conexion):
    titulo("PARTE D. LECTURA HACIA DATAFRAMES")

    punto("D1", "Construccion del motor de SQLAlchemy")
    print("""
    def motor():
        return create_engine(
            f"postgresql+psycopg://{os.getenv('POSTGRES_USER')}:"
            f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('PGHOST')}:"
            f"{os.getenv('PGPORT')}/{os.getenv('POSTGRES_DB')}"
        )

  Punto a exigir: el prefijo postgresql+psycopg. Con postgresql:// a
  secas, SQLAlchemy 2.0 busca psycopg2 y el error menciona un modulo
  que el codigo nunca nombro.
""")

    motor = create_engine(uri())

    punto("D2", "El mismo resultado en pandas y en Polars")
    df_pd = pd.read_sql(B1, motor)
    with psycopg.connect(cadena()) as cn:
        df_pl = pl.read_database(B1, cn)
    print(f"\n  pandas  {df_pd.shape}  importe: {df_pd['importe'].dtype}")
    print(f"  polars  {df_pl.shape}  importe: {df_pl['importe'].dtype}")

    punto("D3", "La suma en el motor frente a la suma en pandas")
    exacta = conexion.execute("SELECT SUM(monto) FROM pagos.transacciones").fetchone()[0]
    montos = pd.read_sql("SELECT monto FROM pagos.transacciones", motor)
    suma = float(montos["monto"].sum())
    print(f"\n  Motor  : {exacta}   ({type(exacta).__name__})")
    print(f"  pandas : {suma}   ({montos['monto'].dtype})")
    print(f"  pandas con veinte decimales: {suma:.20f}")
    print("""
  Lectura correcta del resultado: los dos valores coinciden al
  redondear a dos decimales. La representacion interna de pandas, en
  cambio, ya no es exacta.

  Conviene no exagerar el hallazgo. Con cinco mil filas no hay error
  visible. Lo que se perdio es la GARANTIA, no todavia la exactitud.
""")

    punto("D4", "Lectura parametrizada")
    print("""
    def resumen_por_ciudad(ciudad):
        consulta = \"\"\"
            SELECT c.nombre, COUNT(*) AS operaciones, SUM(t.monto) AS importe
            FROM pagos.transacciones t
            JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
            JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
            WHERE c.ciudad = %(ciudad)s AND t.estatus = 'APROBADA'
            GROUP BY c.nombre ORDER BY importe DESC
        \"\"\"
        with psycopg.connect(cadena()) as cn:
            return pd.read_sql(consulta, cn, params={"ciudad": ciudad})
""")
    with psycopg.connect(cadena()) as cn:
        salida = pd.read_sql("""
            SELECT c.nombre, COUNT(*) AS operaciones, SUM(t.monto) AS importe
            FROM pagos.transacciones t
            JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
            JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
            WHERE c.ciudad = %(ciudad)s AND t.estatus = 'APROBADA'
            GROUP BY c.nombre ORDER BY importe DESC
        """, cn, params={"ciudad": "Ciudad de Mexico"})
    print(salida.to_string(index=False))

    punto("D5", "Materializar el resultado en una tabla")
    premium = pd.read_sql(B3, motor)
    premium.to_sql("comercios_premium", motor, schema="pagos",
                   if_exists="replace", index=False)
    print(f"\n  Escritas {len(premium)} filas en pagos.comercios_premium")
    estructura = conexion.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'pagos' AND table_name = 'comercios_premium'
        ORDER BY ordinal_position
    """).fetchall()
    print("\n  Estructura que creo pandas:")
    for columna, tipo, nulo in estructura:
        print(f"    {columna:<20} {tipo:<20} nulo: {nulo}")


# =====================================================================
# PARTE E. ANALISIS Y ARGUMENTACION
# =====================================================================

def parte_e():
    titulo("PARTE E. ANALISIS Y ARGUMENTACION")

    punto("E1", "Que pasa con la garantia de NUMERIC")
    print("""
  Respuesta esperada:

    La decision de la sesion 2.1 protege la aritmetica DENTRO del motor.
    Toda suma, promedio o comparacion que ocurra en SQL usa aritmetica
    decimal exacta.

    Al leer con pandas, la columna se convierte a punto flotante de 64
    bits. A partir de ese punto, cualquier operacion aritmetica que
    ocurra en el dataframe carece de esa garantia.

    Con cinco mil filas la diferencia no se manifiesta al redondear a
    dos decimales. Con volumenes mayores, o con operaciones encadenadas
    de multiplicacion y division, si puede manifestarse.

  Consecuencia practica, que es lo que se evalua:

    El calculo monetario que alimenta un reporte formal, una conciliacion
    o un asiento contable debe ocurrir en el motor. El dataframe recibe
    el resultado ya calculado.

    Cuando el calculo debe ocurrir en Python, conviene verificar el tipo
    despues de leer y convertir a Decimal de forma explicita, o bien usar
    una ruta de lectura que conserve el tipo decimal.

  Punto que conviene aclarar en la revision: esto no es un defecto de
  pandas. Es una decision de diseno orientada al desempeno numerico. El
  problema aparece cuando quien escribe el codigo no sabe que ocurrio.
""")

    punto("E2", "Criterio para decidir donde agregar")
    print("""
  Criterio esperado, aplicable sin medir:

    Agregar en el motor cuando
      el resultado es mucho mas pequeno que el origen
      el calculo es una agregacion que SQL expresa de forma directa
      el valor es monetario y conviene aritmetica exacta
      los datos no caben comodamente en la memoria del equipo

    Traer al dataframe cuando
      el analisis requiere operaciones que SQL no expresa con comodidad
      se van a explorar muchas variantes sobre el mismo conjunto
      el resultado alimenta un modelo, una grafica o un archivo
      el conjunto ya es pequeno tras un filtro previo

  Formulacion breve que sirve de regla: mover el calculo hacia los
  datos, no los datos hacia el calculo, salvo que el calculo no pueda
  expresarse donde viven los datos.

  Se acepta cualquier criterio equivalente que distinga por tamano
  relativo del resultado y por naturaleza de la operacion. No se acepta
  un criterio basado solo en preferencia personal por una herramienta.
""")

    punto("E3", "Diferencias de la tabla creada por to_sql")
    print("""
  Tres diferencias que el participante debe identificar:

    1. No tiene llave primaria. Ninguna columna identifica la fila.
    2. No tiene restricciones. Ni NOT NULL, ni CHECK, ni llaves foraneas.
    3. No tiene indices. Toda consulta la recorre completa.

  Diferencia adicional que vale reconocer: los tipos los dedujo pandas
  del dataframe, de modo que una columna monetaria puede haber quedado
  como double precision en lugar de NUMERIC.

  Cuando importa:
    Si la tabla es del modelo, importa mucho. Su estructura se declara
    con DDL y el motor debe proteger la integridad.

  Cuando no importa:
    Si la tabla es un resultado derivado, que se regenera por completo
    cada vez y del que nadie depende para escribir, es aceptable. Es el
    caso de comercios_premium.

  Criterio: una tabla que se reconstruye entera y solo se lee puede
  crearse asi. Una tabla que recibe escrituras o que otros objetos
  referencian, no.
""")

    punto("E4", "Punto 5 de la ficha de PostgreSQL")
    print("""
  Interfaz desde Python y lectura hacia dataframes:

    Controlador: psycopg 3, con la interfaz DB-API comun a todo motor
    relacional. Los valores variables se pasan siempre como parametros.

    Lectura: pandas.read_sql sobre un motor de SQLAlchemy declarado con
    el prefijo postgresql+psycopg, o polars.read_database sobre una
    conexion de psycopg. Polars ofrece ademas read_database_uri, mas
    rapido en volumenes altos mediante connectorx o ADBC.

    Punto de atencion: el tipo NUMERIC no cruza igual por todas las
    rutas. pandas lo convierte a punto flotante; polars sobre psycopg
    conserva el decimal. Conviene verificar el tipo despues de leer.

    Escritura: to_sql en pandas y write_database en Polars, adecuados
    para tablas de resultado, no para tablas del modelo.
""")


# =====================================================================
# PARTE F. EXTENSION
# =====================================================================

def parte_f(conexion):
    titulo("PARTE F. EJERCICIO DE EXTENSION")

    punto("F1", "Comparacion de las dos rutas de agregacion")
    print("""
  Con cinco mil filas, agregar en el motor resulta unas cuatro veces mas
  rapido que traer todo y agregar en pandas. La medicion varia entre
  equipos y no conviene presentarla como una constante.

  Proyeccion a veinte millones de filas: la ruta que trae todo deja de
  ser viable, porque el volumen transferido crece de forma lineal
  mientras el resultado agregado sigue teniendo siete filas.

  Lo que se evalua es el razonamiento sobre la proporcion, no el numero
  medido.
""")

    punto("F2", "DISTINCT ON frente a subconsulta")
    correr(conexion, """
        SELECT DISTINCT ON (c.id_comercio) c.nombre, t.id_transaccion, t.monto
        FROM pagos.transacciones t
        JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
        JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
        ORDER BY c.id_comercio, t.monto DESC
    """)
    print("""
  DISTINCT ON conserva la primera fila de cada grupo segun el ORDER BY.
  Es mas corta y evita recorrer la tabla dos veces.

  Contrapartida: es una extension propia de PostgreSQL y no existe en
  otros motores. Conviene conocerla y usarla con conciencia de que ata
  el codigo a este motor.
""")

    punto("F3", "Tipos segun la ruta de lectura")
    consulta = "SELECT monto FROM pagos.transacciones LIMIT 100"
    with psycopg.connect(cadena()) as cn:
        v1 = pl.read_database(consulta, cn)["monto"].dtype
    print(f"\n  polars.read_database sobre psycopg : {v1}")
    try:
        u = (f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
             f"@{os.getenv('PGHOST')}:{os.getenv('PGPORT')}/{os.getenv('POSTGRES_DB')}")
        v2 = pl.read_database_uri(consulta, u, engine="connectorx")["monto"].dtype
        print(f"  read_database_uri con connectorx    : {v2}")
    except Exception as error:
        print(f"  connectorx no disponible: {type(error).__name__}")
    motor = create_engine(uri())
    print(f"  pandas.read_sql                     : "
          f"{pd.read_sql(consulta, motor)['monto'].dtype}")
    print("""
  Tres rutas, tres decisiones distintas sobre el mismo tipo de origen.
  El controlador ADBC puede incluso entregar la columna como texto.

  Conclusion aplicable: verificar el tipo despues de leer. Suponerlo es
  la fuente del problema.
""")


# =====================================================================

def criterios():
    titulo("CRITERIOS DE CALIFICACION")
    print("""
  Parte A, 25 por ciento
    A5 es el punto de mayor valor. Quien no distingue entre filtrar en
    ON y filtrar en WHERE no ha entendido la combinacion externa.
    A4 admite dos interpretaciones sobre los clientes sin operaciones.
    Se acepta cualquiera si el participante la declara.

  Parte B, 25 por ciento
    B2 debe resolverse en una sola pasada. Dos consultas y una division
    en Python obtienen el numero y pierden el ejercicio.
    B5 se evalua por la explicacion del orden de evaluacion, no por la
    correccion mecanica.

  Parte C, 20 por ciento
    C5 concentra el valor. La explicacion de por que no funciona importa
    mas que la solucion. Se acepta subconsulta o DISTINCT ON.
    En C3 se valora que mencione el comportamiento de NOT IN ante nulos.

  Parte D, 15 por ciento
    Verificar el prefijo postgresql+psycopg en D1.
    Verificar el uso de params en D4. La concatenacion obtiene
    calificacion parcial aunque el resultado sea correcto.

  Parte E, 15 por ciento
    E1 y E2 son los puntos evaluables de fondo. E1 se evalua por la
    consecuencia practica que extrae, no por repetir el hallazgo.
    E2 debe producir un criterio aplicable sin medir tiempos.

  Error frecuente a vigilar en toda la entrega
    Una combinacion mal planteada multiplica filas y el conteo aumenta
    sin que nada lo advierta. Exigir que verifiquen el conteo tras cada
    combinacion nueva.
""")


def main():
    with psycopg.connect(cadena()) as conexion:
        conexion.autocommit = True
        parte_a(conexion)
        parte_b(conexion)
        parte_c(conexion)
        parte_d(conexion)
        parte_e()
        parte_f(conexion)
        criterios()


if __name__ == "__main__":
    main()
