import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from src.database.connection import Base

class Pozo(Base):
    __tablename__ = "pozos"
    id = Column(Integer, primary_key=True, index=True)
    nombre_pozo = Column(String, unique=True, index=True, nullable=False)
    profundidad_md_ft = Column(Float, nullable=False)
    tipo_pozo = Column(String, nullable=False)

class Intervencion(Base):
    __tablename__ = "intervenciones"
    id = Column(Integer, primary_key=True, index=True)
    pozo_id = Column(Integer, ForeignKey("pozos.id"), nullable=False)
    tipo_servicio = Column(String, nullable=False) # CEMENTACION, FRACTURA, ABANDONO
    
    # Ahora permitimos nulos en los campos que se llenan post-operación
    ingeniero_a_cargo = Column(String, nullable=True) 
    volumen_teorico_bbl = Column(Float, nullable=True)
    volumen_real_bbl = Column(Float, nullable=True)
    presion_max_psi = Column(Float, nullable=True)
    caudal_promedio_bpm = Column(Float, nullable=True)
    
    # Protocolos Normalizados QHSE
    chk_presion_lineas = Column(Boolean, default=False)
    chk_valvulas_alivio = Column(Boolean, default=False)
    chk_zona_exclusion = Column(Boolean, default=False)
    chk_control_gel = Column(Boolean, default=False)
    chk_hermeticidad = Column(Boolean, default=False)
    
    estado = Column(String, default="PLANIFICADO")
    resumen_calculo = Column(String, nullable=True)
    fecha_operacion = Column(DateTime, default=datetime.datetime.utcnow)

class AlmacenMendoza(Base):
    __tablename__ = "almacen_mendoza"
    id = Column(Integer, primary_key=True, index=True)
    item_nombre = Column(String, unique=True, nullable=False)
    unidad = Column(String, nullable=False)
    stock_actual = Column(Float, default=0.0)
    stock_minimo_alerta = Column(Float, default=100.0)

class HistorialAlmacen(Base):
    __tablename__ = "historial_almacen"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("almacen_mendoza.id"), nullable=False)
    tipo_movimiento = Column(String, nullable=False)
    cantidad = Column(Float, nullable=False)
    referencia = Column(String, nullable=True)
    fecha = Column(DateTime, default=datetime.datetime.utcnow)
