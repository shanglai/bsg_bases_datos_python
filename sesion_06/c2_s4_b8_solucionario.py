"""
c2_s4_b8_solucionario.py
Solucionario del taller de la sesion 2.4, en un solo archivo.

Documento para el instructor. NO se entrega al participante.

Requisitos: base pagos cargada con la columna autorizacion, .env presente
Ejecucion:  python c2_s4_b8_solucionario.py
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
    print("\n" + "-" * 72 + f"\n{clave}. {enunciado}\n" + "-" * 72)


def correr(conexion, sql, limite=8):
    cursor = conexion.execute(sql)
    columnas = [d.name for d in cursor.description]
    filas = cursor.fetchall()
    print("    " + "  ".join(f"{c[:18]:<18}" for c in columnas))
    for fila in filas[:limite]:
        print("    " + "  ".join(f"{str(v)[:18]:<18}" for v in fila))
    if len(filas) > limite:
        print(f"    ... {len(filas) - limite} filas mas")
    print(f"    [{len(filas)} filas]")
    return filas


def plan(conexion, sql):
    for fila in conexion.execute("EXPLAIN ANALYZE " + sql).fetchall():
        print("    " + fila[0])


# =====================================================================

def parte_a(conexion):
    titulo("PARTE A. ACCESO AL DOCUMENTO")

    punto("A2", "Campos del bloque captura, por metodo")
    correr(conexion, """
        SELECT autorizacion->'captura'->>'metodo' AS metodo,
               STRING_AGG(DISTINCT campo, ', ' ORDER BY campo) AS campos
        FROM pagos.transacciones,
             jsonb_object_keys(autorizacion->'captura') AS campo
        GROUP BY metodo ORDER BY metodo
    """)
    print("""
  Explicacion esperada: los campos dependen de la tecnologia de captura.
  Un criptograma solo existe si hubo chip. Un identificador de codigo
  solo existe si hubo QR. Modelarlos como columnas obligaria a
  declararlas todas y dejarlas nulas en la mayoria de las filas.
""")

    punto("A3", "Emisores con mayor tiempo de respuesta")
    correr(conexion, """
        SELECT id_transaccion,
               autorizacion->'emisor'->>'nombre' AS emisor,
               (autorizacion#>>'{emisor,tiempo_respuesta_ms}')::INT AS ms
        FROM pagos.transacciones
        ORDER BY ms DESC LIMIT 10
    """)

    punto("A5", "La diferencia entre -> y ->>")
    correr(conexion, """
        SELECT pg_typeof(autorizacion->'emisor'->'nombre')   AS con_flecha_simple,
               pg_typeof(autorizacion->'emisor'->>'nombre')  AS con_flecha_doble,
               autorizacion->'emisor'->'nombre'              AS valor_jsonb,
               autorizacion->'emisor'->>'nombre'             AS valor_texto
        FROM pagos.transacciones LIMIT 1
    """)
    print("""
  Explicacion esperada:

    ->  devuelve jsonb. Una cadena JSON conserva sus comillas, de modo
        que el valor se ve como "BANORTE", con comillas incluidas.

    ->> devuelve text. Entrega el contenido sin las comillas.

  Consecuencia practica: comparar el resultado de -> contra una cadena
  de Python o de SQL falla, porque los tipos no coinciden. Para
  comparar contra texto se usa ->>; para seguir navegando el documento
  se usa ->.

  Regla de uso: -> en los pasos intermedios, ->> en el ultimo.
""")

    punto("A6", "Puntaje mayor a 90 y la conversion de tipo")
    correr(conexion, """
        SELECT COUNT(*) AS puntaje_alto
        FROM pagos.transacciones
        WHERE (autorizacion#>>'{riesgo,puntaje}')::INT > 90
    """)
    print("""
  El operador #>> devuelve texto. Sin la conversion, la comparacion
  seria alfabetica: el texto '9' resultaria mayor que '90', porque se
  comparan caracter por caracter.

  Comprobacion que conviene mostrar en clase:
      SELECT '9' > '90' AS comparacion_de_texto;   -- verdadero
      SELECT 9 > 90 AS comparacion_numerica;       -- falso
""")
    correr(conexion, "SELECT '9' > '90' AS texto, 9 > 90 AS numero")


def parte_b(conexion):
    titulo("PARTE B. BUSQUEDA DENTRO DEL DOCUMENTO")

    punto("B1", "Mensajes con y sin el bloque riesgo")
    correr(conexion, """
        SELECT autorizacion->>'version' AS version,
               COUNT(*) AS total,
               COUNT(*) FILTER (WHERE autorizacion ? 'riesgo') AS con_riesgo
        FROM pagos.transacciones GROUP BY version ORDER BY total DESC
    """)
    print("""
  Los mensajes sin bloque de riesgo corresponden a la version 1.4 del
  protocolo. Es la situacion habitual en produccion: conviven versiones
  del mensaje y la consulta debe tolerarlo.

  Consecuencia que conviene señalar: una consulta que asuma la
  existencia del bloque devuelve nulo para esas filas, y un promedio
  calculado sobre ellas las ignora en silencio.
""")

    punto("B2 y B3", "Contencion frente a acceso por operador")
    correr(conexion, """
        SELECT
          (SELECT COUNT(*) FROM pagos.transacciones
           WHERE autorizacion @> '{"rechazo": {"codigo": "LIMITE_EXCEDIDO"}}')
              AS con_contencion,
          (SELECT COUNT(*) FROM pagos.transacciones
           WHERE autorizacion->'rechazo'->>'codigo' = 'LIMITE_EXCEDIDO')
              AS con_flecha
    """)
    print("""
  Los dos resultados coinciden. La diferencia aparece en el plan de
  ejecucion, y es el tema de C3.
""")

    punto("B6", "Senales de riesgo con su frecuencia")
    correr(conexion, """
        SELECT senal, COUNT(*) AS ocurrencias
        FROM pagos.transacciones,
             jsonb_array_elements_text(
                 COALESCE(autorizacion#>'{riesgo,senales}', '[]'::jsonb)) AS senal
        GROUP BY senal ORDER BY ocurrencias DESC
    """)
    print("""
  El COALESCE es necesario. Sin el, las filas sin bloque de riesgo
  producen nulo y jsonb_array_elements_text falla.

  Punto de diseno: la expansion multiplica filas. Una operacion con tres
  senales genera tres filas. Si la consulta combinara esto con otras
  tablas, el conteo se inflaria. Conviene expandir en una CTE aparte.
""")


def parte_c(conexion):
    titulo("PARTE C. INDICES")

    # Se eliminan todos los indices sobre la columna, incluidos los que
    # pudo dejar la demostracion de c2_s4_b3_jsonb.sql. Sin esto, el
    # plan de C1 ya usaria un indice y el contraste se pierde.
    conexion.execute("""
        DO $$
        DECLARE i RECORD;
        BEGIN
            FOR i IN SELECT indexname FROM pg_indexes
                     WHERE schemaname = 'pagos' AND tablename = 'transacciones'
                       AND (indexname LIKE '%autorizacion%'
                            OR indexname LIKE '%taller%'
                            OR indexname LIKE '%puntaje%')
            LOOP
                EXECUTE 'DROP INDEX pagos.' || quote_ident(i.indexname);
            END LOOP;
        END $$;
    """)
    conexion.execute("ANALYZE pagos.transacciones")

    consulta_b2 = ("SELECT COUNT(*) FROM pagos.transacciones "
                   "WHERE autorizacion @> '{\"rechazo\": "
                   "{\"codigo\": \"LIMITE_EXCEDIDO\"}}'")

    punto("C1", "Plan sin indice")
    plan(conexion, consulta_b2)

    punto("C2", "Plan con indice GIN")
    conexion.execute("CREATE INDEX idx_taller_gin ON pagos.transacciones "
                     "USING GIN (autorizacion)")
    conexion.execute("ANALYZE pagos.transacciones")
    plan(conexion, consulta_b2)
    print("""
  El recorrido pasa de Seq Scan a Bitmap Heap Scan con un Bitmap Index
  Scan sobre idx_taller_gin.

  El paso Recheck Cond no es un defecto: GIN es un indice con perdida,
  de modo que devuelve candidatos y el motor vuelve a evaluar la
  condicion sobre cada uno.
""")

    punto("C3", "Plan de la version con ->>")
    plan(conexion, "SELECT COUNT(*) FROM pagos.transacciones "
                   "WHERE autorizacion->'rechazo'->>'codigo' = 'LIMITE_EXCEDIDO'")
    print("""
  Sigue en Seq Scan.

  Explicacion esperada: el indice GIN indexa el contenido del documento
  como pares de clave y valor, y responde a los operadores de contencion
  y de existencia. La expresion autorizacion->'rechazo'->>'codigo' es
  una funcion aplicada a la columna: el motor no puede relacionarla con
  las entradas del indice.

  Para que esa expresion use un indice, hay que crear un indice de
  expresion sobre ella misma, como en C5.
""")

    punto("C4", "Un predicado poco selectivo no usa el indice")
    plan(conexion, "SELECT COUNT(*) FROM pagos.transacciones "
                   "WHERE autorizacion @> '{\"emisor\": {\"pais\": \"MX\"}}'")
    print("""
  El indice existe y el operador es el correcto, y aun asi el motor
  elige Seq Scan.

  Explicacion: todas las filas cumplen la condicion. Leer el indice y
  despues visitar cada fila cuesta mas que recorrer la tabla de corrido.
  El planificador estima la selectividad y decide.

  Este es el punto de mayor valor de la parte C. Crear un indice y
  suponer que se usa es un error de diagnostico frecuente. El plan es la
  unica forma de saberlo.
""")

    punto("C5", "Indice de expresion para rangos")
    conexion.execute("""
        CREATE INDEX idx_taller_puntaje ON pagos.transacciones
        (((autorizacion#>>'{riesgo,puntaje}')::INT))
    """)
    conexion.execute("ANALYZE pagos.transacciones")
    plan(conexion, "SELECT COUNT(*) FROM pagos.transacciones "
                   "WHERE (autorizacion#>>'{riesgo,puntaje}')::INT > 98")
    print("""
  Ahora si aparece un Bitmap Index Scan. El indice de expresion es un
  B-tree ordinario sobre el resultado de la expresion, de modo que
  soporta comparaciones de rango. GIN no las soporta.

  Condicion importante: la consulta debe escribir la expresion
  exactamente igual que el indice. Un cambio de #>> a -> ->> impide que
  el motor la reconozca.
""")

    punto("C6", "Tamano de los dos indices GIN")
    conexion.execute("CREATE INDEX idx_taller_path ON pagos.transacciones "
                     "USING GIN (autorizacion jsonb_path_ops)")
    correr(conexion, """
        SELECT indexname,
               pg_size_pretty(pg_relation_size(('pagos.'||indexname)::regclass))
                   AS tamano
        FROM pg_indexes
        WHERE tablename = 'transacciones' AND indexname LIKE 'idx_taller%'
        ORDER BY indexname
    """)
    print("""
  jsonb_path_ops resulta cerca de un treinta por ciento mas pequeno,
  porque indexa el hash de la ruta completa en lugar de cada clave y
  cada valor por separado.

  Lo que se pierde: los operadores de existencia. Con jsonb_path_ops,
  una consulta con ? o ?& no puede usar el indice.

  Criterio: si todas las busquedas usan @>, conviene jsonb_path_ops.
""")


def parte_d():
    titulo("PARTE D. SQLALCHEMY 2.0")

    print("""
  D1 y D3. Declaracion en estilo 2.0

      class Base(DeclarativeBase):
          pass

      class Comercio(Base):
          __tablename__ = "comercios"
          __table_args__ = {"schema": "pagos"}

          id_comercio: Mapped[int] = mapped_column(primary_key=True)
          nombre: Mapped[str] = mapped_column(String(120), unique=True)
          categoria: Mapped[str] = mapped_column(String(60))
          ciudad: Mapped[str] = mapped_column(String(80))

      class Transaccion(Base):
          __tablename__ = "transacciones"
          __table_args__ = {"schema": "pagos"}

          id_transaccion: Mapped[str] = mapped_column(String(20),
                                                      primary_key=True)
          monto: Mapped[Decimal] = mapped_column(Numeric(12, 2))
          autorizacion: Mapped[Optional[dict]] = mapped_column(JSONB)

  Puntos a exigir:

    DeclarativeBase por herencia, no declarative_base() como funcion.
    Mapped[...] con mapped_column, no Column.
    La anotacion define la nulabilidad: Mapped[str] implica NOT NULL,
      Mapped[Optional[str]] admite nulo.
    monto declarado como Decimal con Numeric(12, 2). Declararlo como
      float deshace la decision de la sesion 2.1 en la capa de acceso.

  D2. Consulta con select

      consulta = select(Comercio).where(Comercio.ciudad == ciudad)
      resultado = sesion.execute(consulta).scalars().all()

    scalars() devuelve objetos del modelo. Sin el, se obtienen tuplas.

  D4 y D5. Filtro sobre el documento, resuelto en el motor

      # con acceso por operador
      select(func.count()).select_from(Transaccion).where(
          Transaccion.autorizacion["emisor"]["nombre"].astext == emisor)

      # con contencion, que puede usar el indice GIN
      select(func.count()).select_from(Transaccion).where(
          Transaccion.autorizacion.contains({"emisor": {"nombre": emisor}}))

    Error a vigilar en la revision: traer todas las transacciones y
    filtrar con un ciclo de Python. Devuelve el resultado correcto,
    mueve cinco mil filas por la red y deshace el trabajo de la parte C.

  D6. Consultas en cadena

      # una consulta por cada comercio
      for comercio in sesion.execute(select(Comercio)).scalars():
          len(comercio.terminales)

      # dos consultas en total
      sesion.execute(
          select(Comercio).options(selectinload(Comercio.terminales)))

    Con siete comercios la diferencia es irrelevante. El punto es que el
    patron no produce ningun error: solo se vuelve lento al crecer.
""")


def parte_e(conexion):
    titulo("PARTE E. ANALISIS Y ARGUMENTACION")

    punto("E1", "Cuantas columnas haria falta declarar")
    correr(conexion, """
        SELECT COUNT(DISTINCT campo) AS campos_distintos_en_captura
        FROM pagos.transacciones,
             jsonb_object_keys(autorizacion->'captura') AS campo
    """)
    correr(conexion, """
        SELECT autorizacion->'captura'->>'metodo' AS metodo,
               COUNT(DISTINCT campo)              AS campos_de_este_metodo
        FROM pagos.transacciones,
             jsonb_object_keys(autorizacion->'captura') AS campo
        GROUP BY metodo ORDER BY metodo
    """)
    print("""
  Once campos distintos en total, entre tres y cinco por metodo. Una
  tabla relacional necesitaria once columnas, de las cuales entre seis y
  ocho quedarian nulas en cada fila.

  Ademas, cada metodo de captura nuevo obligaria a alterar la tabla, lo
  que en produccion implica coordinar una migracion.
""")

    punto("E2", "Por que ->> no aprovecha el indice GIN")
    print("""
  Respuesta esperada:

    El indice GIN almacena entradas derivadas del contenido del
    documento: claves y valores. Los operadores @>, ? , ?| y ?& estan
    definidos sobre ese contenido, de modo que el motor puede traducir
    la condicion a una busqueda en el indice.

    La expresion autorizacion->'rechazo'->>'codigo' es una funcion
    aplicada a la columna. Su resultado no esta almacenado en ninguna
    parte y el motor no tiene forma de relacionarlo con las entradas del
    indice, de modo que recorre la tabla y evalua fila por fila.

    Para indexar esa expresion hay que crear un indice sobre ella misma.

  Formulacion breve: GIN indexa el documento, no las expresiones que se
  aplican sobre el.
""")

    punto("E3", "Recuperar garantia de estructura sobre JSONB")
    print("""
  Dos mecanismos, con su limite:

    1. Restriccion CHECK sobre la columna.

         ALTER TABLE pagos.transacciones
         ADD CONSTRAINT chk_version CHECK (autorizacion ? 'version');

       Limite: verifica lo que se declara y nada mas. Cubrir un
       documento completo exigiria decenas de restricciones, dificiles
       de mantener y evaluadas en cada escritura.

    2. Columna generada que extrae un campo y lo somete a las
       restricciones habituales.

         ALTER TABLE pagos.transacciones
         ADD COLUMN emisor TEXT GENERATED ALWAYS AS
             (autorizacion->'emisor'->>'nombre') STORED;

       Limite: solo protege el campo extraido, y duplica el dato.

  Tercer mecanismo aceptable si alguien lo propone: validar contra un
  esquema JSON en la capa de aplicacion. Su limite es que vive fuera del
  motor, de modo que una escritura por otra via lo evita, exactamente el
  argumento de la sesion 1.2 sobre la funcion de limpieza.

  Conclusion honesta: no se recupera la garantia completa. Se recupera
  la parte que se declare de forma explicita.
""")

    punto("E4", "Criterio: columna o documento")
    print("""
  Criterio esperado:

    En columna cuando
      el dato existe en todas las filas
      participa en llaves, restricciones o relaciones
      se filtra o se agrupa con frecuencia
      su ausencia o su tipo incorrecto debe rechazarse

    En documento cuando
      la estructura varia entre filas
      el conjunto de campos cambia con el tiempo sin previo aviso
      se lee casi siempre completo y se consulta poco por campo
      pertenece a un sistema externo cuyo formato no se controla

  Aplicado al caso: la fecha, el monto, el estatus y las llaves foraneas
  son columnas. El mensaje de autorizacion es documento.

  Regla breve: columna para lo que el modelo garantiza, documento para
  lo que el modelo no puede prever.
""")

    punto("E5", "Ficha de PostgreSQL y anticipacion de MongoDB")
    print("""
  Punto 1, modelo de datos: relacional, con soporte documental dentro de
  una columna. Ambos modelos en el mismo motor y en la misma
  transaccion.

  Punto 3, garantias: la parte relacional conserva todas las
  restricciones. La parte documental solo las que se declaren de forma
  explicita.

  Punto 6, cuando conviene: cuando la mayor parte del modelo es estable
  y la variabilidad se concentra en una porcion acotada.

  Anticipacion de MongoDB, que se verifica en el capitulo 3:

    Es probable que difieran los puntos 2, 4 y 6. La pregunta a plantear
    al grupo es que aporta MongoDB si PostgreSQL ya almacena, indexa y
    consulta documentos. Las respuestas candidatas son el modelo de
    distribucion, la ausencia de esquema en toda la coleccion y el
    ecosistema de herramientas.

    Lo que se evalua no es acertar, sino formular la pregunta correcta.
""")


def criterios():
    titulo("CRITERIOS DE CALIFICACION")
    print("""
  Parte A, 20 por ciento
    A5 y A6 concentran el valor. La confusion entre -> y ->> es la causa
    mas comun de errores al empezar con JSONB.

  Parte B, 20 por ciento
    En B6, exigir el COALESCE. Sin el, la consulta falla con las filas
    de la version 1.4 del protocolo.

  Parte C, 25 por ciento
    C4 es el punto de mayor valor de todo el taller. El participante
    debe reconocer que un indice existente no garantiza que se use, y
    que el plan es la unica forma de saberlo.
    C3 exige entender que GIN indexa el documento, no las expresiones.

  Parte D, 20 por ciento
    Verificar estilo 2.0: DeclarativeBase, Mapped, mapped_column,
    select. El estilo 1.x obtiene calificacion parcial.
    Verificar que el filtro ocurra en el motor. Filtrar en Python
    obtiene calificacion parcial aunque el resultado sea correcto.

  Parte E, 15 por ciento
    E3 y E4 son los puntos evaluables de fondo. En E3 se valora que
    reconozca que la garantia no se recupera por completo.

  Error transversal a vigilar
    Suponer que el bloque riesgo existe en todos los mensajes. Cerca del
    seis por ciento no lo trae, y una consulta que lo asuma devuelve
    nulos que se ignoran en silencio al promediar.
""")


def main():
    with psycopg.connect(cadena()) as conexion:
        conexion.autocommit = True
        parte_a(conexion)
        parte_b(conexion)
        parte_c(conexion)
        parte_d()
        parte_e(conexion)
        criterios()


if __name__ == "__main__":
    main()
