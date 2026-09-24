"""
c4_final_b2_genera_acls.py
Genera un usuario de Redis por alumno, aislado en su propio prefijo.

Lo ejecuta el INSTRUCTOR antes de la clase.

QUE RESUELVE

  Veinte personas sobre el mismo Redis se pisan: uno hace FLUSHALL y
  borra el trabajo de todos, otro escribe sobre la clave del vecino.

  Las ACL de Redis 6 en adelante resuelven eso: cada usuario queda
  restringido a las claves que empiecen con su prefijo, y sin permiso
  para los comandos destructivos.

  Comprobado:
    alumno01 escribe en alumno01:*        OK
    alumno01 escribe en alumno02:*        NOPERM
    alumno01 ejecuta FLUSHALL             NOPERM
    alumno02 lee una clave de alumno01    NOPERM

  De paso, el aislamiento por prefijo es contenido de la sesion: es como
  se hace multi-tenencia en un almacen clave-valor que no tiene esquemas
  ni bases separadas por permiso.

Produce dos archivos:
    acl_alumnos.conf            se anexa al archivo de ACL del servidor
    credenciales_alumnos.csv    una fila por alumno, para repartir

Ejecucion: python c4_final_b2_genera_acls.py [numero_de_alumnos]
"""

import csv
import secrets
import sys

ALUMNOS = int(sys.argv[1]) if len(sys.argv) > 1 else 20
SALIDA_ACL = "acl_alumnos.conf"
SALIDA_CSV = "credenciales_alumnos.csv"

# Categorias de comandos que el alumno necesita para el taller.
#   +@read      lectura
#   +@write     escritura
#   +@keyspace  TTL, EXPIRE, TYPE, SCAN
#   +@string +@hash +@list +@set +@sortedset   las cinco estructuras
#   +@connection  PING, ECHO
#   +@transaction MULTI, EXEC
#
# Se niegan de forma explicita los comandos que afectan a todos.
PERMISOS = [
    "+@read", "+@write", "+@keyspace", "+@connection", "+@transaction",
    "+@string", "+@hash", "+@list", "+@set", "+@sortedset",
    "+info", "+dbsize",
    "-flushall", "-flushdb", "-config", "-shutdown", "-debug",
    "-replicaof", "-slaveof", "-acl", "-keys",
]


def main():
    filas = []
    lineas_acl = []

    for numero in range(1, ALUMNOS + 1):
        usuario = f"alumno{numero:02d}"
        # token_urlsafe evita caracteres que rompan la URI de conexion.
        clave = secrets.token_urlsafe(12)

        # ~prefijo:*  restringe las claves a ese patron.
        # resetchannels quita el acceso a los canales de publicacion.
        lineas_acl.append(
            f"user {usuario} on >{clave} ~{usuario}:* resetchannels "
            + " ".join(PERMISOS)
        )
        filas.append({"usuario": usuario, "clave": clave,
                      "prefijo": f"{usuario}:"})

    with open(SALIDA_ACL, "w", encoding="utf-8") as archivo:
        archivo.write("\n".join(lineas_acl) + "\n")

    with open(SALIDA_CSV, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(
            archivo, fieldnames=["usuario", "clave", "prefijo"])
        escritor.writeheader()
        escritor.writerows(filas)

    print(f"Generados {ALUMNOS} usuarios.")
    print(f"  {SALIDA_ACL}    se anexa al archivo de ACL del servidor")
    print(f"  {SALIDA_CSV}    una fila por alumno, para repartir")
    print(f"\nEjemplo de la primera linea de ACL:")
    print(f"  {lineas_acl[0][:100]}...")
    print("""
IMPORTANTE
  credenciales_alumnos.csv contiene contrasenas en claro. No subirlo a
  un repositorio ni compartirlo completo: se reparte una fila a cada
  persona y despues se borra el archivo.
""")


if __name__ == "__main__":
    main()
