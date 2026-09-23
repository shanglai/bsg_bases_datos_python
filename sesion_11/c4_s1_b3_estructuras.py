"""
c4_s1_b3_estructuras.py
Las estructuras de Redis, y para que sirve cada una.

Los tres motores anteriores guardan datos para consultarlos despues.
Redis guarda datos para responder en microsegundos, y esa diferencia de
proposito cambia todo lo demas.

Aqui no hay esquema, ni consulta, ni combinaciones. Hay una clave y un
valor, y el valor tiene una forma que se elige segun la operacion que se
va a hacer sobre el.

Requisitos: contenedor de Redis activo, .env presente
    pip install redis python-dotenv
Ejecucion:  python c4_s1_b3_estructuras.py
"""

import os
import time

import redis
from dotenv import load_dotenv

load_dotenv(override=True)
PREFIJO = "demo"


def conectar():
    """Devuelve un cliente de Redis.

    decode_responses=True hace que las respuestas lleguen como cadenas
    de Python en lugar de bytes. Sin eso, todo valor devuelto es b'...'
    y hay que decodificarlo a mano.
    """
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD") or None,
        decode_responses=True,
    )


def titulo(texto):
    print("\n" + "=" * 70 + f"\n{texto}\n" + "=" * 70)


def limpiar(r):
    """Elimina solo las claves de esta demostracion.

    Se usa SCAN y no KEYS. KEYS recorre el espacio completo de claves y
    bloquea el servidor mientras lo hace. En una base con millones de
    claves, ejecutarlo en produccion es un incidente.
    """
    for clave in r.scan_iter(match=f"{PREFIJO}:*", count=500):
        r.delete(clave)


# =====================================================================
# Bloque 1. La diferencia de proposito
# =====================================================================

def bloque_1_proposito(r):
    titulo("Bloque 1: Redis no es una base de datos mas")

    print("""
  Los tres motores anteriores responden la pregunta "que datos tengo".
  Redis responde "cual es el valor de esta clave", y lo hace en
  microsegundos porque todo vive en memoria.

  Consecuencias de esa decision de diseno:

    No hay lenguaje de consulta. Se accede por clave, no por contenido.
    No hay esquema, ni tablas, ni colecciones.
    No hay combinaciones.
    La memoria es el limite, y es mas cara que el disco.
    Si el servidor se reinicia sin persistencia configurada, se pierde
      todo.

  Ese ultimo punto es el que define su uso: Redis se usa para datos que
  se pueden reconstruir. Una cache, un contador, una cola. No para el
  registro de la transaccion.
""")

    informacion = r.info("server")
    print(f"  Version del servidor: {informacion.get('redis_version')}")
    memoria = r.info("memory")
    print(f"  Memoria en uso: {memoria.get('used_memory_human')}")


# =====================================================================
# Bloque 2. Cadenas
# =====================================================================

def bloque_2_cadenas(r):
    titulo("Bloque 2: cadenas, el tipo basico")

    r.set(f"{PREFIJO}:saludo", "hola")
    print(f"\n  GET: {r.get(f'{PREFIJO}:saludo')}")

    # La expiracion es una propiedad de la clave, no del valor.
    r.set(f"{PREFIJO}:temporal", "desaparezco", ex=2)
    print(f"  TTL de la clave temporal: {r.ttl(f'{PREFIJO}:temporal')} segundos")
    time.sleep(2.2)
    print(f"  Tras esperar: {r.get(f'{PREFIJO}:temporal')}")

    # Los contadores son atomicos, que es la razon de usarlos aqui.
    clave = f"{PREFIJO}:intentos:tarjeta:42"
    r.delete(clave)
    for _ in range(5):
        valor = r.incr(clave)
    print(f"\n  Tras cinco INCR: {valor}")

    print("""
  INCR es atomico. Dos procesos que incrementen la misma clave al mismo
  tiempo no se pisan, y ninguno necesita bloquear nada.

  En PostgreSQL, el equivalente seria SELECT, sumar y UPDATE dentro de
  una transaccion, o bien UPDATE ... SET n = n + 1. Funciona, y cuesta
  mucho mas.

  Este es el caso de uso mas comun de Redis en un sistema de pagos:
  contar intentos por tarjeta para limitar la frecuencia.
""")

    # SETNX escribe solo si la clave no existe. Es la base de un cerrojo.
    clave = f"{PREFIJO}:cerrojo:conciliacion"
    r.delete(clave)
    primero = r.set(clave, "proceso-A", nx=True, ex=10)
    segundo = r.set(clave, "proceso-B", nx=True, ex=10)
    print(f"  Primer intento de tomar el cerrojo: {primero}")
    print(f"  Segundo intento:                    {segundo}")

    print("""
  set con nx=True escribe solo si la clave NO existe, y la operacion es
  atomica. Es el mecanismo de un cerrojo distribuido elemental.

  Advertencia honesta: un cerrojo correcto necesita mas que esto. Hace
  falta que el valor identifique al dueno, que la liberacion verifique
  ese dueno, y que la expiracion cubra el peor tiempo de ejecucion. Con
  varios nodos de Redis, el problema es considerablemente mas dificil.
""")


# =====================================================================
# Bloque 3. Diccionarios
# =====================================================================

def bloque_3_diccionarios(r):
    titulo("Bloque 3: diccionarios, para objetos con campos")

    clave = f"{PREFIJO}:perfil:tarjeta:42"
    r.delete(clave)
    r.hset(clave, mapping={
        "puntaje_riesgo": 37,
        "operaciones_30d": 128,
        "monto_promedio": "1842.50",
        "marca": "VISA",
        "ultima_revision": "2026-06-30",
    })

    print(f"\n  Todo el diccionario: {r.hgetall(clave)}")
    print(f"  Un solo campo:       {r.hget(clave, 'puntaje_riesgo')}")
    print(f"  Varios campos:       "
          f"{r.hmget(clave, ['puntaje_riesgo', 'marca'])}")

    r.hincrby(clave, "operaciones_30d", 1)
    print(f"  Tras HINCRBY:        {r.hget(clave, 'operaciones_30d')}")

    print("""
  El diccionario permite leer o modificar UN campo sin traer ni
  reescribir el objeto completo.

  La alternativa seria guardar el perfil como JSON en una cadena. Leer
  un campo obligaria a traer todo el documento y a decodificarlo, y
  modificarlo obligaria a reescribirlo entero, con el riesgo de pisar un
  cambio concurrente.

  Advertencia sobre tipos: Redis almacena cadenas. El 37 que se guardo
  como numero regresa como texto '37'. La conversion la hace el codigo,
  siempre.
""")

    puntaje = int(r.hget(clave, "puntaje_riesgo"))
    print(f"  Tipo al leer: {type(r.hget(clave, 'puntaje_riesgo')).__name__}, "
          f"tras convertir: {type(puntaje).__name__}")


# =====================================================================
# Bloque 4. Listas y conjuntos
# =====================================================================

def bloque_4_listas_conjuntos(r):
    titulo("Bloque 4: listas y conjuntos")

    # Lista: orden de insercion, admite repetidos, sirve como cola.
    cola = f"{PREFIJO}:cola:revision"
    r.delete(cola)
    for identificador in ["TRX001", "TRX002", "TRX003"]:
        r.rpush(cola, identificador)
    print(f"\n  Lista completa: {r.lrange(cola, 0, -1)}")
    print(f"  Sacar el primero (LPOP): {r.lpop(cola)}")
    print(f"  Queda: {r.lrange(cola, 0, -1)}")

    # Conjunto: sin orden, sin repetidos, pertenencia inmediata.
    conjunto = f"{PREFIJO}:tarjetas:bloqueadas"
    r.delete(conjunto)
    r.sadd(conjunto, "4417", "8823", "4417", "1102")
    print(f"\n  Conjunto: {sorted(r.smembers(conjunto))}")
    print(f"  Esta '4417' en el conjunto: {r.sismember(conjunto, '4417')}")
    print(f"  Esta '9999': {r.sismember(conjunto, '9999')}")

    print("""
  La diferencia entre lista y conjunto es la misma de Python:

    Lista     conserva el orden, admite repetidos, sirve como cola
    Conjunto  sin orden, sin repetidos, pertenencia inmediata

  El conjunto responde "esta esta tarjeta bloqueada" sin recorrer nada.
  En PostgreSQL, esa misma pregunta exige un indice y una consulta.
""")


# =====================================================================
# Bloque 5. Conjuntos ordenados
# =====================================================================

def bloque_5_ordenados(r):
    titulo("Bloque 5: conjuntos ordenados, la estructura distintiva")

    ranking = f"{PREFIJO}:ranking:comercios"
    r.delete(ranking)
    r.zadd(ranking, {
        "Super Norteno": 2217958.06,
        "Viajes Altamar": 2938402.49,
        "Electro Maya": 2378339.96,
        "Boutique Iris": 1542762.30,
        "Cafe Aurora": 198082.83,
    })

    print("\n  Los tres primeros:")
    for nombre, puntaje in r.zrevrange(ranking, 0, 2, withscores=True):
        print(f"    {nombre:<20} {puntaje:>14,.2f}")

    print(f"\n  Posicion de Electro Maya: "
          f"{r.zrevrank(ranking, 'Electro Maya') + 1}")
    print(f"  Cuantos superan 2 millones: "
          f"{r.zcount(ranking, 2_000_000, '+inf')}")

    r.zincrby(ranking, 500000, "Cafe Aurora")
    print(f"  Tras sumar 500000 a Cafe Aurora, su posicion: "
          f"{r.zrevrank(ranking, 'Cafe Aurora') + 1}")

    print("""
  El conjunto ordenado mantiene el orden por puntaje de forma
  permanente. Consultar el ranking no requiere ordenar: ya esta
  ordenado.

  Es la estructura que no tiene equivalente comodo en los otros motores.
  En PostgreSQL, un ranking actualizado al momento exige recalcular una
  agregacion o mantener una tabla con disparadores.

  Usos tipicos en el caso: comercios por volumen del dia, tarjetas por
  puntaje de riesgo, operaciones pendientes por antiguedad.
""")


# =====================================================================
# Bloque 6. Elegir la estructura
# =====================================================================

def bloque_6_criterio(r):
    titulo("Bloque 6: la estructura se elige por la operacion")

    print("""
  Estructura        Cuando                              Operacion tipica
  ----------------  ----------------------------------  ----------------
  Cadena            Un valor suelto, un contador        GET, INCR
  Diccionario       Un objeto con campos que se leen    HGET, HINCRBY
                    o modifican por separado
  Lista             Orden de llegada, cola               RPUSH, LPOP
  Conjunto          Pertenencia, sin repetidos           SADD, SISMEMBER
  Conjunto ordenado Ranking, rango por puntaje           ZADD, ZREVRANGE

  El criterio es la operacion, no el dato. El mismo perfil de riesgo
  puede guardarse como cadena con JSON o como diccionario; la eleccion
  depende de si se lee completo o por campos.

  Regla practica: elegir la estructura que hace la operacion habitual en
  un solo comando.
""")

    print("  Claves de la demostracion, por tipo:")
    for clave in sorted(r.scan_iter(match=f"{PREFIJO}:*", count=100)):
        print(f"    {r.type(clave):<12} {clave}")


if __name__ == "__main__":
    cliente = conectar()
    cliente.ping()
    limpiar(cliente)

    bloque_1_proposito(cliente)
    bloque_2_cadenas(cliente)
    bloque_3_diccionarios(cliente)
    bloque_4_listas_conjuntos(cliente)
    bloque_5_ordenados(cliente)
    bloque_6_criterio(cliente)

    limpiar(cliente)
    print("\nClaves de la demostracion eliminadas.")
