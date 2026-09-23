"""
c4_s1_b4_cache.py
La cache del perfil de riesgo.

El caso de uso que justifica Redis en un sistema de pagos: al autorizar
una operacion hay que consultar el perfil de riesgo de la tarjeta, y esa
consulta ocurre en cada transaccion.

Calcularla contra PostgreSQL cada vez es correcto y lento. Guardarla en
Redis es rapido y plantea un problema nuevo: cuando deja de ser valida.

Requisitos: PostgreSQL con el caso cargado, Redis activo, .env
Ejecucion:  python c4_s1_b4_cache.py
"""

import json
import os
import time

import psycopg
import redis
from dotenv import load_dotenv

load_dotenv(override=True)
PREFIJO = "perfil"
VIGENCIA = 300          # segundos


def cadena_postgres():
    return (f"host={os.getenv('PGHOST', 'localhost')} "
            f"port={os.getenv('PGPORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DB')} "
            f"user={os.getenv('POSTGRES_USER')} "
            f"password={os.getenv('POSTGRES_PASSWORD')}")


def conectar_redis():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD") or None,
        decode_responses=True,
    )


def titulo(texto):
    print("\n" + "=" * 70 + f"\n{texto}\n" + "=" * 70)


CONSULTA_PERFIL = """
    SELECT COUNT(*)                        AS operaciones,
           COALESCE(SUM(t.monto), 0)       AS gasto,
           COALESCE(ROUND(AVG(t.monto), 2), 0) AS ticket,
           COUNT(*) FILTER (WHERE t.estatus = 'RECHAZADA') AS rechazos
    FROM pagos.transacciones t
    WHERE t.id_tarjeta = %s
"""


def calcular_perfil(conexion, id_tarjeta):
    """El calculo real, contra PostgreSQL."""
    operaciones, gasto, ticket, rechazos = conexion.execute(
        CONSULTA_PERFIL, (id_tarjeta,)).fetchone()
    return {
        "id_tarjeta": id_tarjeta,
        "operaciones": operaciones,
        "gasto": float(gasto),
        "ticket_promedio": float(ticket),
        "rechazos": rechazos,
        "calculado_en": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


# =====================================================================
# Bloque 1. Sin cache
# =====================================================================

def bloque_1_sin_cache(conexion):
    titulo("Bloque 1: cada consulta va a PostgreSQL")

    tarjetas = list(range(1, 51))

    inicio = time.perf_counter()
    for id_tarjeta in tarjetas:
        calcular_perfil(conexion, id_tarjeta)
    transcurrido = time.perf_counter() - inicio

    print(f"\n  {len(tarjetas)} perfiles calculados en "
          f"{transcurrido * 1000:.0f} ms")
    print(f"  Promedio por perfil: {transcurrido / len(tarjetas) * 1000:.2f} ms")

    print("""
  Conviene retener este numero, porque el bloque 5 lo va a usar para
  llegar a una conclusion que no es la esperada.

  En terminos absolutos esto no es lento. La consulta usa el indice
  sobre id_tarjeta creado en la sesion 2.1, y los datos caben en
  memoria.

  El argumento habitual para justificar una cache es que esta consulta
  ocurre en CADA autorizacion y que la autorizacion tiene un presupuesto
  de tiempo estricto. Es un argumento razonable; el bloque 5 examina si
  los numeros lo respaldan en este caso concreto.
""")
    return transcurrido


# =====================================================================
# Bloque 2. Con cache
# =====================================================================

def perfil_con_cache(r, conexion, id_tarjeta, vigencia=VIGENCIA):
    """El patron de cache mas comun: buscar, y si no esta, calcular.

    Se le llama cache-aside. La aplicacion consulta primero la cache; si
    el dato no esta, lo calcula, lo guarda y lo devuelve.

    Es el patron correcto para este caso porque el dato es derivado: si
    la cache se pierde, se reconstruye sola.
    """
    clave = f"{PREFIJO}:tarjeta:{id_tarjeta}"

    guardado = r.get(clave)
    if guardado is not None:
        return json.loads(guardado), "cache"

    perfil = calcular_perfil(conexion, id_tarjeta)
    r.set(clave, json.dumps(perfil), ex=vigencia)
    return perfil, "calculado"


def bloque_2_con_cache(r, conexion, referencia):
    titulo("Bloque 2: con cache")

    tarjetas = list(range(1, 51))
    for id_tarjeta in tarjetas:
        r.delete(f"{PREFIJO}:tarjeta:{id_tarjeta}")

    inicio = time.perf_counter()
    for id_tarjeta in tarjetas:
        perfil_con_cache(r, conexion, id_tarjeta)
    primera = time.perf_counter() - inicio

    inicio = time.perf_counter()
    for id_tarjeta in tarjetas:
        perfil_con_cache(r, conexion, id_tarjeta)
    segunda = time.perf_counter() - inicio

    print(f"\n  Primera pasada, cache vacia:  {primera * 1000:7.0f} ms")
    print(f"  Segunda pasada, cache llena:  {segunda * 1000:7.0f} ms")
    print(f"  Relacion: {primera / segunda:.0f} veces")

    print(f"""
  La primera pasada es mas lenta que sin cache ({referencia * 1000:.0f} ms),
  porque ademas de calcular escribe en Redis. Ese costo se paga una vez.

  La segunda no toca PostgreSQL. Esa es la razon de existir de la cache.

  Advertencia sobre la medicion: se cronometra una sola pasada de cada
  tipo, no el minimo de varias. Sirve para ver el orden de magnitud, no
  como medicion rigurosa. El criterio de la sesion 2.5 aplica igual
  aqui.

  Notese ya algo: la primera pasada resulto MAS lenta que no usar cache
  en absoluto. Escribir en Redis cuesta. Ese costo se amortiza si el
  dato se lee muchas veces, y no se amortiza si se lee una.
""")


# =====================================================================
# Bloque 3. El problema que introduce la cache
# =====================================================================

def bloque_3_invalidacion(r, conexion):
    titulo("Bloque 3: cuando el dato guardado deja de ser cierto")

    id_tarjeta = 7
    clave = f"{PREFIJO}:tarjeta:{id_tarjeta}"
    r.delete(clave)

    perfil, origen = perfil_con_cache(r, conexion, id_tarjeta)
    print(f"\n  Perfil inicial ({origen}): "
          f"{perfil['operaciones']} operaciones, "
          f"gasto {perfil['gasto']:,.2f}")

    # Llega una operacion nueva. El dato de origen cambio.
    conexion.execute("""
        INSERT INTO pagos.transacciones
          (id_transaccion, fecha_hora, id_terminal, id_tarjeta, monto,
           moneda, estatus, metodo_captura)
        VALUES ('TRXCACHE1', NOW(), 1, %s, 9999.99, 'MXN', 'APROBADA', 'CHIP')
    """, (id_tarjeta,))

    real = calcular_perfil(conexion, id_tarjeta)
    perfil, origen = perfil_con_cache(r, conexion, id_tarjeta)

    print(f"\n  Tras insertar una operacion de 9,999.99:")
    print(f"    Valor real en PostgreSQL: {real['operaciones']} operaciones, "
          f"gasto {real['gasto']:,.2f}")
    print(f"    Valor que devuelve la cache ({origen}): "
          f"{perfil['operaciones']} operaciones, gasto {perfil['gasto']:,.2f}")

    print("""
  La cache devuelve un dato que ya no es cierto. Nada falla, nada
  advierte, y el sistema autoriza con informacion vieja.

  Es el costo que introduce la cache, y no tiene solucion perfecta. Hay
  tres formas de manejarlo.
""")

    print("""
  1. Expiracion por tiempo

     Se acepta que el dato este desactualizado durante un periodo
     acotado. Es lo que hace este codigo con ex=300.

     Ventaja: simple, y el sistema se recupera solo.
     Costo: hay una ventana en la que el dato es incorrecto.
     Cuando sirve: cuando un dato de cinco minutos es aceptable.

  2. Invalidacion explicita

     Quien escribe el dato de origen elimina la clave de la cache.
""")

    r.delete(clave)
    perfil, origen = perfil_con_cache(r, conexion, id_tarjeta)
    print(f"     Tras invalidar y volver a pedir ({origen}): "
          f"{perfil['operaciones']} operaciones, "
          f"gasto {perfil['gasto']:,.2f}")

    print("""
     Ventaja: el dato se corrige de inmediato.
     Costo: exige que TODO camino de escritura invalide. Un proceso que
       lo olvide deja la cache mintiendo de forma indefinida.
     Cuando sirve: cuando los caminos de escritura son pocos y
       controlados.

  3. Escritura simultanea

     Cada escritura actualiza el origen y la cache a la vez.

     Ventaja: la cache nunca esta desactualizada.
     Costo: encarece toda escritura, y las dos operaciones no son
       atomicas entre si. Si la segunda falla, queda peor que antes.
     Cuando sirve: cuando la lectura desactualizada no es tolerable.

  Criterio para este caso: expiracion por tiempo, con invalidacion
  explicita en los caminos que importan. El perfil de riesgo tolera
  algunos minutos de retraso; el bloqueo de una tarjeta, no.
""")

    conexion.rollback()
    r.delete(clave)


# =====================================================================
# Bloque 4. Lo que la cache no debe guardar
# =====================================================================

def bloque_4_que_no_guardar(r, conexion):
    titulo("Bloque 4: que se guarda y que no")

    print("""
  Se guarda en cache lo que se puede RECONSTRUIR.

    Si Redis se reinicia sin persistencia, todo se pierde. El sistema
    debe seguir funcionando, solo que mas lento.

  Se guarda
    perfiles y agregados derivados
    resultados de consultas costosas
    catalogos que cambian poco
    contadores y limites, que se pueden reiniciar sin consecuencia grave

  NO se guarda
    el registro de la transaccion
    el unico ejemplar de un dato
    informacion cuya perdida obligue a reprocesar

  En el caso de pagos: el perfil de riesgo si, la transaccion no.
""")

    # Se demuestra la reconstruccion.
    for i in range(1, 6):
        r.delete(f"{PREFIJO}:tarjeta:{i}")
    print("  Cache vaciada para cinco tarjetas.")

    inicio = time.perf_counter()
    for i in range(1, 6):
        perfil, origen = perfil_con_cache(r, conexion, i)
    print(f"  Reconstruidas en {(time.perf_counter() - inicio) * 1000:.0f} ms, "
          f"sin intervencion.")

    print("""
  Sobre la persistencia de Redis:

    Redis SI puede persistir en disco, con instantaneas periodicas o con
    bitacora de operaciones. Lo que no garantiza es durabilidad
    equivalente a la de un motor transaccional.

    La diferencia practica: en PostgreSQL, una operacion confirmada esta
    en disco. En Redis, con la configuracion habitual, pueden perderse
    las escrituras del ultimo segundo.

    Para una cache, esa perdida es irrelevante. Para un registro
    contable, es inaceptable. El criterio de uso se desprende de ahi.
""")


# =====================================================================
# Bloque 5. Medicion honesta
# =====================================================================

def bloque_5_medicion(r, conexion):
    titulo("Bloque 5: cuanto mejora en realidad")

    id_tarjeta = 20
    clave = f"{PREFIJO}:tarjeta:{id_tarjeta}"

    def medir(funcion, repeticiones=20):
        tiempos = []
        for _ in range(repeticiones):
            inicio = time.perf_counter()
            funcion()
            tiempos.append(time.perf_counter() - inicio)
        return min(tiempos) * 1000

    r.delete(clave)
    perfil_con_cache(r, conexion, id_tarjeta)

    desde_redis = medir(lambda: r.get(clave))
    desde_postgres = medir(lambda: calcular_perfil(conexion, id_tarjeta))

    print(f"\n  Leer de Redis:              {desde_redis:7.3f} ms")
    print(f"  Calcular en PostgreSQL:     {desde_postgres:7.3f} ms")
    print(f"  Relacion:                   {desde_postgres / desde_redis:7.0f} veces")

    print("""
  Metodo: minimo de veinte repeticiones, conforme al criterio de la
  sesion 2.5.

  EL RESULTADO INCOMODO, Y ES EL PUNTO DE LA SESION

  La diferencia es pequena. Con cinco mil transacciones, un indice
  sobre id_tarjeta y todo en cache de memoria, PostgreSQL resuelve esa
  agregacion en decenas de microsegundos.

  Con estos numeros, la cache NO esta justificada. Agrega un
  componente, introduce el problema de invalidacion del bloque 3, y
  ahorra una fraccion de milisegundo.

  Presentar este ejercicio como prueba de que Redis acelera seria
  deshonesto, y cualquier participante atento lo notaria.

  QUE CAMBIARIA LA CONCLUSION

    Volumen. Con veinte millones de transacciones, esa agregacion deja
    de resolverse en microsegundos. Es el escenario de la sesion 2.5.

    Concurrencia. Mil autorizaciones por segundo consultando el perfil
    ocupan conexiones de PostgreSQL, que son un recurso limitado y caro.
    Redis sostiene ordenes de magnitud mas conexiones concurrentes.

    Costo del calculo. Si el perfil exigiera ventanas, varias
    combinaciones o un modelo, el calculo pasaria de microsegundos a
    decenas de milisegundos.

    Origen remoto. Si el dato viniera de un servicio externo con
    latencia de red, la cache se justifica sola.

  LO QUE SI SE PUEDE AFIRMAR

    Leer un valor por clave desde memoria es mas rapido que calcular una
    agregacion. Era de esperarse.

    Redis no es mas rapido que PostgreSQL: no hacen lo mismo. Si se
    pidiera a Redis calcular ese agregado, no podria.

  El criterio no es de velocidad sino de reparto de trabajo. Redis
  guarda el resultado; PostgreSQL lo produce.

  Y el criterio previo, que suele omitirse: antes de agregar una cache,
  medir si hace falta. Una cache innecesaria es un componente mas que
  operar, y un problema de invalidacion que no se tenia.
""")

    r.delete(clave)


def main():
    r = conectar_redis()
    r.ping()

    with psycopg.connect(cadena_postgres()) as conexion:
        referencia = bloque_1_sin_cache(conexion)
        bloque_2_con_cache(r, conexion, referencia)
        bloque_3_invalidacion(r, conexion)
        bloque_4_que_no_guardar(r, conexion)
        bloque_5_medicion(r, conexion)
        conexion.rollback()

    for clave in r.scan_iter(match=f"{PREFIJO}:*", count=500):
        r.delete(clave)
    print("\nClaves de la demostracion eliminadas.")


if __name__ == "__main__":
    main()
