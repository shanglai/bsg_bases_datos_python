"""
c4_s1_b8_solucionario.py
Solucionario del taller de la sesion 4.1.

Documento para el instructor. NO se entrega al participante.

Requisitos: Redis activo, PostgreSQL con el caso, .env
Ejecucion:  python c4_s1_b8_solucionario.py
"""

import json
import os
import random
import time

import psycopg
import redis
from dotenv import load_dotenv

load_dotenv(override=True)
random.seed(987654)
PREFIJO = "taller"


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
    print("\n" + "=" * 72 + f"\n{texto}\n" + "=" * 72)


def punto(clave, enunciado):
    print("\n" + "-" * 72 + f"\n{clave}. {enunciado}\n" + "-" * 72)


def limpiar(r):
    for clave in r.scan_iter(match=f"{PREFIJO}:*", count=500):
        r.delete(clave)


# =====================================================================

def parte_a(r):
    titulo("PARTE A. ESTRUCTURAS")

    punto("A1 a A4", "Las cuatro estructuras")

    contador = f"{PREFIJO}:intentos:42"
    r.delete(contador)
    for _ in range(5):
        valor = r.incr(contador)
    print(f"\n  A1 contador: {valor}")

    perfil = f"{PREFIJO}:perfil:42"
    r.delete(perfil)
    r.hset(perfil, mapping={"puntaje": 37, "operaciones": 128,
                            "marca": "VISA", "ciudad": "Merida"})
    print(f"  A2 un solo campo: {r.hget(perfil, 'marca')}")

    bloqueadas = f"{PREFIJO}:bloqueadas"
    r.delete(bloqueadas)
    r.sadd(bloqueadas, "4417", "8823", "1102")
    print(f"  A3 '4417' bloqueada: {bool(r.sismember(bloqueadas, '4417'))}, "
          f"'9999': {bool(r.sismember(bloqueadas, '9999'))}")

    ranking = f"{PREFIJO}:ranking"
    r.delete(ranking)
    r.zadd(ranking, {"Viajes Altamar": 2938402.49, "Electro Maya": 2378339.96,
                     "Super Norteno": 2217958.06, "Boutique Iris": 1542762.30,
                     "Farmacia Del Sol": 425508.98,
                     "Gasolinera Km 12": 404545.25, "Cafe Aurora": 198082.83})
    print(f"  A4 tres primeros: "
          f"{[n for n, _ in r.zrevrange(ranking, 0, 2, withscores=True)]}")
    print(f"     posicion de Electro Maya: "
          f"{r.zrevrank(ranking, 'Electro Maya') + 1}")

    punto("A5", "Por que conjunto y no conjunto ordenado")
    print("""
  El conjunto de bloqueadas responde una sola pregunta: esta o no esta.
  No hay orden ni puntaje que aporte nada. SISMEMBER es inmediato.

  El ranking necesita orden por importe, y ese orden es el resultado
  buscado. El conjunto ordenado lo mantiene de forma permanente.

  Que se perderia al intercambiarlos:

    Ranking como conjunto: se perderia el orden. Obtener los tres
    primeros exigiria traer todos los elementos y ordenarlos en Python,
    que es justamente lo que la estructura evita.

    Bloqueadas como conjunto ordenado: funcionaria, y obligaria a
    inventar un puntaje que no significa nada. Ocupa mas y no aporta.

  El criterio: la estructura se elige por la operacion habitual, no por
  el dato.
""")

    punto("A6", "Tipos")
    for clave in [contador, perfil, bloqueadas, ranking]:
        print(f"    {r.type(clave):<8} {clave}")


def parte_b(r):
    titulo("PARTE B. EXPIRACION Y ATOMICIDAD")

    punto("B1", "Expiracion")
    clave = f"{PREFIJO}:temporal"
    r.set(clave, "x", ex=3)
    print(f"\n    TTL inmediato: {r.ttl(clave)} s")
    time.sleep(3.2)
    print(f"    Tras esperar:  {r.get(clave)}")

    punto("B2 y B3", "Limitador de intentos")
    print("""
    def intentos_recientes(r, id_tarjeta, ventana=60):
        clave = f"limite:tarjeta:{id_tarjeta}"
        valor = r.incr(clave)
        if valor == 1:                    # primera vez en la ventana
            r.expire(clave, ventana)
        return valor

  Por que es correcto con dos procesos simultaneos:

    INCR es atomico. Dos procesos que lo llamen a la vez obtienen
    valores distintos, y solo UNO recibe 1. Ese es el unico que fija la
    expiracion.

    Sin la atomicidad de INCR, dos procesos podrian leer 0, calcular 1 y
    escribir 1, perdiendo un intento.

  Detalle honesto que conviene reconocer: hay una ventana minima entre
  el INCR y el EXPIRE. Si el proceso muere justo ahi, la clave queda sin
  expiracion y el limite nunca se libera.

  La forma robusta usa un script de Lua, que Redis ejecuta de forma
  atomica completa. Se menciona y no se desarrolla en esta sesion.
""")

    def intentos_recientes(id_tarjeta, ventana=60):
        clave = f"{PREFIJO}:limite:{id_tarjeta}"
        valor = r.incr(clave)
        if valor == 1:
            r.expire(clave, ventana)
        return valor

    r.delete(f"{PREFIJO}:limite:99")
    print("\n    Seis llamadas seguidas:")
    for i in range(6):
        n = intentos_recientes(99)
        print(f"      intento {i + 1}: contador {n}, "
              f"{'RECHAZADO' if n > 5 else 'permitido'}")
    print(f"    TTL de la clave: {r.ttl(f'{PREFIJO}:limite:99')} s")

    punto("B4 y B5", "Cerrojo elemental y lo que le falta")
    cerrojo = f"{PREFIJO}:cerrojo"
    r.delete(cerrojo)
    print(f"\n    Primer intento:  {r.set(cerrojo, 'A', nx=True, ex=10)}")
    print(f"    Segundo intento: {r.set(cerrojo, 'B', nx=True, ex=10)}")
    print("""
  Dos cosas que le faltan, de las siguientes. Cualquier par sirve:

    El valor debe identificar al dueno, y la liberacion debe verificarlo.
    Tal como esta, cualquier proceso puede borrar el cerrojo de otro.

    La expiracion debe cubrir el peor tiempo de ejecucion. Si el proceso
    tarda mas, el cerrojo expira y otro entra mientras el primero sigue
    trabajando.

    La liberacion debe ser atomica: comprobar el dueno y borrar en una
    sola operacion, lo que exige un script de Lua.

    Con varios nodos de Redis, el problema es considerablemente mas
    dificil y hay debate abierto sobre si se resuelve bien.

  Lo que se evalua es que reconozca que un cerrojo distribuido correcto
  es un problema serio, no dos lineas de codigo.
""")


def parte_c(r, conexion):
    titulo("PARTE C. LA CACHE")

    def calcular(id_tarjeta):
        fila = conexion.execute("""
            SELECT COUNT(*), COALESCE(SUM(monto), 0)
            FROM pagos.transacciones WHERE id_tarjeta = %s
        """, (id_tarjeta,)).fetchone()
        return {"id_tarjeta": id_tarjeta, "operaciones": fila[0],
                "gasto": float(fila[1])}

    def perfil(id_tarjeta, vigencia=300):
        clave = f"{PREFIJO}:perfil_c:{id_tarjeta}"
        guardado = r.get(clave)
        if guardado is not None:
            return json.loads(guardado), "cache"
        valor = calcular(id_tarjeta)
        r.set(clave, json.dumps(valor), ex=vigencia)
        return valor, "calculado"

    punto("C1 y C2", "Cache-aside y medicion")
    tarjetas = list(range(1, 101))
    for t in tarjetas:
        r.delete(f"{PREFIJO}:perfil_c:{t}")

    inicio = time.perf_counter()
    for t in tarjetas:
        perfil(t)
    vacia = time.perf_counter() - inicio

    inicio = time.perf_counter()
    for t in tarjetas:
        perfil(t)
    llena = time.perf_counter() - inicio

    print(f"\n    Cache vacia: {vacia * 1000:7.1f} ms")
    print(f"    Cache llena: {llena * 1000:7.1f} ms")
    print(f"    Relacion:    {vacia / llena:7.1f} veces")

    punto("C3 y C4", "El dato que deja de ser cierto")
    id_tarjeta = 7
    clave = f"{PREFIJO}:perfil_c:{id_tarjeta}"
    r.delete(clave)
    antes, _ = perfil(id_tarjeta)
    print(f"\n    Antes: {antes['operaciones']} operaciones, "
          f"gasto {antes['gasto']:,.2f}")

    conexion.execute("""
        INSERT INTO pagos.transacciones
          (id_transaccion, fecha_hora, id_terminal, id_tarjeta, monto,
           moneda, estatus, metodo_captura)
        VALUES ('TRXTALLER', NOW(), 1, %s, 5000.00, 'MXN', 'APROBADA', 'CHIP')
    """, (id_tarjeta,))

    desactualizado, origen = perfil(id_tarjeta)
    real = calcular(id_tarjeta)
    print(f"    Real:  {real['operaciones']} operaciones, "
          f"gasto {real['gasto']:,.2f}")
    print(f"    Cache ({origen}): {desactualizado['operaciones']} operaciones, "
          f"gasto {desactualizado['gasto']:,.2f}")

    r.delete(clave)
    corregido, origen = perfil(id_tarjeta)
    print(f"    Tras invalidar ({origen}): {corregido['operaciones']} "
          f"operaciones, gasto {corregido['gasto']:,.2f}")

    punto("C5 y C6", "Medicion, y si la cache esta justificada")

    def medir(funcion, repeticiones=20):
        tiempos = []
        for _ in range(repeticiones):
            inicio = time.perf_counter()
            funcion()
            tiempos.append(time.perf_counter() - inicio)
        return min(tiempos) * 1000

    r.delete(clave)
    perfil(id_tarjeta)
    desde_redis = medir(lambda: r.get(clave))
    desde_pg = medir(lambda: calcular(id_tarjeta))
    print(f"\n    Redis:      {desde_redis:7.3f} ms")
    print(f"    PostgreSQL: {desde_pg:7.3f} ms")
    print(f"    Relacion:   {desde_pg / desde_redis:7.1f} veces")

    print("""
  C6 es el punto de mayor valor del taller.

  Respuesta esperada: con ESTE volumen, la cache NO esta justificada por
  la medicion. La diferencia es de fracciones de milisegundo, y a cambio
  se agrega un componente y el problema de invalidacion de C3.

  Lo que se evalua es que el participante llegue a esa conclusion
  incomoda a partir de sus propios numeros, en lugar de repetir que la
  cache acelera.

  Respuesta completa: ademas identifica que cambiaria la conclusion.

    Volumen. Con veinte millones de transacciones, la agregacion deja
    de resolverse en microsegundos.
    Concurrencia. Mil autorizaciones por segundo ocupan conexiones de
    PostgreSQL, que son un recurso limitado.
    Costo del calculo. Un perfil con ventanas o con un modelo cuesta
    ordenes de magnitud mas.
    Origen remoto. Con latencia de red, la cache se justifica sola.

  Respuesta que obtiene calificacion parcial: concluir que si esta
  justificada citando razones generales sin haber mirado la medicion.

  Respuesta que tambien es valida: concluir que si esta justificada POR
  la concurrencia, si lo sustenta. El punto no es la conclusion sino el
  razonamiento.
""")

    conexion.rollback()


def parte_d(r, conexion):
    titulo("PARTE D. APLICADO AL CASO")

    punto("D1 a D4", "Las tres verificaciones y la funcion de autorizacion")

    r.delete(f"{PREFIJO}:ranking_dia")
    r.delete(f"{PREFIJO}:bloqueadas_d")
    r.sadd(f"{PREFIJO}:bloqueadas_d", "4417", "8823")

    def limite_excedido(id_tarjeta, maximo=5, ventana=60):
        clave = f"{PREFIJO}:lim:{id_tarjeta}"
        valor = r.incr(clave)
        if valor == 1:
            r.expire(clave, ventana)
        return valor > maximo

    def tarjeta_bloqueada(ultimos4):
        return bool(r.sismember(f"{PREFIJO}:bloqueadas_d", ultimos4))

    def registrar_volumen(comercio, monto):
        r.zincrby(f"{PREFIJO}:ranking_dia", monto, comercio)

    def autorizar(id_tarjeta, ultimos4, comercio, monto):
        if tarjeta_bloqueada(ultimos4):
            return False, "tarjeta bloqueada"
        if limite_excedido(id_tarjeta):
            return False, "demasiados intentos"
        registrar_volumen(comercio, monto)
        return True, "autorizada"

    print("\n    Tarjeta bloqueada:")
    print(f"      {autorizar(1, '4417', 'Cafe Aurora', 100)}")

    print("\n    Seis intentos de la misma tarjeta:")
    r.delete(f"{PREFIJO}:lim:55")
    for i in range(6):
        print(f"      {i + 1}: {autorizar(55, '9999', 'Cafe Aurora', 100)}")

    print("\n    Cien operaciones simuladas, ranking del dia:")
    comercios = ["Super Norteno", "Cafe Aurora", "Electro Maya",
                 "Viajes Altamar"]
    for i in range(100):
        registrar_volumen(random.choice(comercios),
                          round(random.uniform(100, 5000), 2))
    for nombre, puntaje in r.zrevrange(f"{PREFIJO}:ranking_dia", 0, -1,
                                       withscores=True):
        print(f"      {nombre:<20} {puntaje:>12,.2f}")

    punto("D5", "Cuantas veces por segundo")
    print("""
  Estimacion esperada: en un procesador de pagos de tamano medio, del
  orden de cientos a miles de autorizaciones por segundo en hora pico.

  Si cada una hiciera tres consultas a PostgreSQL, serian miles de
  consultas por segundo solo en verificaciones previas, sin contar el
  registro de la transaccion.

  El problema no es el tiempo de cada consulta, que es de microsegundos
  como se midio en C5. El problema es la CONCURRENCIA: cada consulta
  ocupa una conexion, y las conexiones de PostgreSQL son un recurso
  limitado y caro.

  Ese es el argumento que si justifica Redis en este caso, y no la
  velocidad de una consulta aislada.

  Es la conexion que conviene que el participante haga entre C6 y D5.
""")


def parte_e():
    titulo("PARTE E. ANALISIS Y ARGUMENTACION")

    punto("E1", "Que si y que no guardar en Redis")
    print("""
  SI, porque se puede reconstruir:
    perfil de riesgo de la tarjeta, derivado de las transacciones
    ranking de comercios del dia, recalculable
    contador de intentos, cuya perdida solo relaja el limite un momento
    catalogo de comercios, que vive en PostgreSQL

  NO, porque es el unico ejemplar:
    el registro de la transaccion
    el contracargo
    el mensaje de autorizacion original
    cualquier dato con obligacion de conservacion

  Criterio a exigir: si Redis se reinicia sin persistencia y el dato se
  pierde, el sistema debe seguir funcionando, solo que mas lento. Si la
  perdida obliga a reprocesar o deja un hueco contable, no va en Redis.
""")

    punto("E2", "Dos estrategias distintas para dos datos")
    print("""
  Perfil de riesgo: expiracion por tiempo.
    Tolera estar desactualizado algunos minutos. La expiracion es simple
    y el sistema se recupera solo.

  Bloqueo de tarjeta: invalidacion explicita, o escritura simultanea.
    NO tolera retraso. Una tarjeta bloqueada que siga autorizando
    durante cinco minutos es una perdida directa.

  El criterio que los separa: cuanto cuesta que el dato este
  desactualizado durante la ventana.

  Respuesta completa: reconoce que la invalidacion explicita exige que
  TODO camino de escritura la haga, y que por eso conviene concentrar la
  escritura del bloqueo en un solo lugar.
""")

    punto("E3", "Persistencia no es durabilidad")
    print("""
  Redis si persiste, con instantaneas periodicas o bitacora de
  operaciones. Lo que no ofrece es la garantia de un motor
  transaccional.

  La diferencia practica: en PostgreSQL, una operacion confirmada esta
  en disco antes de que el cliente reciba la confirmacion. En Redis,
  con la configuracion habitual de bitacora, pueden perderse las
  escrituras del ultimo segundo.

  Para una cache eso es irrelevante. Para un registro contable es
  inaceptable, y ademas faltarian las transacciones entre claves, las
  restricciones y la consulta.

  Respuesta que NO obtiene el punto: decir que Redis no persiste. Si
  persiste, y el matiz es el que importa.
""")

    punto("E4", "Mover la tabla de comercios a Redis")
    print("""
  Evaluacion esperada: es una propuesta razonable a medias, y conviene
  examinarla en lugar de descartarla.

  A favor:
    son siete filas, caben de sobra
    se consultan en casi toda operacion
    cambian muy poco, de modo que la invalidacion es barata

  En contra:
    la medicion de C5 mostro que leerlas de PostgreSQL ya cuesta
      microsegundos, porque caben en su cache de memoria
    agregar el componente introduce el problema de invalidacion
    el catalogo es el ORIGEN del dato en el modelo relacional, y el
      enunciado dice "mover", no "copiar"

  La distincion clave: COPIAR el catalogo a Redis como cache es
  defendible. MOVERLO es un error, porque perderia la llave foranea que
  garantiza que ninguna terminal apunte a un comercio inexistente.

  Se valora que el participante note esa diferencia entre copiar y
  mover. Es el punto del ejercicio.
""")

    punto("E5", "Ficha de seis puntos de Redis")
    print("""
  1. Modelo de datos que asume
     Clave y valor, con el valor tipado como cadena, diccionario, lista,
     conjunto o conjunto ordenado. Todo en memoria. Sin esquema ni
     relaciones.

  2. Operaciones en las que resulta eficiente
     Acceso por clave. Incremento atomico. Pertenencia a un conjunto.
     Rango sobre un conjunto ordenado. Todas en microsegundos.
     Ineficiente, o imposible: consultar por contenido, combinar,
     agregar sobre muchos registros.

  3. Garantias de consistencia
     Cada comando es atomico. Hay transacciones con MULTI y EXEC, y
     scripts de Lua para atomicidad compuesta. La durabilidad es
     configurable y menor que la de un motor transaccional.

  4. Costo de escritura frente a costo de lectura
     Ambos muy bajos. El costo real es la MEMORIA, que es cara, y la
     invalidacion, que es un problema de diseno y no de rendimiento.

  5. Interfaz desde Python
     redis-py. Los valores llegan como cadenas, o como bytes sin
     decode_responses. La conversion de tipos la hace el codigo.

  6. Cuando conviene y cuando no
     Conviene para datos derivados que se leen mucho, se reconstruyen
     solos y toleran perdida: cache, contadores, rankings, colas.
     No conviene como unico ejemplar de un dato, ni cuando se necesita
     consultar por contenido, ni cuando la memoria no alcanza.
""")


def criterios():
    titulo("CRITERIOS DE CALIFICACION")
    print("""
  Parte A, 20 por ciento
    A5 se evalua por la justificacion, no por el codigo.

  Parte B, 20 por ciento
    B3 exige entender que INCR es atomico y que solo un proceso recibe 1.
    En B5 se valora reconocer que un cerrojo correcto es un problema
    serio.

  Parte C, 25 por ciento
    C6 es el punto de mayor valor del taller. Se evalua que llegue a una
    conclusion a partir de SU medicion, no de una consigna.
    Ambas conclusiones son aceptables si estan sustentadas.

  Parte D, 15 por ciento
    D5 debe conectar con C6: el argumento que justifica Redis aqui es la
    concurrencia, no la velocidad de una consulta aislada.

  Parte E, 20 por ciento
    E4 es el mas fino: distinguir entre copiar y mover el catalogo.
    En E3, decir que Redis no persiste no obtiene el punto.

  Error transversal a vigilar
    Presentar Redis como una base de datos mas rapida. No es mas rapida:
    hace menos cosas, y por eso responde antes.
""")


def main():
    r = conectar_redis()
    r.ping()
    limpiar(r)

    with psycopg.connect(cadena_postgres()) as conexion:
        parte_a(r)
        parte_b(r)
        parte_c(r, conexion)
        parte_d(r, conexion)
        conexion.rollback()

    parte_e()
    criterios()
    limpiar(r)
    print("\nClaves del taller eliminadas.")


if __name__ == "__main__":
    main()
