"""
c2_s3_b7_solucionario.py
Solucionario del taller de la sesion 2.3, en un solo archivo.

Documento para el instructor. NO se entrega al participante.

Resuelve las partes A a F del taller c2_s3_b4_taller.md, ejecuta cada
consulta contra la base y comenta el resultado.

Requisitos: base pagos cargada, archivo .env presente
Ejecucion:  python c2_s3_b7_solucionario.py
"""

import os
import warnings

import psycopg
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()


def cadena():
    return (f"host={os.getenv('PGHOST', 'localhost')} "
            f"port={os.getenv('PGPORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DB')} "
            f"user={os.getenv('POSTGRES_USER')} "
            f"password={os.getenv('POSTGRES_PASSWORD')}")


def titulo(texto):
    print("\n" + "=" * 72 + f"\n{texto}\n" + "=" * 72)


def punto(clave, enunciado):
    print("\n" + "-" * 72)
    print(f"{clave}. {enunciado}")
    print("-" * 72)


def correr(conexion, sql, limite=8):
    cursor = conexion.execute(sql)
    columnas = [d.name for d in cursor.description]
    filas = cursor.fetchall()
    print("    " + "  ".join(f"{c[:16]:<16}" for c in columnas))
    for fila in filas[:limite]:
        print("    " + "  ".join(f"{str(v)[:16]:<16}" for v in fila))
    if len(filas) > limite:
        print(f"    ... {len(filas) - limite} filas mas")
    print(f"    [{len(filas)} filas]")
    return filas


# =====================================================================
# PARTE A
# =====================================================================

def parte_a(conexion):
    titulo("PARTE A. FUNCIONES DE VENTANA")

    punto("A1", "Acumulado y total de la tarjeta 5")
    correr(conexion, """
        SELECT id_transaccion, fecha_hora, monto,
               SUM(monto) OVER (PARTITION BY id_tarjeta ORDER BY fecha_hora)
                   AS acumulado,
               SUM(monto) OVER (PARTITION BY id_tarjeta) AS total_tarjeta
        FROM pagos.transacciones
        WHERE estatus = 'APROBADA' AND id_tarjeta = 5
        ORDER BY fecha_hora
    """, limite=6)
    print("""
  La ultima fila del acumulado coincide con el total de la tarjeta. Es
  la comprobacion que conviene exigir: si no coinciden, el ORDER BY de
  la ventana esta mal planteado.
""")

    punto("A2", "Porcentaje de cada operacion sobre el total de su comercio")
    correr(conexion, """
        SELECT t.id_transaccion, c.nombre, t.monto,
               ROUND(100.0 * t.monto
                     / SUM(t.monto) OVER (PARTITION BY c.id_comercio), 3)
                   AS pct_del_comercio
        FROM pagos.transacciones t
        JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
        JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
        WHERE t.estatus = 'APROBADA'
        ORDER BY pct_del_comercio DESC
        LIMIT 10
    """)
    print("""
  Punto de diseno: se particiona por c.id_comercio y no por c.nombre.
  Ambos funcionan aqui porque el nombre es unico, pero particionar por
  la llave es la practica correcta.
""")

    punto("A3", "Con ORDER BY y sin ORDER BY dentro de OVER")
    correr(conexion, """
        SELECT id_transaccion, monto,
               SUM(monto) OVER (PARTITION BY id_tarjeta)                     AS sin_order,
               SUM(monto) OVER (PARTITION BY id_tarjeta ORDER BY fecha_hora) AS con_order
        FROM pagos.transacciones
        WHERE estatus = 'APROBADA' AND id_tarjeta = 5
        ORDER BY fecha_hora
    """, limite=5)
    print("""
  Explicacion esperada:

    Sin ORDER BY, el marco predeterminado abarca el grupo completo, de
    modo que SUM devuelve el total de la tarjeta, identico en todas las
    filas.

    Con ORDER BY, el marco predeterminado pasa a ser
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW, es decir, desde
    el inicio del grupo hasta la fila actual. Eso produce el acumulado.

  El punto que se evalua: ORDER BY dentro de OVER no ordena la salida.
  Cambia el marco, y por lo tanto cambia el valor calculado. Es la
  confusion mas frecuente de la sesion.
""")

    punto("A4", "Promedio movil de tres operaciones")
    correr(conexion, """
        SELECT id_transaccion, fecha_hora, monto,
               ROUND(AVG(monto) OVER (PARTITION BY id_tarjeta ORDER BY fecha_hora
                                      ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2)
                   AS movil_3
        FROM pagos.transacciones
        WHERE estatus = 'APROBADA' AND id_tarjeta = 5
        ORDER BY fecha_hora
    """, limite=6)
    print("""
  Requiere marco explicito. Las primeras dos filas promedian sobre menos
  de tres operaciones, porque el marco no puede retroceder mas alla del
  inicio del grupo. Ese comportamiento es correcto y conviene señalarlo.
""")


# =====================================================================
# PARTE B
# =====================================================================

def parte_b(conexion):
    titulo("PARTE B. ORDENAMIENTO Y DESPLAZAMIENTO")

    punto("B1", "Las tres funciones de rango ante empates")
    correr(conexion, """
        SELECT cl.nombre, COUNT(*) AS operaciones,
               ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS row_number,
               RANK()       OVER (ORDER BY COUNT(*) DESC) AS rank,
               DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) AS dense_rank
        FROM pagos.transacciones t
        JOIN pagos.tarjetas ta ON ta.id_tarjeta = t.id_tarjeta
        JOIN pagos.clientes cl ON cl.id_cliente = ta.id_cliente
        WHERE t.estatus = 'APROBADA'
        GROUP BY cl.id_cliente, cl.nombre
        ORDER BY operaciones DESC
        LIMIT 12
    """, limite=12)
    print("""
  Explicacion esperada:

    ROW_NUMBER numera de forma consecutiva y no reconoce empates. Dos
    clientes con el mismo conteo reciben numeros distintos, y cual queda
    primero es arbitrario salvo que se agregue un criterio de desempate.

    RANK asigna el mismo numero a los empatados y despues salta tantas
    posiciones como empates hubo.

    DENSE_RANK asigna el mismo numero y no salta.

  Criterio de uso:
    ROW_NUMBER  para elegir una sola fila por grupo
    RANK        para un ranking publicable, donde el salto es correcto
    DENSE_RANK  para contar cuantos niveles distintos existen

  Advertencia practica: con ROW_NUMBER conviene agregar un segundo
  criterio de ordenamiento, para que el resultado sea reproducible.
""")

    punto("B2", "Operacion de mayor monto de cada comercio")
    correr(conexion, """
        WITH ordenadas AS (
            SELECT t.id_transaccion, c.nombre, t.monto,
                   ROW_NUMBER() OVER (PARTITION BY c.id_comercio
                                      ORDER BY t.monto DESC) AS posicion
            FROM pagos.transacciones t
            JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
            JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
            WHERE t.estatus = 'APROBADA'
        )
        SELECT id_transaccion, nombre, monto
        FROM ordenadas WHERE posicion = 1
        ORDER BY monto DESC
    """)
    print("""
  Comparacion con la solucion de la sesion 2.2:

    La subconsulta correlacionada se evalua una vez por cada fila del
    resultado externo, y cada evaluacion vuelve a recorrer la tabla.

    La funcion de ventana recorre la tabla una sola vez, ordena dentro
    de cada particion y numera. Un solo paso.

  Esa diferencia es la que se evalua en E2.
""")

    punto("B3", "Intervalo desde la operacion anterior")
    correr(conexion, """
        WITH ordenadas AS (
            SELECT id_transaccion, id_tarjeta, fecha_hora,
                   LAG(fecha_hora) OVER (PARTITION BY id_tarjeta
                                         ORDER BY fecha_hora) AS anterior
            FROM pagos.transacciones WHERE estatus = 'APROBADA'
        )
        SELECT id_transaccion, id_tarjeta, fecha_hora,
               fecha_hora - anterior AS intervalo
        FROM ordenadas WHERE anterior IS NOT NULL
        ORDER BY intervalo LIMIT 10
    """)
    print("""
  El filtro anterior IS NOT NULL descarta la primera operacion de cada
  tarjeta, que no tiene predecesora. Omitirlo produce nulos en el
  resultado, lo cual no es un error pero suele no ser lo deseado.
""")

    punto("B4", "Variacion porcentual mensual")
    correr(conexion, """
        WITH por_mes AS (
            SELECT DATE_TRUNC('month', fecha_hora)::DATE AS mes,
                   SUM(monto) AS importe
            FROM pagos.transacciones WHERE estatus = 'APROBADA'
            GROUP BY mes
        )
        SELECT mes, importe,
               LAG(importe) OVER (ORDER BY mes) AS mes_anterior,
               ROUND(100.0 * (importe - LAG(importe) OVER (ORDER BY mes))
                     / LAG(importe) OVER (ORDER BY mes), 2) AS variacion_pct
        FROM por_mes ORDER BY mes
    """)
    print("""
  Nota: LAG aparece tres veces en la misma consulta. Se puede evitar la
  repeticion con una CTE intermedia, o con la clausula WINDOW del
  ejercicio F2. El motor no la evalua tres veces, pero la legibilidad
  si sufre.
""")

    punto("B5", "Los tres comercios de mayor importe por ciudad")
    correr(conexion, """
        WITH por_comercio AS (
            SELECT c.ciudad, c.nombre, SUM(t.monto) AS importe
            FROM pagos.transacciones t
            JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
            JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
            WHERE t.estatus = 'APROBADA'
            GROUP BY c.ciudad, c.nombre
        ),
        ranking AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY ciudad
                                         ORDER BY importe DESC) AS posicion
            FROM por_comercio
        )
        SELECT ciudad, posicion, nombre, importe
        FROM ranking WHERE posicion <= 3
        ORDER BY ciudad, posicion
    """, limite=12)
    print("""
  Observacion sobre este conjunto de datos: solo Ciudad de Mexico tiene
  mas de un comercio. Las demas ciudades devuelven una sola fila. El
  resultado es correcto y conviene anticiparlo, porque algun
  participante creera que su consulta falla.
""")


# =====================================================================
# PARTE C
# =====================================================================

def parte_c(conexion):
    titulo("PARTE C. EXPRESIONES DE TABLA COMUNES")

    punto("C1", "B5 reescrita con CTE encadenadas")
    print("""
  La solucion de B5 ya usa dos CTE. Lo que se evalua aqui es la
  comparacion con la version anidada.

  Con subconsultas, la misma logica queda asi:

      SELECT ciudad, posicion, nombre, importe
      FROM (
          SELECT *, ROW_NUMBER() OVER (...) AS posicion
          FROM (
              SELECT c.ciudad, c.nombre, SUM(t.monto) AS importe
              FROM ... GROUP BY c.ciudad, c.nombre
          ) AS por_comercio
      ) AS ranking
      WHERE posicion <= 3;

  Diferencias que el participante debe identificar:

    La version con CTE se lee de arriba abajo, en el orden en que ocurre
    el calculo. La anidada se lee de adentro hacia afuera.

    Cada CTE tiene nombre, de modo que la intencion queda documentada.

    Agregar una etapa a la version con CTE es agregar un bloque. En la
    anidada implica envolver todo otra vez.

  El resultado es identico. La diferencia es de mantenimiento.
""")

    punto("C2", "Desviaciones del gasto de cada cliente")
    correr(conexion, """
        WITH aprobadas AS (
            SELECT id_tarjeta, monto FROM pagos.transacciones
            WHERE estatus = 'APROBADA'
        ),
        por_cliente AS (
            SELECT cl.id_cliente, cl.nombre, SUM(a.monto) AS gasto
            FROM aprobadas a
            JOIN pagos.tarjetas ta ON ta.id_tarjeta = a.id_tarjeta
            JOIN pagos.clientes cl ON cl.id_cliente = ta.id_cliente
            GROUP BY cl.id_cliente, cl.nombre
        ),
        estadisticas AS (
            SELECT AVG(gasto) AS promedio, STDDEV(gasto) AS desviacion
            FROM por_cliente
        )
        SELECT p.nombre, p.gasto,
               ROUND((p.gasto - e.promedio) / e.desviacion, 2) AS desviaciones
        FROM por_cliente p CROSS JOIN estadisticas e
        ORDER BY p.gasto DESC LIMIT 10
    """)
    print("""
  El CROSS JOIN contra una CTE de una sola fila es la forma habitual de
  incorporar un valor global a cada fila. La alternativa es una funcion
  de ventana sin PARTITION BY:

      AVG(gasto) OVER () AS promedio

  Ambas son correctas. La segunda es mas breve y evita una etapa.
""")

    punto("C3", "Comercios que concentran el ochenta por ciento")
    filas = correr(conexion, """
        WITH por_comercio AS (
            SELECT c.nombre, SUM(t.monto) AS importe
            FROM pagos.transacciones t
            JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
            JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
            WHERE t.estatus = 'APROBADA'
            GROUP BY c.nombre
        ),
        acumulado AS (
            SELECT nombre, importe,
                   SUM(importe) OVER (ORDER BY importe DESC) AS acum,
                   SUM(importe) OVER ()                      AS total
            FROM por_comercio
        )
        SELECT nombre, importe,
               ROUND(100.0 * acum / total, 2) AS pct_acumulado
        FROM acumulado ORDER BY importe DESC
    """)
    print("""
  Lectura del resultado: cuatro comercios superan el ochenta por ciento
  acumulado. Es el patron de concentracion que el generador introdujo a
  proposito, y que sera relevante en la sesion 2.4 cuando se estudie el
  efecto de un indice sobre datos sesgados.
""")

    punto("C4", "Por que falla la consulta con ROW_NUMBER en WHERE")
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
        print(f"\n  Error real del motor: {str(error).splitlines()[0]}")

    print("""
  Explicacion esperada:

    Las funciones de ventana se evaluan en la etapa de SELECT, que ocurre
    despues de WHERE, de GROUP BY y de HAVING. Cuando WHERE se evalua,
    la ventana todavia no existe.

    Es la misma logica del orden de evaluacion que se vio en la sesion
    2.2 con las funciones de agregacion, aplicada un paso mas adelante.

  Correccion: calcular la ventana en una etapa y filtrar en la
  siguiente, con CTE o subconsulta. Es exactamente la estructura de B5.

  Consecuencia didactica que conviene explicitar: esta limitacion es la
  razon practica de que CTE y funciones de ventana se enseñen juntas.
  Casi toda consulta analitica util combina ambas.
""")


# =====================================================================
# PARTE D
# =====================================================================

def parte_d(conexion):
    titulo("PARTE D. CTE RECURSIVA")

    punto("D1", "Serie de dias del primer trimestre")
    correr(conexion, """
        WITH RECURSIVE dias AS (
            SELECT DATE '2026-01-01' AS dia
            UNION ALL
            SELECT (dia + INTERVAL '1 day')::DATE FROM dias
            WHERE dia < DATE '2026-03-31'
        )
        SELECT COUNT(*) AS total_dias, MIN(dia) AS desde, MAX(dia) AS hasta
        FROM dias
    """)
    print("""
  Alternativa mas breve, propia de PostgreSQL:

      SELECT generate_series(DATE '2026-01-01', DATE '2026-03-31',
                             INTERVAL '1 day')::DATE;

  Conviene mostrarla despues del ejercicio, no antes. El proposito del
  ejercicio es entender el mecanismo recursivo; generate_series lo
  resuelve sin enseñarlo.
""")

    punto("D2", "Dias sin actividad, con importe cero")
    correr(conexion, """
        WITH RECURSIVE dias AS (
            SELECT DATE '2026-01-01' AS dia
            UNION ALL
            SELECT (dia + INTERVAL '1 day')::DATE FROM dias
            WHERE dia < DATE '2026-03-31'
        ),
        por_dia AS (
            SELECT fecha_hora::DATE AS dia, SUM(monto) AS importe
            FROM pagos.transacciones WHERE estatus = 'APROBADA'
            GROUP BY 1
        )
        SELECT d.dia, COALESCE(p.importe, 0) AS importe
        FROM dias d LEFT JOIN por_dia p ON p.dia = d.dia
        ORDER BY d.dia LIMIT 10
    """)
    print("""
  El LEFT JOIN va desde el calendario hacia los datos, nunca al reves.
  Invertirlo elimina justamente los dias que se querian conservar.

  COALESCE convierte el nulo en cero. Sin el, un dia sin actividad
  aparece con nulo, que no es lo mismo y rompe las sumas posteriores.
""")

    punto("D3", "Jerarquia de areas con nivel y ruta")
    conexion.execute("DROP TABLE IF EXISTS areas")
    conexion.execute("""
        CREATE TEMP TABLE areas (
            id_area INT PRIMARY KEY, nombre TEXT NOT NULL,
            id_padre INT REFERENCES areas (id_area))
    """)
    conexion.execute("""
        INSERT INTO areas VALUES
        (1,'Direccion General',NULL),(2,'Operaciones',1),(3,'Tecnologia',1),
        (4,'Autorizaciones',2),(5,'Contracargos',2),(6,'Infraestructura',3),
        (7,'Desarrollo',3),(8,'Antifraude',5)
    """)
    correr(conexion, """
        WITH RECURSIVE jerarquia AS (
            SELECT id_area, nombre, id_padre, 1 AS nivel, nombre::TEXT AS ruta
            FROM areas WHERE id_padre IS NULL
            UNION ALL
            SELECT a.id_area, a.nombre, a.id_padre, j.nivel + 1,
                   j.ruta || ' > ' || a.nombre
            FROM areas a JOIN jerarquia j ON j.id_area = a.id_padre
        )
        SELECT nivel, ruta FROM jerarquia ORDER BY ruta
    """, limite=10)
    print("""
  Tres elementos que el participante debe identificar:

    El caso base selecciona la raiz, con id_padre nulo.
    El paso recursivo se combina contra el resultado de la vuelta previa.
    La ruta se construye por concatenacion acumulativa.

  La condicion de parada aqui es implicita: la recursion termina cuando
  ninguna fila nueva se agrega, es decir, cuando se agotan las hojas.
""")

    punto("D4", "Solo las areas sin hijas")
    correr(conexion, """
        WITH RECURSIVE jerarquia AS (
            SELECT id_area, nombre, id_padre, 1 AS nivel FROM areas
            WHERE id_padre IS NULL
            UNION ALL
            SELECT a.id_area, a.nombre, a.id_padre, j.nivel + 1
            FROM areas a JOIN jerarquia j ON j.id_area = a.id_padre
        )
        SELECT j.nivel, j.nombre FROM jerarquia j
        WHERE NOT EXISTS (SELECT 1 FROM areas h WHERE h.id_padre = j.id_area)
        ORDER BY j.nivel, j.nombre
    """)

    punto("D5", "Que ocurre sin condicion de parada")
    print("""
  Sin condicion de parada, la recursion no termina por si sola. Dos
  escenarios distintos:

    En una serie generada, el paso recursivo siempre produce una fila
    nueva y la consulta crece hasta agotar memoria o disco.

    En una jerarquia con un ciclo, por ejemplo un area que es su propio
    ancestro, ocurre lo mismo aunque el paso parezca acotado.

  Mecanismos de proteccion:

    UNION en lugar de UNION ALL elimina duplicados y detiene los ciclos,
    a costa de comparar cada fila contra las anteriores.

    Llevar un contador de nivel y limitarlo:
        WHERE j.nivel < 10

    Acumular la ruta y verificar que el nodo no aparezca ya en ella, que
    es la forma correcta de detectar ciclos en una jerarquia real.

    PostgreSQL 14 y posteriores ofrecen ademas la clausula CYCLE, que
    marca las filas ciclicas de forma declarativa.
""")


# =====================================================================
# PARTE E
# =====================================================================

def parte_e():
    titulo("PARTE E. ANALISIS Y ARGUMENTACION")

    punto("E1", "Criterio para elegir donde calcular el acumulado")
    print("""
  Criterio esperado, sin recurrir a mediciones:

    En el motor cuando
      el resultado es mucho menor que el origen
      hay un solo consumidor del resultado
      el calculo forma parte de la definicion del dato y conviene que
        todos los consumidores obtengan el mismo valor
      el volumen no cabe comodamente en la memoria del equipo

    En el dataframe cuando
      se exploraran varias derivaciones sobre el mismo conjunto, de modo
        que el costo de traerlo se amortiza
      el calculo encadena operaciones que SQL no expresa con comodidad
      el resultado alimenta un modelo o una visualizacion

  Regla breve: mover el calculo hacia los datos, salvo que el calculo no
  pueda expresarse donde viven los datos, o salvo que el mismo conjunto
  vaya a servir para muchas preguntas distintas.

  Se acepta cualquier criterio equivalente. No se acepta uno basado solo
  en preferencia por una herramienta.
""")

    punto("E2", "Subconsulta correlacionada frente a funcion de ventana")
    print("""
  Diferencia de trabajo para el motor:

    La subconsulta correlacionada se evalua una vez por cada fila del
    resultado externo. Cada evaluacion vuelve a recorrer o buscar sobre
    la tabla interna. Con N filas externas, hay N evaluaciones.

    La funcion de ventana requiere un solo recorrido: el motor ordena
    las filas por particion y calcula al vuelo. Con N filas, hay un
    paso de ordenamiento y un paso de calculo.

  Diferencia de expresion:

    La ventana declara la intencion de forma directa. La subconsulta
    correlacionada obliga a repetir las condiciones de la consulta
    externa dentro de la interna, lo que duplica la logica y multiplica
    las oportunidades de error al mantenerla.

  Matiz que conviene reconocer: los planificadores modernos reescriben
  algunas subconsultas correlacionadas de forma eficiente. La ventaja
  de la ventana es siempre de expresividad, y con frecuencia tambien de
  desempeno.
""")

    punto("E3", "La CTE mejora la legibilidad, y el desempeno")
    print("""
  Respuesta esperada:

    La CTE mejora la legibilidad de forma consistente. Sobre el
    desempeno, no hay una respuesta unica.

    En PostgreSQL 12 y posteriores, una CTE referenciada una sola vez se
    integra en la consulta principal, de modo que el plan resultante es
    equivalente al de una subconsulta. No hay penalizacion.

    En versiones anteriores, la CTE actuaba siempre como barrera de
    optimizacion: se materializaba por completo antes de continuar, lo
    que impedia que un filtro externo se empujara hacia adentro. Ahi si
    podia empeorar el desempeno.

    Una CTE referenciada varias veces se materializa una vez y se
    reutiliza, lo que suele ser una ventaja frente a repetir la
    subconsulta.

  Se puede forzar el comportamiento con MATERIALIZED y
  NOT MATERIALIZED.

  Lo que se evalua es que el participante distinga entre legibilidad,
  que es siempre mejor, y desempeno, que depende de la version y del
  numero de referencias.
""")

    punto("E4", "Limitaciones del criterio de tres desviaciones")
    print("""
  Dos limitaciones que el participante debe identificar. Cualquier par
  razonable es aceptable:

    Supone una distribucion aproximadamente simetrica. El gasto con
    tarjeta tiene cola larga a la derecha, de modo que el criterio
    marca operaciones legitimas de alto monto.

    Necesita historial suficiente. Con pocas operaciones, el promedio y
    la desviacion de la propia tarjeta son inestables, y una tarjeta
    nueva no tiene patron contra el cual comparar.

    El propio dato atipico contamina el calculo, porque entra en el
    promedio y en la desviacion que sirven para juzgarlo.

    No considera contexto: hora, comercio, geografia, ni el
    comportamiento de tarjetas similares. Una compra grande en un
    comercio habitual no es lo mismo que una en un giro nuevo.

  Punto de honestidad que conviene señalar en clase: en este conjunto
  los datos son sinteticos, de modo que los patrones son los que
  introdujo el generador. El ejercicio enseña SQL analitico, no
  deteccion de fraude.
""")


# =====================================================================
# PARTE F
# =====================================================================

def parte_f(conexion):
    titulo("PARTE F. EJERCICIO DE EXTENSION")

    punto("F2", "La clausula WINDOW")
    correr(conexion, """
        SELECT id_transaccion, fecha_hora, monto,
               SUM(monto) OVER w   AS acumulado,
               ROUND(AVG(monto) OVER w, 2) AS promedio_hasta_aqui,
               ROW_NUMBER() OVER w AS posicion
        FROM pagos.transacciones
        WHERE estatus = 'APROBADA' AND id_tarjeta = 5
        WINDOW w AS (PARTITION BY id_tarjeta ORDER BY fecha_hora)
        ORDER BY fecha_hora
    """, limite=6)
    print("""
  La clausula WINDOW nombra una definicion y la reutiliza. Evita repetir
  PARTITION BY y ORDER BY en cada columna.

  Ubicacion: va despues de HAVING y antes de ORDER BY. Es un lugar poco
  intuitivo y suele ser la causa del error al usarla por primera vez.
""")

    punto("F3", "ROWS frente a RANGE con valores repetidos")
    correr(conexion, """
        SELECT metodo_captura, monto,
               SUM(monto) OVER (ORDER BY metodo_captura
                                RANGE BETWEEN UNBOUNDED PRECEDING
                                          AND CURRENT ROW) AS con_range,
               SUM(monto) OVER (ORDER BY metodo_captura
                                ROWS  BETWEEN UNBOUNDED PRECEDING
                                          AND CURRENT ROW) AS con_rows
        FROM pagos.transacciones
        WHERE estatus = 'APROBADA' AND id_tarjeta = 5
        ORDER BY metodo_captura
    """, limite=8)
    print("""
  Lectura del resultado:

    RANGE trata como una sola unidad a todas las filas con el mismo
    valor de ORDER BY. Las filas empatadas comparten el mismo acumulado,
    que ya incluye a todo el grupo.

    ROWS cuenta filas fisicas, de modo que el acumulado avanza fila por
    fila incluso entre valores repetidos.

  Cuando conviene cada uno:

    ROWS para acumulados y promedios moviles, donde interesa la posicion
    fisica de la fila.

    RANGE cuando el criterio de ordenamiento tiene significado propio y
    los empates deben tratarse juntos, por ejemplo un acumulado diario
    donde todas las operaciones del mismo dia cuentan igual.

  Advertencia: el marco predeterminado es RANGE, no ROWS. Un promedio
  movil escrito sin marco explicito sobre una columna con valores
  repetidos da un resultado distinto del esperado, y no falla.
""")


# =====================================================================

def criterios():
    titulo("CRITERIOS DE CALIFICACION")
    print("""
  Parte A, 25 por ciento
    A3 es el punto de mayor valor. La confusion mas frecuente es creer
    que ORDER BY dentro de OVER sirve para ordenar la salida. Cambia el
    marco y por lo tanto el valor calculado.
    En A1, exigir la comprobacion de que el ultimo acumulado coincide
    con el total del grupo.

  Parte B, 25 por ciento
    B1 se evalua por la explicacion, no por reproducir las tres columnas.
    B5 devuelve una sola fila para casi todas las ciudades en este
    conjunto. Es correcto. Anticiparlo evita que el grupo crea que su
    consulta esta mal.

  Parte C, 20 por ciento
    C4 concentra el valor. Debe reconocerse como el mismo problema de
    orden de evaluacion de la sesion 2.2, un paso mas adelante.

  Parte D, 15 por ciento
    D3 debe identificar los tres elementos: caso base, paso recursivo y
    condicion de parada.
    En D5 se acepta cualquier mecanismo de proteccion correcto.

  Parte E, 15 por ciento
    E1 y E2 son los puntos evaluables de fondo.
    En E3 se valora que distinga legibilidad de desempeno y que no
    afirme de forma categorica que la CTE es mas rapida o mas lenta.
    En E4 se valora el escepticismo. Un participante que presenta el
    criterio como deteccion de fraude no obtiene el punto.

  Error transversal a vigilar
    Usar GROUP BY donde el ejercicio pedia conservar el detalle. Produce
    un resultado que parece correcto y responde otra pregunta.
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
