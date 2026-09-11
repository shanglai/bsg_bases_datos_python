"""
c2_s4_b0_diagramas.py
Genera los diagramas de la sesion 2.4.

Produce tres figuras:
    c2_s4_d1_columnas_vs_documento.png  desde PlantUML
    c2_s4_d2_operadores.png             desde PlantUML
    c2_s4_d3_indices.png                desde mingrammer/diagrams

Requisitos:
    pip install diagrams
    Graphviz instalado en el sistema
    Java instalado y plantuml.jar en el directorio actual

Ejecucion: python c2_s4_b0_diagramas.py
"""

import subprocess
from pathlib import Path

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.database import Postgresql
from diagrams.programming.flowchart import Decision, Document
from diagrams.generic.storage import Storage

PLANTUML_JAR = Path("plantuml.jar")
FUENTES_PUML = [
    "c2_s4_d1_columnas_vs_documento.puml",
    "c2_s4_d2_operadores.puml",
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


def d3_indices():
    """Tres formas de indexar un documento, y cuando sirve cada una."""
    with Diagram(
        "Tres formas de indexar un documento",
        filename="c2_s4_d3_indices",
        show=False,
        direction="LR",
        graph_attr=GRAPH_ATTR,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
    ):
        columna = Postgresql("transacciones\n.autorizacion\njsonb")

        with Cluster("GIN completo"):
            gin = Storage("Indexa cada clave\ny cada valor\n2.4 MB")

        with Cluster("GIN jsonb_path_ops"):
            path = Storage("Solo rutas completas\n1.7 MB")

        with Cluster("B-tree de expresion"):
            btree = Storage("Un solo campo\nordenado")

        decision = Decision("Que operador\nusa la consulta")
        resultado = Document("Plan con\nBitmap Index Scan")

        columna >> decision
        decision >> Edge(label="?  ?|  ?&  @>") >> gin
        decision >> Edge(label="solo @>") >> path
        decision >> Edge(label="rangos sobre\nun campo") >> btree
        gin >> resultado
        path >> resultado
        btree >> resultado


if __name__ == "__main__":
    renderizar_plantuml()
    d3_indices()
    print("Diagramas de la sesion 2.4 generados.")
