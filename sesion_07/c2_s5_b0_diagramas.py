"""
c2_s5_b0_diagramas.py
Genera los diagramas de la sesion 2.5.

Produce tres figuras:
    c2_s5_d1_plan.png                desde PlantUML
    c2_s5_d2_cuando_no_se_usa.png    desde PlantUML
    c2_s5_d3_transaccion.png         desde mingrammer/diagrams

Requisitos:
    pip install diagrams
    Graphviz instalado en el sistema
    Java instalado y plantuml.jar en el directorio actual

Ejecucion: python c2_s5_b0_diagramas.py
"""

import subprocess
from pathlib import Path

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.database import Postgresql
from diagrams.programming.language import Python
from diagrams.programming.flowchart import Decision, Action, StartEnd

PLANTUML_JAR = Path("plantuml.jar")
FUENTES_PUML = ["c2_s5_d1_plan.puml", "c2_s5_d2_cuando_no_se_usa.puml"]

GRAPH_ATTR = {"fontsize": "18", "bgcolor": "transparent", "pad": "0.4",
              "splines": "ortho"}
NODE_ATTR = {"fontsize": "13"}
EDGE_ATTR = {"fontsize": "12", "color": "#56646f"}


def renderizar_plantuml():
    if not PLANTUML_JAR.exists():
        print("Aviso: no se encontro plantuml.jar. Se omiten esas figuras.")
        return
    for fuente in FUENTES_PUML:
        if Path(fuente).exists():
            subprocess.run(["java", "-jar", str(PLANTUML_JAR), "-tpng", fuente],
                           check=True)
            print(f"Generado desde PlantUML: {fuente}")


def d3_transaccion():
    """El recorrido de una transaccion y sus dos salidas."""
    with Diagram(
        "Una transaccion y sus dos salidas",
        filename="c2_s5_d3_transaccion",
        show=False,
        direction="LR",
        graph_attr=GRAPH_ATTR,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
    ):
        inicio = StartEnd("with psycopg.connect()")

        with Cluster("Transaccion abierta"):
            op1 = Action("UPDATE saldos\ncuenta 1: -300")
            op2 = Action("UPDATE saldos\ncuenta 2: +300")
            op1 >> op2

        verificacion = Decision("Hubo excepcion")

        with Cluster("Salida A"):
            commit = Postgresql("COMMIT\nlos dos cambios\nquedan")

        with Cluster("Salida B"):
            rollback = Postgresql("ROLLBACK\nninguno queda")

        inicio >> op1
        op2 >> verificacion
        verificacion >> Edge(label="no") >> commit
        verificacion >> Edge(label="si") >> rollback


if __name__ == "__main__":
    renderizar_plantuml()
    d3_transaccion()
    print("Diagramas de la sesion 2.5 generados.")
