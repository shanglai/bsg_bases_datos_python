"""
c3_s3_b0_diagramas.py
Genera los diagramas de la sesion 3.3.

Produce tres figuras:
    c3_s3_d1_donde_vive.png     desde PlantUML
    c3_s3_d2_preguntas.png      desde PlantUML
    c3_s3_d3_recorrido.png      desde mingrammer/diagrams

Requisitos:
    pip install diagrams
    Graphviz instalado en el sistema
    Java instalado y plantuml.jar en el directorio actual

Ejecucion: python c3_s3_b0_diagramas.py
"""

import subprocess
from pathlib import Path

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.database import Mongodb, Postgresql
from diagrams.generic.storage import Storage
from diagrams.programming.language import Python

PLANTUML_JAR = Path("plantuml.jar")
FUENTES_PUML = ["c3_s3_d1_donde_vive.puml", "c3_s3_d2_preguntas.puml"]

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


def d3_recorrido():
    """El mismo dato, por los dos caminos del curso."""
    with Diagram(
        "El mismo dato, dos caminos",
        filename="c3_s3_d3_recorrido",
        show=False,
        direction="LR",
        graph_attr=GRAPH_ATTR,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
    ):
        origen = Storage("pagos_plano.csv\n1 tabla sucia\nsesion 1.1")

        with Cluster("Capitulo 1 y 2: el camino relacional"):
            modelo = Storage("6 entidades\nnormalizadas\nsesion 1.2")
            pg = Postgresql("PostgreSQL\nesquema estricto\nJSONB acotado")
            modelo >> pg

        with Cluster("Capitulo 3: el camino documental"):
            mg = Mongodb("MongoDB\n1 coleccion\ndenormalizada")

        matriz = Python("Matriz de decision\nsesion 3.3")

        origen >> Edge(label="normalizar") >> modelo
        pg >> Edge(label="denormalizar\nsesion 3.1") >> mg
        pg >> matriz
        mg >> matriz


if __name__ == "__main__":
    renderizar_plantuml()
    d3_recorrido()
    print("Diagramas de la sesion 3.3 generados.")
