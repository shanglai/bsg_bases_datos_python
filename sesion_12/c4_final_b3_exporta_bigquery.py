"""
c4_final_b3_exporta_bigquery.py
Genera el archivo que se carga en BigQuery, con estructura anidada.

Lo ejecuta el INSTRUCTOR una sola vez, antes de la clase. Los alumnos no
lo corren: ellos encuentran la tabla ya cargada.

Produce dos archivos:

    operaciones.ndjson   un documento JSON por linea, que es el formato
                         que BigQuery carga de forma nativa
    esquema.json         el esquema explicito, con RECORD y REPEATED

Por que NDJSON y no CSV: el caso tiene estructura anidada, y esa es
exactamente la capacidad de BigQuery que la sesion enseña. Un CSV
obligaria a aplanar todo y perderia el punto.

Requisitos: PostgreSQL con el caso cargado y la columna autorizacion
Ejecucion:  python c4_final_b3_exporta_bigquery.py
"""

import json
import os
from datetime import datetime
from decimal import Decimal

import psycopg
from dotenv import load_dotenv

load_dotenv(override=True)
SALIDA_DATOS = "operaciones.ndjson"
SALIDA_ESQUEMA = "esquema.json"


def cadena_postgres():
    return (f"host={os.getenv('PGHOST', 'localhost')} "
            f"port={os.getenv('PGPORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DB')} "
            f"user={os.getenv('POSTGRES_USER')} "
            f"password={os.getenv('POSTGRES_PASSWORD')}")


CONSULTA = """
    SELECT t.id_transaccion, t.fecha_hora, t.monto, t.moneda,
           t.estatus, t.metodo_captura, t.autorizacion,
           c.id_comercio, c.nombre AS comercio, c.categoria, c.ciudad,
           te.id_terminal, te.codigo AS terminal,
           cl.id_cliente, cl.nombre AS cliente, cl.correo,
           ta.id_tarjeta, ta.ultimos4, ta.marca,
           cc.id_contracargo IS NOT NULL AS tiene_contracargo
    FROM pagos.transacciones t
    JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
    JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
    JOIN pagos.tarjetas   ta ON ta.id_tarjeta  = t.id_tarjeta
    JOIN pagos.clientes   cl ON cl.id_cliente  = ta.id_cliente
    LEFT JOIN pagos.contracargos cc ON cc.id_transaccion = t.id_transaccion
    ORDER BY t.fecha_hora
"""


# =====================================================================
# El esquema
#
# Tres tipos que no existen en PostgreSQL y son el tema de la sesion:
#
#   RECORD             una columna que contiene subcolumnas. Es lo que
#                      en el modelo relacional seria una tabla aparte.
#   REPEATED           una columna que contiene varios valores. Es lo
#                      que seria una tabla de detalle.
#   RECORD + REPEATED  varias filas completas dentro de una columna.
#
# BigQuery los almacena en columnas separadas de forma interna, de modo
# que consultar solo comercio.nombre NO lee el resto del registro. Esa
# es la diferencia con JSONB de PostgreSQL, que lee el documento entero.
# =====================================================================

ESQUEMA = [
    {"name": "id_transaccion", "type": "STRING", "mode": "REQUIRED",
     "description": "Identificador de la operacion"},
    {"name": "fecha_hora", "type": "TIMESTAMP", "mode": "REQUIRED",
     "description": "Columna de particionamiento"},
    {"name": "monto", "type": "NUMERIC", "mode": "REQUIRED",
     "description": "NUMERIC conserva exactitud decimal, como en PostgreSQL"},
    {"name": "moneda", "type": "STRING", "mode": "REQUIRED"},
    {"name": "estatus", "type": "STRING", "mode": "REQUIRED"},
    {"name": "metodo_captura", "type": "STRING", "mode": "REQUIRED"},
    {"name": "tiene_contracargo", "type": "BOOLEAN", "mode": "REQUIRED"},

    {"name": "comercio", "type": "RECORD", "mode": "NULLABLE",
     "description": "Columna con subcolumnas",
     "fields": [
         {"name": "id", "type": "INTEGER"},
         {"name": "nombre", "type": "STRING"},
         {"name": "categoria", "type": "STRING"},
         {"name": "ciudad", "type": "STRING"},
     ]},
    {"name": "terminal", "type": "RECORD", "mode": "NULLABLE",
     "fields": [
         {"name": "id", "type": "INTEGER"},
         {"name": "codigo", "type": "STRING"},
     ]},
    {"name": "cliente", "type": "RECORD", "mode": "NULLABLE",
     "fields": [
         {"name": "id", "type": "INTEGER"},
         {"name": "nombre", "type": "STRING"},
         {"name": "correo", "type": "STRING"},
     ]},
    {"name": "tarjeta", "type": "RECORD", "mode": "NULLABLE",
     "fields": [
         {"name": "id", "type": "INTEGER"},
         {"name": "ultimos4", "type": "STRING"},
         {"name": "marca", "type": "STRING"},
     ]},

    {"name": "autorizacion", "type": "RECORD", "mode": "NULLABLE",
     "description": "El mensaje de la terminal, anidado en tres niveles",
     "fields": [
         {"name": "version", "type": "STRING"},
         {"name": "recibido_en", "type": "STRING"},
         {"name": "emisor", "type": "RECORD", "fields": [
             {"name": "nombre", "type": "STRING"},
             {"name": "pais", "type": "STRING"},
             {"name": "tiempo_respuesta_ms", "type": "INTEGER"},
         ]},
         {"name": "dispositivo", "type": "RECORD", "fields": [
             {"name": "serie", "type": "STRING"},
             {"name": "firmware", "type": "STRING"},
             {"name": "ubicacion", "type": "RECORD", "fields": [
                 {"name": "lat", "type": "FLOAT"},
                 {"name": "lon", "type": "FLOAT"},
             ]},
         ]},
         {"name": "captura", "type": "RECORD", "fields": [
             {"name": "metodo", "type": "STRING"},
             {"name": "criptograma", "type": "STRING"},
             {"name": "aid", "type": "STRING"},
             {"name": "contador_aplicacion", "type": "INTEGER"},
             {"name": "limite_sin_firma", "type": "INTEGER"},
             {"name": "id_codigo", "type": "STRING"},
             {"name": "aplicacion", "type": "STRING"},
             {"name": "vigencia_segundos", "type": "INTEGER"},
             {"name": "pista", "type": "INTEGER"},
             {"name": "lectura_degradada", "type": "BOOLEAN"},
             {"name": "motivo", "type": "STRING"},
             {"name": "operador", "type": "STRING"},
         ]},
         {"name": "riesgo", "type": "RECORD", "fields": [
             {"name": "puntaje", "type": "INTEGER"},
             # REPEATED: varios valores en una sola columna. En el modelo
             # relacional habria sido una tabla de detalle con su llave
             # foranea. Aqui vive dentro de la fila.
             {"name": "senales", "type": "STRING", "mode": "REPEATED"},
         ]},
         {"name": "rechazo", "type": "RECORD", "fields": [
             {"name": "codigo", "type": "STRING"},
             {"name": "reintentable", "type": "BOOLEAN"},
         ]},
     ]},
]


def construir_fila(fila):
    """Arma un registro con la estructura que espera el esquema.

    BigQuery exige que los tipos coincidan. Dos conversiones necesarias:

      TIMESTAMP  se escribe en formato ISO 8601
      NUMERIC    se escribe como cadena, para no perder precision al
                 pasar por el flotante de JSON. Es la misma decision del
                 monto que el curso ha seguido desde la sesion 2.1, y
                 aqui SI se conserva.
    """
    autorizacion = fila["autorizacion"] or {}

    return {
        "id_transaccion": fila["id_transaccion"],
        "fecha_hora": fila["fecha_hora"].isoformat(),
        "monto": str(fila["monto"]),
        "moneda": fila["moneda"],
        "estatus": fila["estatus"],
        "metodo_captura": fila["metodo_captura"],
        "tiene_contracargo": fila["tiene_contracargo"],
        "comercio": {
            "id": fila["id_comercio"], "nombre": fila["comercio"],
            "categoria": fila["categoria"], "ciudad": fila["ciudad"],
        },
        "terminal": {"id": fila["id_terminal"], "codigo": fila["terminal"]},
        "cliente": {"id": fila["id_cliente"], "nombre": fila["cliente"],
                    "correo": fila["correo"]},
        "tarjeta": {"id": fila["id_tarjeta"], "ultimos4": fila["ultimos4"],
                    "marca": fila["marca"]},
        "autorizacion": autorizacion,
    }


def main():
    with psycopg.connect(cadena_postgres()) as conexion:
        with conexion.cursor(row_factory=psycopg.rows.dict_row) as cursor:
            cursor.execute(CONSULTA)
            filas = cursor.fetchall()

    print(f"Filas leidas de PostgreSQL: {len(filas)}")

    with open(SALIDA_DATOS, "w", encoding="utf-8") as archivo:
        for fila in filas:
            archivo.write(json.dumps(construir_fila(fila),
                                     ensure_ascii=False) + "\n")

    with open(SALIDA_ESQUEMA, "w", encoding="utf-8") as archivo:
        json.dump(ESQUEMA, archivo, indent=2, ensure_ascii=False)

    tamano = os.path.getsize(SALIDA_DATOS) / 1024 / 1024
    print(f"Escrito {SALIDA_DATOS}: {tamano:.1f} MB")
    print(f"Escrito {SALIDA_ESQUEMA}")

    print("\n--- Verificacion ---")
    with open(SALIDA_DATOS, encoding="utf-8") as archivo:
        primera = json.loads(archivo.readline())
    print(f"Columnas de primer nivel: {len(primera)}")
    print(f"Subcolumnas de comercio:  {list(primera['comercio'])}")
    print(f"Senales del primer registro: "
          f"{primera.get('autorizacion', {}).get('riesgo', {}).get('senales')}")

    print("""
--- Carga en BigQuery ---

  bq mk --location=us-central1 --dataset PROYECTO:pagos

  bq load --source_format=NEWLINE_DELIMITED_JSON \\
     --time_partitioning_field=fecha_hora \\
     --time_partitioning_type=DAY \\
     --clustering_fields=estatus,metodo_captura \\
     PROYECTO:pagos.operaciones operaciones.ndjson esquema.json

  El particionamiento por fecha y el agrupamiento por estatus y metodo
  son el tema de la sesion: deciden cuanto se cobra por cada consulta.
""")


if __name__ == "__main__":
    main()
