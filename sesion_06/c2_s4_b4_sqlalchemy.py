"""
c2_s4_b4_sqlalchemy.py
SQLAlchemy 2.0 con estilo declarativo moderno, y JSONB desde Python.

Puntos de la sesion que este script ejercita:
    - el estilo declarativo de la version 2.0, con Mapped y mapped_column
    - consulta con select() y session.execute(), no con session.query()
    - acceso a campos JSONB desde el mapeo
    - cuando conviene el mapeo objeto-relacional y cuando no

Requisitos: base pagos cargada, columna autorizacion presente, .env
    pip install "psycopg[binary]" python-dotenv sqlalchemy
Ejecucion: python c2_s4_b4_sqlalchemy.py
"""

import os
from datetime import datetime
from decimal import Decimal
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import (ForeignKey, Numeric, String, create_engine, func,
                        select, text)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (DeclarativeBase, Mapped, Session, mapped_column,
                            relationship)

load_dotenv()


def uri():
    """El prefijo declara el controlador de forma explicita.

    Con postgresql:// a secas, SQLAlchemy 2.0 busca psycopg2, que es el
    controlador de la generacion anterior.
    """
    return (f"postgresql+psycopg://{os.getenv('POSTGRES_USER')}:"
            f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('PGHOST', 'localhost')}:"
            f"{os.getenv('PGPORT', '5432')}/{os.getenv('POSTGRES_DB')}")


def titulo(texto):
    print("\n" + "=" * 70 + f"\n{texto}\n" + "=" * 70)


# =====================================================================
# El mapeo, en estilo 2.0
#
# Diferencias con el estilo 1.x que todavia circula en documentacion y
# en respuestas de foros:
#
#   1.x   class Base(declarative_base())
#         nombre = Column(String(120), nullable=False)
#         session.query(Comercio).filter_by(ciudad='Merida').all()
#
#   2.0   class Base(DeclarativeBase)
#         nombre: Mapped[str] = mapped_column(String(120))
#         session.execute(select(Comercio).where(...)).scalars().all()
#
# La anotacion de tipo no es decorativa: de ella sale la nulabilidad.
# Mapped[str] implica NOT NULL; Mapped[Optional[str]] admite nulo.
# =====================================================================

class Base(DeclarativeBase):
    pass


class Comercio(Base):
    __tablename__ = "comercios"
    __table_args__ = {"schema": "pagos"}

    id_comercio: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    categoria: Mapped[str] = mapped_column(String(60))
    ciudad: Mapped[str] = mapped_column(String(80))

    terminales: Mapped[list["Terminal"]] = relationship(back_populates="comercio")

    def __repr__(self):
        return f"Comercio({self.nombre!r}, {self.ciudad!r})"


class Terminal(Base):
    __tablename__ = "terminales"
    __table_args__ = {"schema": "pagos"}

    id_terminal: Mapped[int] = mapped_column(primary_key=True)
    id_comercio: Mapped[int] = mapped_column(ForeignKey("pagos.comercios.id_comercio"))
    codigo: Mapped[str] = mapped_column(String(30))

    comercio: Mapped["Comercio"] = relationship(back_populates="terminales")
    transacciones: Mapped[list["Transaccion"]] = relationship(
        back_populates="terminal")


class Transaccion(Base):
    __tablename__ = "transacciones"
    __table_args__ = {"schema": "pagos"}

    id_transaccion: Mapped[str] = mapped_column(String(20), primary_key=True)
    fecha_hora: Mapped[datetime]
    id_terminal: Mapped[int] = mapped_column(
        ForeignKey("pagos.terminales.id_terminal"))
    id_tarjeta: Mapped[int]
    # Numeric(12, 2) del lado del motor corresponde con Decimal del lado
    # de Python. Declararlo como float perderia la aritmetica exacta,
    # que es la decision de la sesion 2.1.
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    moneda: Mapped[str] = mapped_column(String(3))
    estatus: Mapped[str] = mapped_column(String(20))
    metodo_captura: Mapped[str] = mapped_column(String(20))
    # El documento se mapea como JSONB. SQLAlchemy lo entrega como
    # diccionario de Python y lo convierte de vuelta al escribir.
    autorizacion: Mapped[Optional[dict]] = mapped_column(JSONB)

    terminal: Mapped["Terminal"] = relationship(back_populates="transacciones")


# =====================================================================
# Bloque 1. Consulta en estilo 2.0
# =====================================================================

def bloque_1_estilo_moderno(motor):
    titulo("Bloque 1: select() y session.execute()")

    with Session(motor) as sesion:
        # scalars() devuelve objetos del modelo, no tuplas.
        consulta = select(Comercio).where(Comercio.ciudad == "Ciudad de Mexico")
        for comercio in sesion.execute(consulta).scalars():
            print(f"  {comercio}")

        # Sin scalars(), el resultado son tuplas de columnas.
        consulta = (select(Comercio.nombre, func.count(Terminal.id_terminal))
                    .join(Terminal)
                    .group_by(Comercio.nombre)
                    .order_by(func.count(Terminal.id_terminal).desc()))
        print("\n  Terminales por comercio:")
        for nombre, total in sesion.execute(consulta):
            print(f"    {nombre:<22} {total}")

    print("""
  session.query() sigue funcionando por compatibilidad, y es lo que
  aparece en la mayor parte de la documentacion antigua. El estilo 2.0
  usa select() y session.execute(), que es el mismo constructor que se
  usa fuera del mapeo.
""")


# =====================================================================
# Bloque 2. Acceso a JSONB desde el mapeo
# =====================================================================

def bloque_2_jsonb(motor):
    titulo("Bloque 2: campos JSONB desde el mapeo")

    with Session(motor) as sesion:
        # El documento llega como diccionario de Python.
        transaccion = sesion.execute(
            select(Transaccion).where(Transaccion.metodo_captura == "QR").limit(1)
        ).scalars().one()

        print(f"  Transaccion: {transaccion.id_transaccion}")
        print(f"  Tipo del atributo: {type(transaccion.autorizacion).__name__}")
        print(f"  Emisor: {transaccion.autorizacion['emisor']['nombre']}")
        print(f"  Aplicacion: {transaccion.autorizacion['captura']['aplicacion']}")

        # El filtro puede ocurrir del lado del motor, sobre el documento.
        # El operador de indexacion se traduce a -> y ->>
        consulta = (
            select(func.count())
            .select_from(Transaccion)
            .where(Transaccion.autorizacion["emisor"]["nombre"].astext == "BANORTE")
        )
        print(f"\n  Operaciones del emisor BANORTE: "
              f"{sesion.execute(consulta).scalar()}")

        # El operador de contencion, que es el que aprovecha el indice GIN.
        consulta = (
            select(func.count())
            .select_from(Transaccion)
            .where(Transaccion.autorizacion.contains(
                {"captura": {"aplicacion": "CoDi"}}))
        )
        print(f"  Operaciones con CoDi: {sesion.execute(consulta).scalar()}")

    print("""
  Punto importante: filtrar en Python despues de traer las filas
  deshace la ventaja del indice. La condicion debe expresarse en la
  consulta, para que el motor la resuelva.
""")


# =====================================================================
# Bloque 3. El costo oculto del mapeo
# =====================================================================

def bloque_3_costo_del_mapeo(motor):
    titulo("Bloque 3: el problema de las consultas en cadena")

    with Session(motor) as sesion:
        print("\n  Sin carga anticipada, cada acceso a la relacion")
        print("  dispara una consulta adicional:\n")

        comercios = sesion.execute(select(Comercio)).scalars().all()
        consultas = 1
        for comercio in comercios:
            _ = len(comercio.terminales)   # cada acceso consulta la base
            consultas += 1
        print(f"    {len(comercios)} comercios  ->  {consultas} consultas")

    with Session(motor) as sesion:
        from sqlalchemy.orm import selectinload
        print("\n  Con carga anticipada, dos consultas en total:\n")
        comercios = sesion.execute(
            select(Comercio).options(selectinload(Comercio.terminales))
        ).scalars().all()
        for comercio in comercios:
            _ = len(comercio.terminales)
        print(f"    {len(comercios)} comercios  ->  2 consultas")

    print("""
  Con siete comercios la diferencia es irrelevante. Con siete mil, son
  siete mil consultas contra dos.

  Este patron aparece con frecuencia en codigo escrito con mapeo, y no
  produce ningun error: solo se vuelve lento. Es el argumento principal
  para conocer que SQL genera el mapeo.
""")


# =====================================================================
# Bloque 4. Cuando conviene el mapeo y cuando no
# =====================================================================

def bloque_4_criterio(motor):
    titulo("Bloque 4: mapeo o SQL directo")

    with Session(motor) as sesion:
        # Una consulta analitica con ventana, expresada en SQL directo.
        # Escribirla con el mapeo seria mas largo y menos legible.
        resultado = sesion.execute(text("""
            SELECT c.nombre,
                   SUM(t.monto) AS importe,
                   ROUND(100.0 * SUM(t.monto)
                         / SUM(SUM(t.monto)) OVER (), 2) AS pct
            FROM pagos.transacciones t
            JOIN pagos.terminales te ON te.id_terminal = t.id_terminal
            JOIN pagos.comercios  c  ON c.id_comercio  = te.id_comercio
            WHERE t.estatus = 'APROBADA'
            GROUP BY c.nombre
            ORDER BY importe DESC
        """)).all()

        print("\n  Consulta analitica en SQL directo:")
        for nombre, importe, pct in resultado:
            print(f"    {nombre:<22} {importe:>14,.2f}  {pct:>6}%")

    print("""
  Criterio:

    Conviene el mapeo cuando
      la unidad de trabajo es una entidad completa que se lee, se
        modifica y se guarda
      hay muchas operaciones parecidas sobre las mismas entidades
      importa la portabilidad entre motores

    Conviene el SQL directo cuando
      la consulta es analitica: agregaciones, ventanas, CTE
      el resultado no corresponde con ninguna entidad del modelo
      se usan caracteristicas propias del motor, como JSONB o GIN

  En un mismo proyecto conviven ambos, y esa convivencia es lo normal.
  El error no es elegir uno u otro, sino usar el mapeo para consultas
  analiticas sin saber que SQL genera.
""")


if __name__ == "__main__":
    motor = create_engine(uri())
    bloque_1_estilo_moderno(motor)
    bloque_2_jsonb(motor)
    bloque_3_costo_del_mapeo(motor)
    bloque_4_criterio(motor)
