"""
c3_s2_b0_diagramas.py
Genera los diagramas de la sesion 3.2.

Produce tres figuras:
    c3_s2_d1_tuberia.png       desde PlantUML
    c3_s2_d2_unwind.png        desde PlantUML
    c3_s2_d3_donde_calcular.png  desde mingrammer/diagrams

Requisitos:
    pip install diagrams
    Graphviz instalado en el sistema
    Java instalado y plantuml.jar en el directorio actual

Ejecucion: python c3_s2_b0_diagramas.py
"""

import subprocess
from pathlib import Path

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.database import Mongodb
from diagrams.programming.language import Python
from diagrams.programming.flowchart import Decision
from diagrams.generic.storage import Storage

PLANTUML_JAR = Path("plantuml.jar")
FUENTES_PUML = ["c3_s2_d1_tuberia.puml", "c3_s2_d2_unwind.puml"]

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


def d3_donde_calcular():
    """Tres formas de llevar el documento al dataframe."""
    with Diagram(
        "Del documento al dataframe",
        filename="c3_s2_d3_donde_calcular",
        show=False,
        direction="LR",
        graph_attr=GRAPH_ATTR,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
    ):
        origen = Mongodb("operaciones\n5000 documentos\nanidados")

        with Cluster("A: traer y aplanar en el cliente"):
            a1 = Python("find()")
            a2 = Python("json_normalize\n44 columnas\n13 casi vacias")
            a1 >> a2

        with Cluster("B: aplanar en el servidor"):
            b1 = Mongodb("$project")
            b2 = Python("10 columnas\nya planas")
            b1 >> b2

        with Cluster("C: agregar en el servidor"):
            c1 = Mongodb("$group")
            c2 = Python("30 filas")
            c1 >> c2

        criterio = Decision("Cuanto se reduce\nfrente al origen")
        destino = Storage("Analisis,\nmodelo o grafica")

        origen >> Edge(label="todo") >> a1
        origen >> Edge(label="campos elegidos") >> b1
        origen >> Edge(label="solo el resultado") >> c1
        a2 >> criterio
        b2 >> criterio
        c2 >> criterio
        criterio >> destino


if __name__ == "__main__":
    renderizar_plantuml()
    d3_donde_calcular()
    print("Diagramas de la sesion 3.2 generados.")
