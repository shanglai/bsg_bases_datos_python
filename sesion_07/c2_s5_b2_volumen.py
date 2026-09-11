"""
c2_s5_b2_volumen.py
Genera la tabla de volumen alto para el estudio de indices y planes.

Las cinco mil transacciones del caso responden de inmediato a cualquier
consulta, de modo que el efecto de un indice no se aprecia. Esta sesion
necesita volumen.

La tabla se construye dentro del motor con generate_series. No hay
transferencia de datos desde Python, de modo que dos millones de filas
tardan segundos en lugar de minutos.

Dos decisiones deliberadas:

    La distribucion por comercio es sesgada, con la misma ponderacion
    que el generador de la sesion 1.1. Con una distribucion uniforme, el
    planificador estima mal y el efecto del indice no se aprecia como en
    un sistema real.

    La tabla es independiente de pagos.transacciones y no lleva llaves
    foraneas. El proposito es medir, no modelar. El modelo ya se estudio
    en el capitulo 1.

Requisitos: base pagos cargada, .env presente
Ejecucion:  python c2_s5_b2_volumen.py [numero_de_filas]
            por omision, 2000000
"""

import os
import sys
import time

import psycopg
from dotenv import load_dotenv

load_dotenv()

FILAS = int(sys.argv[1]) if len(sys.argv) > 1 else 2_000_000

# Misma ponderacion que el generador de la sesion 1.1.
PESOS = {
    "Super Norteno": 30,
    "Farmacia Del Sol": 22,
    "Cafe Aurora": 18,
    "Boutique Iris": 12,
    "Gasolinera Km 12": 10,
    "Electro Maya": 5,
    "Viajes Altamar": 3,
}


def cadena():
    return (f"host={os.getenv('PGHOST', 'localhost')} "
            f"port={os.getenv('PGPORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DB')} "
            f"user={os.getenv('POSTGRES_USER')} "
            f"password={os.getenv('POSTGRES_PASSWORD')}")


def clausula_pesos():
    partes = " ".join(f"WHEN '{nombre}' THEN {peso}" for nombre, peso in PESOS.items())
    return f"CASE c.nombre {partes} ELSE 3 END"


CONSULTA = """
DROP TABLE IF EXISTS pagos.transacciones_volumen;

CREATE TABLE pagos.transacciones_volumen AS
WITH terminales_ponderadas AS (
    -- Cada terminal aparece tantas veces como su ponderacion, de modo
    -- que al elegir una al azar la distribucion queda sesgada.
    SELECT te.id_terminal,
           ROW_NUMBER() OVER (ORDER BY te.id_terminal, s) AS n
    FROM pagos.terminales te
    JOIN pagos.comercios c USING (id_comercio),
         LATERAL generate_series(1, {pesos}) s
),
base AS (
    -- El indice aleatorio se calcula aqui, una vez por fila.
    -- Calcularlo dentro de la condicion del JOIN haria que el motor lo
    -- evalue una sola vez y todas las filas caerian en la misma
    -- terminal. Es un error facil de cometer y dificil de notar.
    SELECT g,
           1 + floor(random() * (SELECT COUNT(*) FROM terminales_ponderadas))::INT
               AS indice,
           TIMESTAMP '2026-01-01' + (random() * 180) * INTERVAL '1 day'
               AS fecha_hora,
           1 + floor(random() * 219)::INT           AS id_tarjeta,
           round((random() * 5000 + 50)::NUMERIC, 2) AS monto,
           CASE WHEN random() < 0.08 THEN 'RECHAZADA' ELSE 'APROBADA' END
               AS estatus,
           (ARRAY['CHIP', 'CONTACTLESS', 'BANDA', 'QR', 'MANUAL'])
               [1 + floor(random() * 5)::INT]       AS metodo_captura
    FROM generate_series(1, {filas}) g
)
SELECT 'TRXV' || LPAD(b.g::TEXT, 9, '0') AS id_transaccion,
       b.fecha_hora,
       tp.id_terminal,
       b.id_tarjeta,
       b.monto,
       b.estatus,
       b.metodo_captura
FROM base b
JOIN terminales_ponderadas tp ON tp.n = b.indice;
"""


def main():
    print(f"Generando {FILAS:,} filas dentro del motor...")

    with psycopg.connect(cadena()) as conexion:
        conexion.autocommit = True

        inicio = time.perf_counter()
        conexion.execute(CONSULTA.format(pesos=clausula_pesos(), filas=FILAS))
        transcurrido = time.perf_counter() - inicio
        print(f"Tabla creada en {transcurrido:.1f} s")

        # VACUUM ANALYZE hace dos cosas: recopila estadisticas de
        # distribucion, y actualiza el mapa de visibilidad.
        #
        # Sin estadisticas, el planificador estima a ciegas y elige mal.
        #
        # Sin mapa de visibilidad actualizado, un Index Only Scan no es
        # posible: el motor debe visitar la tabla para comprobar que
        # cada fila es visible, y el plan degrada a Bitmap Heap Scan.
        # Es la causa de que un indice de cobertura recien creado a
        # veces no produzca el plan esperado.
        conexion.execute("VACUUM ANALYZE pagos.transacciones_volumen")
        print("Estadisticas y mapa de visibilidad actualizados "
              "con VACUUM ANALYZE.")

        print("\n--- Verificacion ---")
        total = conexion.execute(
            "SELECT COUNT(*) FROM pagos.transacciones_volumen").fetchone()[0]
        tamano = conexion.execute(
            "SELECT pg_size_pretty(pg_total_relation_size("
            "'pagos.transacciones_volumen'))").fetchone()[0]
        print(f"Filas:  {total:,}")
        print(f"Tamano: {tamano}")

        print("\nDistribucion por comercio:")
        filas = conexion.execute("""
            SELECT c.nombre, COUNT(*) AS operaciones,
                   ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
            FROM pagos.transacciones_volumen v
            JOIN pagos.terminales te ON te.id_terminal = v.id_terminal
            JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
            GROUP BY c.nombre ORDER BY operaciones DESC
        """).fetchall()
        for nombre, operaciones, pct in filas:
            print(f"  {nombre:<20} {operaciones:>10,}  {pct:>5}%")

        indices = conexion.execute("""
            SELECT indexname FROM pg_indexes
            WHERE schemaname = 'pagos' AND tablename = 'transacciones_volumen'
        """).fetchall()
        print(f"\nIndices sobre la tabla: {len(indices)}")
        print("La tabla se entrega sin indices. Crearlos es el ejercicio "
              "de la sesion.")


if __name__ == "__main__":
    main()
