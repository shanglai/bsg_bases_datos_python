"""
c2_s4_b2_payload.py
Genera el mensaje de autorizacion y lo agrega a la base como JSONB.

El modelo relacional de la sesion 1.2 captura lo que toda transaccion
tiene en comun. El mensaje de autorizacion es distinto: llega desde la
terminal con una estructura anidada, y los campos que trae dependen del
metodo de captura.

    CHIP         trae datos del criptograma y del emisor
    CONTACTLESS  igual que CHIP, mas el limite sin firma
    QR           trae el identificador del codigo y la aplicacion origen
    BANDA        trae menos campos, sin criptograma
    MANUAL       trae el motivo de la captura y el operador

Esa variabilidad es el argumento de la sesion: un esquema fijo obligaria
a declarar todas las columnas y dejarlas nulas casi siempre.

Requisitos: base pagos cargada, .env presente
Ejecucion:  python c2_s4_b2_payload.py
"""

import json
import os
import random
from datetime import timedelta

import psycopg
from dotenv import load_dotenv

SEMILLA = 987654
load_dotenv()
random.seed(SEMILLA)


def cadena():
    return (f"host={os.getenv('PGHOST', 'localhost')} "
            f"port={os.getenv('PGPORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DB')} "
            f"user={os.getenv('POSTGRES_USER')} "
            f"password={os.getenv('POSTGRES_PASSWORD')}")


CIUDADES = {
    "Ciudad de Mexico": (19.4326, -99.1332),
    "Monterrey": (25.6866, -100.3161),
    "Guadalajara": (20.6597, -103.3496),
    "Puebla": (19.0414, -98.2063),
    "Merida": (20.9674, -89.5926),
    "Cancun": (21.1619, -86.8515),
}

EMISORES = ["BANORTE", "BBVA", "SANTANDER", "HSBC", "SCOTIABANK", "BANAMEX"]
MOTIVOS_RECHAZO = ["FONDOS_INSUFICIENTES", "TARJETA_BLOQUEADA",
                   "NIP_INCORRECTO", "LIMITE_EXCEDIDO", "EMISOR_NO_DISPONIBLE"]
APLICACIONES_QR = ["CoDi", "MercadoPago", "BanorteMovil", "Clip"]


def hexa(n):
    return "".join(random.choice("0123456789ABCDEF") for _ in range(n))


def construir_payload(fila):
    """Arma el mensaje de autorizacion de una transaccion.

    La estructura comun esta siempre. El bloque 'captura' varia segun el
    metodo, y el bloque 'rechazo' solo existe cuando la operacion no fue
    aprobada.
    """
    (id_transaccion, fecha_hora, monto, estatus, metodo, ciudad) = fila

    lat, lon = CIUDADES.get(ciudad, (19.4326, -99.1332))
    lat += random.uniform(-0.05, 0.05)
    lon += random.uniform(-0.05, 0.05)

    payload = {
        "version": "2.1",
        "recibido_en": (fecha_hora + timedelta(milliseconds=random.randint(80, 900))
                        ).isoformat(),
        "emisor": {
            "nombre": random.choice(EMISORES),
            "pais": "MX",
            "tiempo_respuesta_ms": random.randint(120, 2400),
        },
        "dispositivo": {
            "serie": f"SN{hexa(10)}",
            "firmware": f"{random.randint(3, 6)}.{random.randint(0, 9)}."
                        f"{random.randint(0, 20)}",
            "ubicacion": {"lat": round(lat, 5), "lon": round(lon, 5)},
        },
        "captura": {"metodo": metodo},
        "riesgo": {
            "puntaje": random.randint(1, 100),
            "senales": random.sample(
                ["velocidad_alta", "geo_inusual", "monto_atipico",
                 "comercio_nuevo", "hora_inusual", "dispositivo_nuevo"],
                k=random.choice([0, 0, 0, 1, 1, 2, 3]),
            ),
        },
    }

    # El bloque de captura cambia por completo segun el metodo.
    if metodo in ("CHIP", "CONTACTLESS"):
        payload["captura"].update({
            "criptograma": hexa(16),
            "aid": "A0000000041010",
            "contador_aplicacion": random.randint(1, 9999),
        })
        if metodo == "CONTACTLESS":
            payload["captura"]["limite_sin_firma"] = random.choice([500, 1000, 1500])
    elif metodo == "QR":
        payload["captura"].update({
            "id_codigo": f"QR-{hexa(12)}",
            "aplicacion": random.choice(APLICACIONES_QR),
            "vigencia_segundos": random.choice([60, 120, 300]),
        })
    elif metodo == "BANDA":
        payload["captura"].update({
            "pista": random.choice([1, 2]),
            "lectura_degradada": random.random() < 0.15,
        })
    elif metodo == "MANUAL":
        payload["captura"].update({
            "motivo": random.choice(["FALLA_LECTOR", "TARJETA_DANADA",
                                     "OPERACION_TELEFONICA"]),
            "operador": f"OP{random.randint(100, 999)}",
        })

    if estatus != "APROBADA":
        payload["rechazo"] = {
            "codigo": random.choice(MOTIVOS_RECHAZO),
            "reintentable": random.choice([True, False]),
        }

    # Una fraccion de los mensajes llega de una version anterior del
    # protocolo, sin el bloque de riesgo. Es deliberado: en produccion
    # conviven versiones, y la consulta debe tolerarlo.
    if random.random() < 0.06:
        payload["version"] = "1.4"
        payload.pop("riesgo", None)

    return payload


def main():
    with psycopg.connect(cadena()) as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.columns
                WHERE table_schema = 'pagos' AND table_name = 'transacciones'
                  AND column_name = 'autorizacion'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "ALTER TABLE pagos.transacciones ADD COLUMN autorizacion JSONB")
                print("Columna autorizacion agregada (tipo JSONB).")
            else:
                print("La columna autorizacion ya existe. Se sobrescribe.")

            cursor.execute("""
                SELECT t.id_transaccion, t.fecha_hora, t.monto, t.estatus,
                       t.metodo_captura, c.ciudad
                FROM pagos.transacciones t
                JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
                JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
                ORDER BY t.id_transaccion
            """)
            filas = cursor.fetchall()
            print(f"Transacciones a procesar: {len(filas)}")

            datos = [(json.dumps(construir_payload(f)), f[0]) for f in filas]

            cursor.executemany(
                "UPDATE pagos.transacciones SET autorizacion = %s::jsonb "
                "WHERE id_transaccion = %s",
                datos,
            )
        conexion.commit()

        with conexion.cursor() as cursor:
            print("\n--- Verificacion ---")
            cursor.execute(
                "SELECT COUNT(*) FROM pagos.transacciones WHERE autorizacion IS NOT NULL")
            print(f"Mensajes cargados: {cursor.fetchone()[0]}")

            cursor.execute("""
                SELECT autorizacion->'captura'->>'metodo'            AS metodo,
                       COUNT(*)                                      AS mensajes,
                       STRING_AGG(DISTINCT campo, ', ' ORDER BY campo) AS campos
                FROM pagos.transacciones,
                     jsonb_object_keys(autorizacion->'captura') AS campo
                GROUP BY metodo
                ORDER BY mensajes DESC
            """)
            print("\nCampos del bloque captura, por metodo:")
            for metodo, mensajes, campos in cursor.fetchall():
                print(f"  {metodo:<12} {mensajes:>5} filas   {campos}")

            cursor.execute("""
                SELECT autorizacion->>'version' AS version, COUNT(*)
                FROM pagos.transacciones GROUP BY version ORDER BY 2 DESC
            """)
            print("\nVersiones del protocolo presentes:")
            for version, total in cursor.fetchall():
                print(f"  {version:<8} {total:>5}")

    print("\nCarga del mensaje de autorizacion completa.")


if __name__ == "__main__":
    main()
