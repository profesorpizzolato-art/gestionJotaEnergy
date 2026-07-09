# src/modules/operations/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from src.database.connection import Base

class Pozo(Base):
    __tablename__ = "pozos"

    id = Column(Integer, primary_key=True, index=True)
    nombre_pozo = Column(String, unique=True, nullable=False, index=True)
    profundidad_md_ft = Column(Float, nullable=False)
    tipo_pozo = Column(String, nullable=False)  # Vertical, Dirigido, Horizontal
    fecha_registro = Column(DateTime, default=datetime.datetime.utcnow)

    # Relación con las intervenciones que se le hagan al pozo
    intervenciones = relationship("Intervencion", back_populates="pozo", cascade="all, delete-orphan")


class Intervencion(Base):
    __tablename__ = "intervenciones"

    id = Column(Integer, primary_key=True, index=True)
    pozo_id = Column(Integer, ForeignKey("pozos.id"), nullable=False)
    tipo_servicio = Column(String, nullable=False)  # CEMENTACION, ESTIMULACION, etc.
    ingeniero_a_cargo = Column(String, nullable=False)
    estado = Column(String, default="FINALIZADO")  # EN_PROCESO, FINALIZADO
    resumen_calculo = Column(String, nullable=True)  # Se guardará el string con los bbl, sacos, etc.
    fecha_operacion = Column(DateTime, default=datetime.datetime.utcnow)

    # Relación inversa hacia el pozo
    pozo = relationship("Pozo", back_populates="intervenciones")
