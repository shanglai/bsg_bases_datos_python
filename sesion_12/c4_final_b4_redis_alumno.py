"""
c4_final_b4_redis_alumno.py
Ejercicio de Redis, para ejecutar en Cloud Shell.

NO HAY QUE INSTALAR NADA.

  1. Abrir Cloud Shell en la consola de GCP, con el icono de terminal
     arriba a la derecha.
  2. pip install redis --quiet
  3. Pegar este archivo y ejecutarlo con los datos que le dio el
     instructor.

     python c4_final_b4_redis_alumno.py HOST USUARIO CLAVE

Cada participante tiene su propio usuario y solo puede escribir claves
que empiecen con su nombre de usuario. Intentar tocar las de otro
devuelve NOPERM, y eso es a proposito: es la forma de hacer
multi-tenencia en un almacen que no tiene esquemas.
"""

import sys
import time

try:
    import redis
except ImportError:
    raise SystemExit("Falta el controlador. Ejecuta: pip install redis --quiet")

if len(sys.argv) < 4:
    raise SystemExit(
        "Uso: python c4_final_b4_redis_alumno.py HOST USUARIO CLAVE")

HOST, USUARIO, CLAVE = sys.argv[1], sys.argv[2], sys.argv[3]
P = f"{USUARIO}:"          # todas las claves llevan este prefijo


def titulo(texto):
    print("\n" + "=" * 68 + f"\n{texto}\n" + "=" * 68)


r = redis.Redis(host=HOST, port=6379, username=USUARIO, password=CLAVE,
                decode_responses=True, socket_timeout=10)
r.ping()
print(f"Conectado como {USUARIO}. Tus claves llevan el prefijo '{P}'")


# =====================================================================
# 1. Las cinco estructuras
# =====================================================================

titulo("1. Las cinco estructuras, en un recorrido")

# Cadena, y el contador atomico.
r.delete(f"{P}intentos")
for _ in range(5):
    valor = r.incr(f"{P}intentos")
print(f"  Cadena, contador tras cinco INCR: {valor}")

# Diccionario: un objeto con campos que se leen por separado.
r.delete(f"{P}perfil")
r.hset(f"{P}perfil", mapping={"puntaje": 37, "operaciones": 128,
                              "marca": "VISA"})
print(f"  Diccionario, un solo campo: {r.hget(f'{P}perfil', 'marca')}")
r.hincrby(f"{P}perfil", "operaciones", 1)
print(f"  Diccionario, tras HINCRBY:  "
      f"{r.hget(f'{P}perfil', 'operaciones')}")

# Lista: orden de llegada, sirve como cola.
r.delete(f"{P}cola")
r.rpush(f"{P}cola", "TRX001", "TRX002", "TRX003")
print(f"  Lista, LPOP devuelve el primero: {r.lpop(f'{P}cola')}")

# Conjunto: pertenencia inmediata.
r.delete(f"{P}bloqueadas")
r.sadd(f"{P}bloqueadas", "4417", "8823", "4417")
print(f"  Conjunto, sin repetidos: {sorted(r.smembers(f'{P}bloqueadas'))}")
print(f"  Conjunto, '4417' bloqueada: "
      f"{bool(r.sismember(f'{P}bloqueadas', '4417'))}")

# Conjunto ordenado: ranking que se mantiene solo.
r.delete(f"{P}ranking")
r.zadd(f"{P}ranking", {"Viajes Altamar": 2938402.49,
                       "Electro Maya": 2378339.96,
                       "Super Norteno": 2217958.06,
                       "Cafe Aurora": 198082.83})
print("  Conjunto ordenado, los dos primeros:")
for nombre, puntaje in r.zrevrange(f"{P}ranking", 0, 1, withscores=True):
    print(f"    {nombre:<18} {puntaje:>14,.2f}")


# =====================================================================
# 2. La expiracion
# =====================================================================

titulo("2. La expiracion es una propiedad de la clave")

r.set(f"{P}temporal", "desaparezco", ex=3)
print(f"  TTL recien puesta: {r.ttl(f'{P}temporal')} s")
time.sleep(3.2)
print(f"  Tras esperar:      {r.get(f'{P}temporal')}")

print("""
  Ningun otro motor del curso tiene esto. En PostgreSQL habria que
  guardar una fecha de caducidad y borrar con un proceso aparte.
""")


# =====================================================================
# 3. El limitador de intentos
# =====================================================================

titulo("3. Un limitador, que es el caso de uso real")


def intentos_recientes(id_tarjeta, ventana=60):
    """INCR es atomico: dos procesos simultaneos no se pisan.

    Solo el primero recibe 1, y solo ese fija la expiracion.
    """
    clave = f"{P}limite:{id_tarjeta}"
    valor = r.incr(clave)
    if valor == 1:
        r.expire(clave, ventana)
    return valor


r.delete(f"{P}limite:99")
print()
for i in range(6):
    n = intentos_recientes(99)
    estado = "RECHAZADO" if n > 5 else "permitido"
    print(f"  intento {i + 1}: contador {n}, {estado}")

print("""
  Por que funciona con concurrencia: INCR es atomico. Sin esa garantia,
  dos procesos podrian leer el mismo valor, sumar uno y escribir lo
  mismo, perdiendo un intento.
""")


# =====================================================================
# 4. El aislamiento entre participantes
# =====================================================================

titulo("4. Lo que NO puedes hacer, y por que")

vecino = "alumno01:" if USUARIO != "alumno01" else "alumno02:"

pruebas = [
    ("Escribir en el prefijo de otro", lambda: r.set(f"{vecino}x", "1")),
    ("Borrar la base completa", lambda: r.flushall()),
    ("Listar todas las claves con KEYS", lambda: r.keys("*")),
    ("Leer la configuracion del servidor", lambda: r.config_get("maxmemory")),
]

print()
for etiqueta, accion in pruebas:
    try:
        accion()
        print(f"  PERMITIDO  {etiqueta}")
    except redis.exceptions.ResponseError as error:
        print(f"  RECHAZADO  {etiqueta:<36} {str(error)[:34]}")

print("""
  Cada participante tiene un usuario con ACL restringido a su prefijo.

  Es la forma de hacer multi-tenencia en un almacen clave-valor: no hay
  esquemas ni bases separadas por permiso, de modo que el aislamiento se
  consigue por convencion de nombres mas permisos.

  Notese que KEYS esta prohibido para todos. Recorre el espacio completo
  de claves y bloquea el servidor mientras lo hace. Se usa SCAN.
""")

print("  Tus claves, con SCAN:")
for clave in sorted(r.scan_iter(match=f"{P}*", count=50)):
    print(f"    {r.type(clave):<10} {clave}")


# =====================================================================
# 5. Limpieza
# =====================================================================

titulo("5. Limpieza")

borradas = 0
for clave in list(r.scan_iter(match=f"{P}*", count=100)):
    r.delete(clave)
    borradas += 1
print(f"\n  Claves eliminadas: {borradas}")
print("\n  Ejercicio terminado.")
