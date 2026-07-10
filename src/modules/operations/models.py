# src/modules/operations/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
import datetime
from src.database.connection import Base

class Pozo(Base):
    __tablename__ = "pozos"

    id = Column(Integer, primary_key=True, index=True)
    nombre_pozo = Column(String, unique=True, nullable=False, index=True)
    profundidad_md_ft = Column(Float, nullable=False)
    tipo_pozo = Column(String, nullable=False)
    fecha_registro = Column(DateTime, default=datetime.datetime.utcnow)

    intervenciones = relationship("Intervencion", back_populates="pozo", cascade="all, delete-orphan")


class Intervencion(Base):
    __tablename__ = "intervenciones"

    id = Column(Integer, primary_key=True, index=True)
    pozo_id = Column(Integer, ForeignKey("pozos.id"), nullable=False)
    tipo_servicio = Column(String, nullable=False)  # CEMENTACION, ESTIMULACION, FRACTURA
    ingeniero_a_cargo = Column(String, nullable=False)
    estado = Column(String, default="EN_PROCESO")  # EN_PROCESO, FINALIZADO
    
    # --- Datos de Diseño vs Real ---
    volumen_teorico_bbl = Column(Float, nullable=True)
    volumen_real_bbl = Column(Float, nullable=True)
    presion_max_psi = Column(Float, nullable=True)
    caudal_promedio_bpm = Column(Float, nullable=True)
    
    # --- Control de Seguridad HSE ---
    checklist_presion_lineas = Column(Boolean, default=False)
    checklist_valvulas_alivio = Column(Boolean, default=False)
    checklist_zona_exclusion = Column(Boolean, default=False)
    
    resumen_calculo = Column(String, nullable=True)
    fecha_operacion = Column(DateTime, default=datetime.datetime.utcnow)

    pozo = relationship("Pozo", back_populates="intervenciones")
    
class AlmacenMendoza(Base):
    __tablename__ = "almacen_mendoza"

    id = Column(Integer, primary_key=True, index=True)
    item_nombre = Column(String, unique=True, nullable=False) # Cemento, Retardador, Arena
    unidad = Column(String, nullable=False)                    # Sks, gal, lbs
    stock_actual = Column(Float, default=0.0)
    stock_minimo_alerta = Column(Float, default=100.0)         # Punto de reorden
