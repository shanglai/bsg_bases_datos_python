"""
c2_s2_b0_diagramas.py
Genera los diagramas de la sesion 2.2.

Produce tres figuras:
    c2_s2_d1_join_recorrido.png     desde PlantUML
    c2_s2_d2_orden_logico.png       desde PlantUML
    c2_s2_d3_motor_o_dataframe.png  desde mingrammer/diagrams

Requisitos:
    pip install diagrams
    Graphviz instalado en el sistema
    Java instalado y plantuml.jar en el directorio actual

Ejecucion: python c2_s2_b0_diagramas.py
"""

import subprocess
from pathlib import Path

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.database import Postgresql
from diagrams.programming.language import Python
from diagrams.generic.storage import Storage
from diagrams.programming.flowchart import Decision

PLANTUML_JAR = Path("plantuml.jar")
FUENTES_PUML = [
    "c2_s2_d1_join_recorrido.puml",
    "c2_s2_d2_orden_logico.puml",
]

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


def d3_motor_o_dataframe():
    """Las dos rutas para obtener un resultado agregado."""
    with Diagram(
        "Donde ocurre la agregacion",
        filename="c2_s2_d3_motor_o_dataframe",
        show=False,
        direction="LR",
        graph_attr=GRAPH_ATTR,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
    ):
        origen = Postgresql("pagos.transacciones\n5000 filas")

        with Cluster("Ruta A: agregar en el dataframe"):
            trae_todo = Python("read_sql\n3917 filas")
            agrega_pd = Python("groupby\n7 filas")
            trae_todo >> Edge(label="en memoria") >> agrega_pd

        with Cluster("Ruta B: agregar en el motor"):
            agrega_sql = Postgresql("GROUP BY\nen el servidor")
            trae_poco = Python("read_sql\n7 filas")
            agrega_sql >> Edge(label="solo el resultado") >> trae_poco

        criterio = Decision("Que tan grande\nes el resultado\nfrente al origen")
        destino = Storage("Analisis,\nmodelo o grafica")

        origen >> Edge(label="SELECT sin agrupar") >> trae_todo
        origen >> Edge(label="SELECT con GROUP BY") >> agrega_sql
        agrega_pd >> criterio
        trae_poco >> criterio
        criterio >> destino


if __name__ == "__main__":
    renderizar_plantuml()
    d3_motor_o_dataframe()
    print("Diagramas de la sesion 2.2 generados.")
