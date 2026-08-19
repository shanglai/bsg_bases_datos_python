
"""
Taller de la Sesión 01.
"""

import sqlite3
from pathlib import Path

# **B1.** Escribir una funcion `operaciones_por_ciudad(ciudad)` que reciba el nombre
# de una ciudad y devuelva la cantidad de operaciones aprobadas. La ciudad debe
# pasarse como **parametro** de la consulta, no concatenarse en la cadena.

def operaciones_por_ciudad(ciudad):
    print('Calculando operaciones para la ciudad ' + ciudad)
    conn= sqlite3.connect(Path('pagos.db'))
    cursor= conn.cursor()
    #cursor.execute("SELECT ciudad_comercio, count(1) as operaciones from movimientos where estatus='APROBADA' AND ciudad_comercio = ? group by ciudad_comercio", [ciudad] )

    #Opcion 2
    cursor.execute("SELECT ?, count(1) as operaciones from movimientos where estatus='APROBADA' AND ciudad_comercio = ?", (ciudad,ciudad))
    print(cursor.fetchone())

    #Opcion 1
    #resultado= cursor.fetchone() #[1]
    #if resultado == None:
    #    print('Ninguna Operacion')
    #else:
    #    print('Las operaciones en {} son: {}.'.format(ciudad,resultado[1]))


    #print('Las operaciones en ' + ciudad + ' son: ' + str(resultado))
    #print('Las operaciones en {} son: {}.'.format(ciudad,resultado))


operaciones_por_ciudad('Cancun')
operaciones_por_ciudad('Queretaro')



