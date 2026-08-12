"""
c1_s1_b2_generar_datos.py
Genera el conjunto de datos del caso de estudio en su forma plana.

Este archivo representa el punto de partida del curso: una sola tabla con
redundancia e inconsistencias, tal como suele llegar un extracto operativo.
La normalizacion de este archivo es el trabajo de la sesion 1.2.

Ejecucion: python c1_s1_b2_generar_datos.py
Salida:
    pagos_plano.csv     archivo plano con las transacciones
    pagos.db            base SQLite con una unica tabla llamada movimientos
"""

import csv
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

SEMILLA = 987654
N_TRANSACCIONES = 5000
ARCHIVO_CSV = Path("pagos_plano.csv")
ARCHIVO_DB = Path("pagos.db")

random.seed(SEMILLA)

# Cada comercio se declara con variantes de escritura y de categoria.
# Esa inconsistencia es deliberada y es el material de la sesion 1.2.
COMERCIOS = [
    {
        "variantes": ["Farmacia del Sol", "FARMACIA DEL SOL", "Farmacia del Sol "],
        "categorias": ["Farmacia", "farmacia", "FARM"],
        "ciudad": "Ciudad de Mexico",
        "ticket": (120, 900),
        "peso": 22,
    },
    {
        "variantes": ["Super Norteno", "SUPER NORTENO", "Super Nortenio"],
        "categorias": ["Supermercado", "supermercado", "SUPER"],
        "ciudad": "Monterrey",
        "ticket": (200, 3500),
        "peso": 30,
    },
    {
        "variantes": ["Cafe Aurora", "CAFE AURORA"],
        "categorias": ["Restaurante", "restaurante"],
        "ciudad": "Guadalajara",
        "ticket": (60, 480),
        "peso": 18,
    },
    {
        "variantes": ["Boutique Iris", "BOUTIQUE IRIS", "Boutique  Iris"],
        "categorias": ["Ropa", "ropa", "VESTIMENTA"],
        "ciudad": "Ciudad de Mexico",
        "ticket": (400, 6000),
        "peso": 12,
    },
    {
        "variantes": ["Gasolinera Km 12", "GASOLINERA KM 12"],
        "categorias": ["Combustible", "combustible"],
        "ciudad": "Puebla",
        "ticket": (300, 1800),
        "peso": 10,
    },
    {
        "variantes": ["Electro Maya", "ELECTRO MAYA"],
        "categorias": ["Electronica", "electronica", "ELECTRO"],
        "ciudad": "Merida",
        "ticket": (900, 24000),
        "peso": 5,
    },
    {
        "variantes": ["Viajes Altamar", "VIAJES ALTAMAR"],
        "categorias": ["Viajes", "viajes"],
        "ciudad": "Cancun",
        "ticket": (3000, 45000),
        "peso": 3,
    },
]

NOMBRES = ["Ana", "Luis", "Sofia", "Miguel", "Carmen", "Jorge", "Elena", "Raul",
           "Patricia", "Hector", "Lucia", "Fernando", "Rocio", "Ivan", "Teresa"]
APELLIDOS = ["Ramirez", "Gonzalez", "Herrera", "Mendoza", "Cortes", "Nunez",
             "Salazar", "Vargas", "Trejo", "Rivas", "Zamora", "Delgado"]

MARCAS = ["VISA", "MASTERCARD", "AMEX"]
CAPTURAS = ["CHIP", "CONTACTLESS", "BANDA", "QR", "MANUAL"]
ESTATUS = ["APROBADA", "APROBADA", "APROBADA", "APROBADA", "APROBADA",
           "APROBADA", "APROBADA", "RECHAZADA", "REVERSADA"]


def construir_clientes(n=180):
    """Crea el padron de clientes con sus tarjetas."""
    clientes = []
    for i in range(1, n + 1):
        nombre = f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)}"
        correo = nombre.lower().replace(" ", ".") + f"{i}@correo.mx"
        clientes.append({
            "nombre": nombre,
            "correo": correo,
            "tarjetas": [
                {
                    "ultimos4": f"{random.randint(1000, 9999)}",
                    "marca": random.choice(MARCAS),
                }
                for _ in range(random.choice([1, 1, 1, 2]))
            ],
        })
    return clientes


def elegir_comercio():
    """Selecciona un comercio con distribucion sesgada.

    La concentracion del volumen en pocos comercios es realista y ademas es
    necesaria: con una distribucion uniforme, el efecto de un indice sobre
    la consulta no se aprecia. Este punto se retoma en la sesion 2.5.
    """
    pesos = [c["peso"] for c in COMERCIOS]
    return random.choices(COMERCIOS, weights=pesos, k=1)[0]


def generar_filas():
    clientes = construir_clientes()
    inicio = datetime(2026, 1, 1, 6, 0, 0)
    filas = []

    for i in range(1, N_TRANSACCIONES + 1):
        comercio = elegir_comercio()
        cliente = random.choice(clientes)
        tarjeta = random.choice(cliente["tarjetas"])

        momento = inicio + timedelta(
            days=random.randint(0, 179),
            hours=random.randint(0, 15),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )

        piso, techo = comercio["ticket"]
        monto = round(random.uniform(piso, techo), 2)
        estatus = random.choice(ESTATUS)

        # El contracargo solo tiene sentido sobre una operacion aprobada.
        contracargo = "S" if (estatus == "APROBADA" and random.random() < 0.012) else "N"

        filas.append({
            "id_transaccion": f"TRX{i:07d}",
            "fecha_hora": momento.strftime("%Y-%m-%d %H:%M:%S"),
            "comercio": random.choice(comercio["variantes"]),
            "categoria_comercio": random.choice(comercio["categorias"]),
            "ciudad_comercio": comercio["ciudad"],
            "terminal": f"TPV{random.randint(1, 4):02d}-{comercio['ciudad'][:3].upper()}",
            "cliente": cliente["nombre"],
            "correo_cliente": cliente["correo"],
            "tarjeta_ultimos4": tarjeta["ultimos4"],
            "marca_tarjeta": tarjeta["marca"],
            "monto": monto,
            "moneda": "MXN",
            "estatus": estatus,
            "metodo_captura": random.choice(CAPTURAS),
            "contracargo": contracargo,
        })

    return filas


def escribir_csv(filas):
    with ARCHIVO_CSV.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"Archivo plano escrito: {ARCHIVO_CSV} ({len(filas)} filas)")


def escribir_sqlite(filas):
    if ARCHIVO_DB.exists():
        ARCHIVO_DB.unlink()

    conexion = sqlite3.connect(ARCHIVO_DB)
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE movimientos (
            id_transaccion     TEXT,
            fecha_hora         TEXT,
            comercio           TEXT,
            categoria_comercio TEXT,
            ciudad_comercio    TEXT,
            terminal           TEXT,
            cliente            TEXT,
            correo_cliente     TEXT,
            tarjeta_ultimos4   TEXT,
            marca_tarjeta      TEXT,
            monto              REAL,
            moneda             TEXT,
            estatus            TEXT,
            metodo_captura     TEXT,
            contracargo        TEXT
        )
    """)

    cursor.executemany(
        """INSERT INTO movimientos VALUES
           (:id_transaccion, :fecha_hora, :comercio, :categoria_comercio,
            :ciudad_comercio, :terminal, :cliente, :correo_cliente,
            :tarjeta_ultimos4, :marca_tarjeta, :monto, :moneda, :estatus,
            :metodo_captura, :contracargo)""",
        filas,
    )

    conexion.commit()
    conexion.close()
    print(f"Base SQLite escrita: {ARCHIVO_DB} (tabla movimientos)")


if __name__ == "__main__":
    filas = generar_filas()
    escribir_csv(filas)
    escribir_sqlite(filas)
