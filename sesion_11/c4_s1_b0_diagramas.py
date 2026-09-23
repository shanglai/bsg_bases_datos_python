"""
c4_s1_b0_diagramas.py
Genera los diagramas de la sesion 4.1.

Produce tres figuras:
    c4_s1_d1_proposito.png      desde PlantUML
    c4_s1_d2_invalidacion.png   desde PlantUML
    c4_s1_d3_cache_aside.png    desde mingrammer/diagrams

Requisitos:
    pip install diagrams
    Graphviz instalado en el sistema
    Java instalado y plantuml.jar en el directorio actual

Ejecucion: python c4_s1_b0_diagramas.py
"""

import subprocess
from pathlib import Path

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.database import Postgresql
from diagrams.onprem.inmemory import Redis
from diagrams.programming.language import Python
from diagrams.programming.flowchart import Decision

PLANTUML_JAR = Path("plantuml.jar")
FUENTES_PUML = ["c4_s1_d1_proposito.puml", "c4_s1_d2_invalidacion.puml"]

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


def d3_cache_aside():
    """El patron cache-aside, que es el que usa el material."""
    with Diagram(
        "El patron cache-aside",
        filename="c4_s1_d3_cache_aside",
        show=False,
        direction="LR",
        graph_attr=GRAPH_ATTR,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
    ):
        aplicacion = Python("Motor de\nautorizacion")
        pregunta = Decision("Esta la clave\nen Redis")

        with Cluster("Si esta: acierto"):
            acierto = Redis("GET\nmicrosegundos")

        with Cluster("Si no esta: fallo"):
            fallo = Postgresql("Calcular\nla agregacion")
            guardar = Redis("SET con\nexpiracion")
            fallo >> guardar

        aplicacion >> pregunta
        pregunta >> Edge(label="si") >> acierto
        pregunta >> Edge(label="no") >> fallo
        acierto >> Edge(label="perfil") >> aplicacion
        guardar >> Edge(label="perfil") >> aplicacion


if __name__ == "__main__":
    renderizar_plantuml()
    d3_cache_aside()
    print("Diagramas de la sesion 4.1 generados.")
