"""
c2_s3_b0_diagramas.py
Genera los diagramas de la sesion 2.3.

Produce tres figuras:
    c2_s3_d1_ventana_vs_group.png   desde PlantUML
    c2_s3_d2_marco.png              desde PlantUML
    c2_s3_d3_cte_recursiva.png      desde mingrammer/diagrams

Requisitos:
    pip install diagrams
    Graphviz instalado en el sistema
    Java instalado y plantuml.jar en el directorio actual

Ejecucion: python c2_s3_b0_diagramas.py
"""

import subprocess
from pathlib import Path

from diagrams import Diagram, Cluster, Edge
from diagrams.programming.flowchart import Decision, StartEnd, Action
from diagrams.generic.storage import Storage

PLANTUML_JAR = Path("plantuml.jar")
FUENTES_PUML = [
    "c2_s3_d1_ventana_vs_group.puml",
    "c2_s3_d2_marco.puml",
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


def d3_cte_recursiva():
    """Las tres partes de una CTE recursiva."""
    with Diagram(
        "Estructura de una CTE recursiva",
        filename="c2_s3_d3_cte_recursiva",
        show=False,
        direction="TB",
        graph_attr=GRAPH_ATTR,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
    ):
        inicio = StartEnd("WITH RECURSIVE\ncalendario AS (")

        with Cluster("1. Caso base"):
            base = Action("SELECT DATE '2026-01-01'\nse ejecuta una vez")

        with Cluster("2. Paso recursivo"):
            paso = Action("SELECT mes + 1 mes\nFROM calendario")

        with Cluster("3. Condicion de parada"):
            parada = Decision("WHERE mes <\n'2026-06-01'")

        acumulado = Storage("Resultado acumulado\nde todas las vueltas")
        fin = StartEnd("SELECT * FROM calendario")

        inicio >> base
        base >> Edge(label="UNION ALL") >> paso
        paso >> parada
        parada >> Edge(label="se cumple:\nnueva vuelta") >> paso
        parada >> Edge(label="no se cumple:\nse detiene") >> acumulado
        base >> Edge(style="dashed", label="aporta la\nprimera fila") >> acumulado
        acumulado >> fin


if __name__ == "__main__":
    renderizar_plantuml()
    d3_cte_recursiva()
    print("Diagramas de la sesion 2.3 generados.")
