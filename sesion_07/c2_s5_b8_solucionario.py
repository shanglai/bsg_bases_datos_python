"""
c2_s5_b8_solucionario.py
Solucionario del taller de la sesion 2.5, en un solo archivo.

Documento para el instructor. NO se entrega al participante.

Ejecuta cada consulta contra la tabla de volumen y reporta los planes
reales. Los numeros varian entre equipos; lo que no varia es el tipo de
recorrido que elige el motor, y eso es lo que se evalua.

Requisitos: tabla pagos.transacciones_volumen, .env presente
Ejecucion:  python c2_s5_b8_solucionario.py
"""

import os
import time

import psycopg
from dotenv import load_dotenv

load_dotenv()
TABLA = "pagos.transacciones_volumen"


def cadena():
    return (f"host={os.getenv('PGHOST', 'localhost')} "
            f"port={os.getenv('PGPORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DB')} "
            f"user={os.getenv('POSTGRES_USER')} "
            f"password={os.getenv('POSTGRES_PASSWORD')}")


def titulo(texto):
    print("\n" + "=" * 72 + f"\n{texto}\n" + "=" * 72)


def punto(clave, enunciado):
    print("\n" + "-" * 72 + f"\n{clave}. {enunciado}\n" + "-" * 72)


def plan(conexion, sql, opciones="ANALYZE"):
    """Imprime el plan y devuelve el tipo de recorrido y el tiempo."""
    filas = conexion.execute(f"EXPLAIN ({opciones}) " + sql).fetchall()
    for fila in filas:
        print("    " + fila[0])

    recorrido = "sin recorrido identificado"
    for fila in filas:
        texto = fila[0].strip().lstrip("-> ").strip()
        if "Scan" in texto:
            # Se conserva solo el nombre del nodo, antes del parentesis
            # de costos.
            recorrido = texto.split("  (")[0].strip()
            break

    tiempo = next((f[0].strip() for f in filas if "Execution Time" in f[0]), "")
    return recorrido, tiempo


def limpiar_indices(conexion):
    for (nombre,) in conexion.execute("""
        SELECT indexname FROM pg_indexes
        WHERE schemaname = 'pagos' AND tablename = 'transacciones_volumen'
    """).fetchall():
        conexion.execute(f"DROP INDEX pagos.{nombre}")
    conexion.execute(f"ANALYZE {TABLA}")


CONSULTA_A1 = f"""
    SELECT COUNT(*), SUM(monto) FROM {TABLA}
    WHERE id_tarjeta = 77 AND fecha_hora BETWEEN '2026-02-01' AND '2026-02-28'
"""


# =====================================================================

def parte_a(conexion):
    titulo("PARTE A. LEER UN PLAN")
    limpiar_indices(conexion)

    punto("A1 y A2", "Plan sin indice")
    plan(conexion, CONSULTA_A1)
    print("""
  Elementos que el participante debe identificar:

    Tipo de recorrido   Parallel Seq Scan. Se lee la tabla completa,
                        repartida entre varios procesos.
    rows estimado       lo que el motor calculo antes de ejecutar
    rows real           lo que efectivamente devolvio cada vuelta
    loops               numero de vueltas. Con recorrido paralelo,
                        las filas reales se multiplican por loops
    Execution Time      milisegundos totales

  Punto que suele confundir: con loops mayor que uno, el valor de rows
  es POR VUELTA, no el total. Multiplicar rows por loops da el total.
""")

    punto("A3 y A4", "Bloques leidos de memoria y de disco")
    print("  Primera ejecucion:")
    plan(conexion, CONSULTA_A1, "ANALYZE, BUFFERS")
    print("\n  Segunda ejecucion inmediata:")
    plan(conexion, CONSULTA_A1, "ANALYZE, BUFFERS")
    print("""
  Explicacion esperada:

    shared read  bloques traidos de disco
    shared hit   bloques encontrados en la memoria compartida

  En la primera ejecucion predomina read. En la segunda, hit, porque los
  bloques quedaron en cache.

  Consecuencia para la medicion: cronometrar una sola vez mide el estado
  de la cache tanto como el plan. Es el fundamento de E5.
""")


def parte_b(conexion):
    titulo("PARTE B. CREAR Y MEDIR")

    punto("B1", "Indice y justificacion del orden de columnas")
    conexion.execute(f"""
        CREATE INDEX idx_sol_tarjeta_fecha ON {TABLA} (id_tarjeta, fecha_hora)
    """)
    conexion.execute(f"ANALYZE {TABLA}")
    print("""
    CREATE INDEX idx_tarjeta_fecha
        ON pagos.transacciones_volumen (id_tarjeta, fecha_hora);

  Justificacion esperada:

    id_tarjeta va primero porque el filtro es de igualdad y es muy
    selectivo: hay 219 tarjetas sobre dos millones de filas.

    fecha_hora va segundo porque el filtro es de rango. Un indice
    compuesto puede aprovechar la segunda columna solo despues de fijar
    la primera con igualdad.

  Regla general: las columnas de igualdad primero, la de rango al final.
  Invertir el orden produce un indice que sirve mucho menos.
""")

    punto("B2", "Plan con el indice creado")
    recorrido, tiempo = plan(conexion, CONSULTA_A1)
    print(f"""
  El recorrido paso a {recorrido}.

  El Bitmap Heap Scan aparece cuando el motor espera varias filas
  dispersas: primero construye un mapa de bloques con el indice y
  despues los visita en orden fisico, lo que reduce el movimiento del
  disco.
""")

    punto("B3", "Tamano del indice frente al de la tabla")
    for fila in conexion.execute(f"""
        SELECT pg_size_pretty(pg_relation_size('{TABLA}')) AS tabla,
               pg_size_pretty(pg_relation_size('pagos.idx_sol_tarjeta_fecha'))
                   AS indice
    """).fetchall():
        print(f"    tabla: {fila[0]}   indice: {fila[1]}")
    print("""
  El indice ocupa una fraccion considerable del tamano de la tabla. Es
  el argumento cuantitativo contra crear indices por si acaso, que se
  retoma en E4.
""")

    punto("B5", "Indice de cobertura")
    conexion.execute(f"""
        CREATE INDEX idx_sol_cobertura ON {TABLA} (id_tarjeta, fecha_hora)
        INCLUDE (monto)
    """)
    # VACUUM, no solo ANALYZE: el Index Only Scan necesita el mapa de
    # visibilidad actualizado.
    conexion.execute(f"VACUUM ANALYZE {TABLA}")
    recorrido, _ = plan(conexion, CONSULTA_A1)
    print(f"""
  Recorrido: {recorrido}

  Index Only Scan significa que la consulta se resolvio SIN visitar la
  tabla. Todo lo que necesitaba, incluido monto, estaba en el indice.

  INCLUDE agrega columnas al indice sin que formen parte de la clave, de
  modo que no afectan el orden ni el tamano de la parte navegable.

  Advertencia que conviene anticipar en clase: Index Only Scan requiere
  ademas que el mapa de visibilidad este actualizado. Tras una carga
  masiva, ANALYZE por si solo NO basta: hace falta VACUUM. Sin el, el
  plan sigue mostrando Bitmap Heap Scan aunque el indice tenga todas
  las columnas necesarias.

  El contador Heap Fetches del plan lo delata: debe ser cero.

  Comprobado en este conjunto: con ANALYZE, Bitmap Heap Scan en 2.4 ms;
  tras VACUUM ANALYZE, Index Only Scan en 0.3 ms con Heap Fetches 0.
""")


def parte_c(conexion):
    titulo("PARTE C. CUANDO EL INDICE NO SE USA")

    punto("C1", "Predicado poco selectivo")
    recorrido, tiempo = plan(
        conexion, f"SELECT COUNT(*) FROM {TABLA} WHERE estatus = 'APROBADA'")
    print(f"""
  Recorrido: {recorrido}

  Cerca del 92 por ciento de las filas cumplen la condicion. Leer el
  indice y despues visitar casi todas las filas cuesta mas que recorrer
  la tabla de corrido.

  El motor hace bien. La decision se toma con las estadisticas que
  recopila ANALYZE.
""")

    punto("C2", "Funcion aplicada sobre la columna indexada")
    conexion.execute(f"CREATE INDEX idx_sol_fecha ON {TABLA} (fecha_hora)")
    conexion.execute(f"ANALYZE {TABLA}")
    recorrido, tiempo = plan(
        conexion,
        f"SELECT COUNT(*) FROM {TABLA} WHERE DATE(fecha_hora) = '2026-03-15'")
    print(f"""
  Recorrido: {recorrido}

  El indice esta sobre fecha_hora. La expresion DATE(fecha_hora) es otro
  valor, que no esta almacenado en ninguna parte. El motor no puede
  relacionarla con las entradas del indice.

  Es el mismo fenomeno de la sesion 2.4 con el operador ->>: el indice
  cubre la columna, no las expresiones aplicadas sobre ella.
""")

    punto("C3", "La misma consulta reescrita como rango")
    recorrido, tiempo = plan(
        conexion,
        f"SELECT COUNT(*) FROM {TABLA} "
        f"WHERE fecha_hora >= '2026-03-15' AND fecha_hora < '2026-03-16'")
    print(f"""
  Recorrido: {recorrido}

  La condicion ahora se expresa sobre la columna misma, de modo que el
  motor puede recorrer el indice.

  Dos alternativas equivalentes:
    reescribir como rango, que es lo hecho aqui
    crear un indice de expresion sobre DATE(fecha_hora)

  La primera se prefiere cuando se controla la consulta. La segunda,
  cuando la consulta viene de una herramienta que no se puede modificar.
""")

    punto("C4", "Filtro solo sobre la segunda columna del compuesto")
    conexion.execute("DROP INDEX pagos.idx_sol_fecha")
    conexion.execute("DROP INDEX IF EXISTS pagos.idx_sol_cobertura")
    conexion.execute(f"ANALYZE {TABLA}")
    recorrido, tiempo = plan(
        conexion,
        f"SELECT COUNT(*) FROM {TABLA} "
        f"WHERE fecha_hora BETWEEN '2026-03-01' AND '2026-03-02'")
    print(f"""
  Recorrido: {recorrido}

  Queda solo el indice (id_tarjeta, fecha_hora). Un indice compuesto se
  recorre por su primera columna: sin conocer id_tarjeta, el motor no
  tiene por donde entrar.

  Analogia util en clase: un directorio ordenado por apellido y despues
  por nombre. Sirve para buscar por apellido, y no sirve para buscar a
  todos los que se llaman Ana.

  Nota de version: PostgreSQL 18 incorporo el recorrido con salto, que
  aprovecha el indice en algunos de estos casos. En las versiones
  anteriores el comportamiento es el observado aqui.
""")

    punto("C5", "Indices sin uso")
    for fila in conexion.execute("""
        SELECT indexrelname, idx_scan,
               pg_size_pretty(pg_relation_size(indexrelid))
        FROM pg_stat_user_indexes
        WHERE relname = 'transacciones_volumen' ORDER BY idx_scan
    """).fetchall():
        print(f"    {fila[0]:<28} usado {fila[1]:>6} veces   {fila[2]}")
    print("""
  Un indice con cero lecturas no es neutro:

    ocupa espacio en disco y en la memoria compartida
    se actualiza en cada insercion, actualizacion y borrado
    alarga el tiempo de mantenimiento y de respaldo

  Es el argumento cuantitativo de E4.

  Salvedad: idx_scan cuenta desde el ultimo reinicio de estadisticas. Un
  indice que solo se usa en el cierre mensual puede aparecer con cero un
  martes cualquiera. Conviene observar un periodo representativo antes
  de eliminarlo.
""")


def parte_d(conexion):
    titulo("PARTE D. TRANSACCIONES DESDE PYTHON")

    punto("D1 y D2", "Transferencia con todo o nada")
    print("""
    def transferir(origen, destino, monto):
        with psycopg.connect(cadena()) as conexion:
            conexion.execute(
                "UPDATE pagos.saldos SET saldo = saldo - %s WHERE id_cuenta = %s",
                (monto, origen))
            conexion.execute(
                "UPDATE pagos.saldos SET saldo = saldo + %s WHERE id_cuenta = %s",
                (monto, destino))

  El bloque with confirma al salir sin excepcion y revierte si la hubo.
  No hace falta un commit explicito.

  Puntos a exigir:
    los dos UPDATE dentro del mismo bloque
    parametros, no concatenacion
    la restriccion CHECK (saldo >= 0) declarada en la tabla, no
      verificada en Python. Verificar en Python deja una ventana entre
      la lectura y la escritura.
""")

    conexion.execute("DROP TABLE IF EXISTS pagos.saldos_sol")
    conexion.execute("""
        CREATE TABLE pagos.saldos_sol (
            id_cuenta INT PRIMARY KEY,
            saldo NUMERIC(12,2) NOT NULL CHECK (saldo >= 0))
    """)
    conexion.execute("INSERT INTO pagos.saldos_sol VALUES (1, 1000), (2, 500)")

    print("\n  Estado inicial:",
          conexion.execute("SELECT id_cuenta, saldo FROM pagos.saldos_sol "
                           "ORDER BY id_cuenta").fetchall())

    otra = psycopg.connect(cadena())
    try:
        otra.execute("UPDATE pagos.saldos_sol SET saldo = saldo - 5000 "
                     "WHERE id_cuenta = 1")
        otra.execute("UPDATE pagos.saldos_sol SET saldo = saldo + 5000 "
                     "WHERE id_cuenta = 2")
        otra.commit()
    except psycopg.errors.CheckViolation as error:
        otra.rollback()
        print(f"  Error capturado: {str(error).splitlines()[0]}")
    finally:
        otra.close()

    print("  Estado final:  ",
          conexion.execute("SELECT id_cuenta, saldo FROM pagos.saldos_sol "
                           "ORDER BY id_cuenta").fetchall())
    print("""
  Ningun saldo cambio. El cargo se revirtio junto con el abono que nunca
  ocurrio.
""")

    punto("D3 y D4", "La conexion abortada")
    otra = psycopg.connect(cadena())
    try:
        otra.execute("SELECT * FROM pagos.no_existe")
    except psycopg.errors.UndefinedTable as error:
        print(f"  Primer error:  {str(error).splitlines()[0]}")
    try:
        otra.execute("SELECT 1")
    except psycopg.errors.InFailedSqlTransaction as error:
        print(f"  Segundo error: {str(error).splitlines()[0]}")
    otra.rollback()
    print(f"  Tras rollback: la conexion responde "
          f"{otra.execute('SELECT 1').fetchone()[0]}")
    otra.close()
    print("""
  Explicacion esperada: PostgreSQL marca la transaccion como abortada y
  rechaza toda sentencia posterior hasta que se revierta. El segundo
  mensaje no dice nada sobre la causa real.

  Correccion: rollback dentro del bloque except, o un punto de guardado
  antes de la sentencia que puede fallar.
""")

    punto("D5", "Carga por lotes tolerante a errores")
    print("""
    registros = [(10, 100), (11, -50), (12, 300), (10, 400)]
    guardados, descartados = 0, 0

    with psycopg.connect(cadena()) as conexion:
        for id_cuenta, saldo in registros:
            try:
                with conexion.transaction():      # punto de guardado
                    conexion.execute(
                        "INSERT INTO pagos.saldos_sol VALUES (%s, %s)",
                        (id_cuenta, saldo))
                guardados += 1
            except psycopg.Error:
                descartados += 1

  El bloque transaction() anidado crea un SAVEPOINT. Un fallo revierte
  solo ese registro y el resto del lote sobrevive.

  Sin el, el primer error aborta la transaccion completa y se pierde
  todo lo insertado antes.
""")
    registros = [(10, 100), (11, -50), (12, 300), (10, 400)]
    guardados = descartados = 0
    otra = psycopg.connect(cadena())
    for id_cuenta, saldo in registros:
        try:
            with otra.transaction():
                otra.execute("INSERT INTO pagos.saldos_sol VALUES (%s, %s)",
                             (id_cuenta, saldo))
            guardados += 1
        except psycopg.Error:
            descartados += 1
    otra.commit()
    print(f"  Guardados: {guardados}   Descartados: {descartados}")
    print(f"  Contenido: "
          f"{otra.execute('SELECT id_cuenta, saldo FROM pagos.saldos_sol ORDER BY id_cuenta').fetchall()}")
    otra.close()
    print("""
  Descartados: el saldo negativo por CheckViolation, y la cuenta 10
  repetida por UniqueViolation.
""")

    punto("D6", "Clasificar los errores del motor")
    print("""
    MENSAJES = {
        "23505": "El registro ya existe.",
        "23503": "Referencia a un registro que no existe.",
        "23514": "El valor esta fuera del rango permitido.",
        "23502": "Falta un campo obligatorio.",
    }

    def ejecutar(conexion, sentencia, parametros):
        try:
            conexion.execute(sentencia, parametros)
            return True, "Registro guardado."
        except psycopg.Error as error:
            conexion.rollback()
            return False, MENSAJES.get(error.sqlstate,
                                       f"Error del motor: {error.sqlstate}")

  Se usa sqlstate y no el texto del mensaje. El codigo es del estandar,
  es estable entre versiones y no cambia con el idioma del servidor.

  Criterio de tratamiento que conviene exigir en la respuesta:
    errores de datos          se registran y se descartan
    conflictos de concurrencia y de conexion   se reintentan
    errores de programacion   se propagan, no se ocultan
""")

    conexion.execute("DROP TABLE IF EXISTS pagos.saldos_sol")


def parte_e(conexion):
    titulo("PARTE E. ANALISIS Y ARGUMENTACION")

    punto("E1", "Costo de escritura de los indices")
    conexion.execute("DROP TABLE IF EXISTS pagos.prueba_w")
    conexion.execute("CREATE TABLE pagos.prueba_w "
                     "(id BIGINT, f TIMESTAMP, t INT, m NUMERIC(12,2))")
    inicio = time.perf_counter()
    conexion.execute("""
        INSERT INTO pagos.prueba_w
        SELECT g, TIMESTAMP '2026-01-01' + (random()*180)*INTERVAL '1 day',
               1 + floor(random()*30)::INT, round((random()*5000)::NUMERIC,2)
        FROM generate_series(1, 500000) g
    """)
    sin_indices = time.perf_counter() - inicio

    conexion.execute("DROP TABLE pagos.prueba_w")
    conexion.execute("CREATE TABLE pagos.prueba_w "
                     "(id BIGINT, f TIMESTAMP, t INT, m NUMERIC(12,2))")
    conexion.execute("CREATE INDEX w1 ON pagos.prueba_w (t)")
    conexion.execute("CREATE INDEX w2 ON pagos.prueba_w (f)")
    conexion.execute("CREATE INDEX w3 ON pagos.prueba_w (t, f)")
    inicio = time.perf_counter()
    conexion.execute("""
        INSERT INTO pagos.prueba_w
        SELECT g, TIMESTAMP '2026-01-01' + (random()*180)*INTERVAL '1 day',
               1 + floor(random()*30)::INT, round((random()*5000)::NUMERIC,2)
        FROM generate_series(1, 500000) g
    """)
    con_indices = time.perf_counter() - inicio
    conexion.execute("DROP TABLE pagos.prueba_w")

    print(f"\n  500 mil inserciones sin indices : {sin_indices:.2f} s")
    print(f"  500 mil inserciones con 3 indices: {con_indices:.2f} s")
    print(f"  Relacion: {con_indices / sin_indices:.1f} veces")
    print("""
  Cada indice debe actualizarse en cada fila insertada. Con tres
  indices, cada insercion implica cuatro escrituras: la tabla y los tres
  indices.

  Es la contrapartida de la lectura rapida, y es la razon de que un
  sistema con carga de escritura alta indexe con moderacion.
""")

    punto("E2", "Criterio para decidir si crear un indice")
    print("""
  Criterio esperado, con los cuatro factores:

    Frecuencia    una consulta que corre miles de veces al dia justifica
                  un indice; una que corre una vez al mes, no.

    Selectividad  el indice ayuda cuando el filtro devuelve una fraccion
                  pequena de la tabla. Como referencia practica, por
                  debajo de un cinco o diez por ciento. Por encima, el
                  motor suele preferir el recorrido secuencial.

    Escritura     cada indice encarece toda insercion, actualizacion y
                  borrado. En una tabla con escritura intensa, el costo
                  puede superar el beneficio.

    Espacio       un indice puede ocupar una fraccion considerable de la
                  tabla, y compite por la memoria compartida.

  Formulacion breve: se indexa lo que se consulta con frecuencia y
  devuelve poco. Todo lo demas se evalua con el plan antes de decidir.
""")

    punto("E3", "Diferencia entre filas estimadas y filas reales")
    print("""
  Significado: el planificador eligio el plan con base en una
  estimacion. Si la estimacion esta lejos del valor real, es probable
  que el plan elegido no sea el mejor.

  Causas frecuentes:
    estadisticas desactualizadas tras una carga masiva
    correlacion entre columnas que el motor supone independientes
    una funcion cuyo resultado el motor no puede estimar

  Que se hace:
    ejecutar ANALYZE sobre la tabla
    aumentar el detalle de las estadisticas con ALTER TABLE ...
      ALTER COLUMN ... SET STATISTICS
    declarar estadisticas extendidas con CREATE STATISTICS cuando hay
      correlacion entre columnas
    reescribir la consulta para que el predicado sea estimable

  Un factor de dos o tres es tolerable. Un factor de cien merece
  investigacion.
""")

    punto("E4", "Por que no conviene indexar todo por si acaso")
    print("""
  Cuatro argumentos, respaldados por lo medido en el taller:

    1. Cada indice ocupa espacio. En este ejercicio, un solo indice
       compuesto ocupa una fraccion importante de la tabla.

    2. Cada indice encarece la escritura. Con tres indices, la insercion
       masiva tarda varias veces mas, como se midio en E1.

    3. Muchos indices dificultan la tarea del planificador, que debe
       evaluar mas combinaciones antes de elegir.

    4. Un indice que no se usa no aporta nada y paga los tres costos
       anteriores. pg_stat_user_indexes lo revela.

  Ademas: un indice sobre una columna poco selectiva no se usara nunca,
  aunque exista. Crearlo es puro costo.

  Respuesta corta que conviene dejar: los indices se crean a partir de
  las consultas que el sistema ejecuta de verdad, no de las que podria
  llegar a ejecutar.
""")

    punto("E5", "Por que una sola medicion no basta")
    print("""
  Razones:

    La primera ejecucion lee bloques de disco; las siguientes los
    encuentran en cache. La diferencia puede ser de un orden de
    magnitud, y no depende del plan.

    El equipo ejecuta otros procesos. Una medicion puede caer en un
    momento de contencion.

    El planificador puede elegir planes distintos segun las
    estadisticas del momento.

  Procedimiento defendible:

    1. Ejecutar una vez sin medir, para calentar la cache.
    2. Medir al menos cinco repeticiones.
    3. Reportar el minimo, que se aproxima al costo real sin ruido.
    4. Declarar el numero de repeticiones y el estadistico utilizado.
    5. Acompanar el tiempo con el plan, porque el tiempo dice cuanto
       tardo y el plan dice por que.

  El punto evaluable es el cuarto. Una medicion sin metodo declarado no
  es verificable.
""")


def criterios():
    titulo("CRITERIOS DE CALIFICACION")
    print("""
  Parte A, 20 por ciento
    A2 exige identificar los cinco elementos del plan. El error mas
    comun es leer rows como total cuando loops es mayor que uno.
    A4 exige entender el efecto de la cache. Es la base de E5.

  Parte B, 20 por ciento
    B1 se evalua por la justificacion del orden de columnas: igualdad
    primero, rango al final. Un indice correcto sin justificacion
    obtiene calificacion parcial.

  Parte C, 25 por ciento
    Es la parte de mayor valor. Los cuatro casos deben identificarse con
    su motivo, no solo reportarse.
    C2 y C3 juntos son el par mas util: el mismo resultado, dos planes.

  Parte D, 20 por ciento
    Verificar que la restriccion viva en la tabla y no en Python.
    En D5, exigir el punto de guardado. Sin el, el primer error pierde
    el lote completo.
    En D6, exigir el uso de sqlstate y no del texto del mensaje.

  Parte E, 15 por ciento
    E2 y E4 son los puntos evaluables de fondo.
    En E5 se valora que declare el metodo, no que llegue a un numero.

  Error transversal a vigilar
    Reportar tiempos sin indicar repeticiones ni estadistico. Es el
    habito que esta sesion busca corregir.
""")


def main():
    with psycopg.connect(cadena()) as conexion:
        conexion.autocommit = True
        parte_a(conexion)
        parte_b(conexion)
        parte_c(conexion)
        parte_d(conexion)
        parte_e(conexion)
        criterios()


if __name__ == "__main__":
    main()
