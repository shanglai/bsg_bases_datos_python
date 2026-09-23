"""
c3_s1_b0_diagramas.py
Genera los diagramas de la sesion 3.1.

Produce tres figuras:
    c3_s1_d1_relacional_vs_documento.png  desde PlantUML
    c3_s1_d2_esquema_flexible.png         desde PlantUML
    c3_s1_d3_entorno.png                  desde mingrammer/diagrams

Requisitos:
    pip install diagrams
    Graphviz instalado en el sistema
    Java instalado y plantuml.jar en el directorio actual

Ejecucion: python c3_s1_b0_diagramas.py
"""

import subprocess
from pathlib import Path

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.database import Mongodb, Postgresql
from diagrams.programming.language import Python
from diagrams.onprem.client import Client
from diagrams.generic.storage import Storage

PLANTUML_JAR = Path("plantuml.jar")
FUENTES_PUML = [
    "c3_s1_d1_relacional_vs_documento.puml",
    "c3_s1_d2_esquema_flexible.puml",
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


def d3_entorno():
    """Los dos motores conviven durante todo el capitulo 3."""
    with Diagram(
        "El entorno del capitulo 3",
        filename="c3_s1_d3_entorno",
        show=False,
        direction="LR",
        graph_attr=GRAPH_ATTR,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
    ):
        with Cluster("Equipo del participante"):
            carga = Python("c3_s1_b3_carga.py")
            entorno = Storage(".env\ncredenciales\nde ambos motores")
            dbeaver = Client("DBeaver")

        with Cluster("Motor de contenedores"):
            with Cluster("curso_postgres"):
                pg = Postgresql("PostgreSQL\npuerto 5432")
            with Cluster("curso_mongo"):
                mongo = Mongodb("MongoDB\npuerto 27017")

        entorno >> Edge(style="dashed", label="lee") >> carga
        pg >> Edge(label="1. lee y recompone") >> carga
        carga >> Edge(label="2. escribe documentos") >> mongo
        dbeaver >> Edge(style="dashed", label="consulta") >> pg

if __name__ == "__main__":
    renderizar_plantuml()
    d3_entorno()
    print("Diagramas de la sesion 3.1 generados.")
