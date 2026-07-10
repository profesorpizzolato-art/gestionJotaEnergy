import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

import streamlit as st
import math
from sqlalchemy import inspect
from src.database.connection import engine, Base, SessionLocal
from src.modules.operations.models import Pozo, Intervencion, AlmacenMendoza, HistorialAlmacen
from src.modules.pumping.calculator import CementCalculator
from src.modules.pumping.services import PumpingService

# Configuración inicial
st.set_page_config(page_title="Jota Energy - Sistema Integral", layout="wide")

# Inicialización de BD
if not inspect(engine).has_table("pozos"):
    Base.metadata.create_all(bind=engine)

db = SessionLocal()
if db.query(AlmacenMendoza).count() == 0:
    PumpingService.inicializar_almacen_si_vacio(db)
if db.query(Pozo).count() == 0:
    db.add(Pozo(nombre_pozo="Pozo Operativo 01", profundidad_md_ft=5000, tipo_pozo="Desarrollo"))
    db.commit()
db.close()

# --- INTERFAZ ---
st.title("⚡ Jota Energy - Gestión Operativa")
tab_cem, tab_est, tab_aba, tab_aud = st.tabs(["🧪 Cementación", "⚡ Estimulación", "🛑 Abandono", "📊 Auditoría"])

def registrar_operacion(tipo, datos_extra=None):
    db = SessionLocal()
    try:
        nueva = Intervencion(pozo_id=1, tipo_servicio=tipo, ingeniero_a_cargo="Admin", **(datos_extra or {}), estado="FINALIZADO")
        db.add(nueva)
        db.commit()
        st.success(f"{tipo} registrada correctamente.")
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        db.close()
        st.rerun()

with tab_cem:
    if st.button("Ejecutar Cementación"):
        registrar_operacion("CEMENTACION")

with tab_est:
    if st.button("Ejecutar Estimulación"):
        registrar_operacion("FRACTURA")

with tab_aba:
    if st.button("Ejecutar Abandono"):
        registrar_operacion("ABANDONO", {"chk_hermeticidad": True})

with tab_aud:
    st.subheader("📊 Auditoría de Datos")
    db = SessionLocal()
    int_data = [{"ID": i.id, "Tipo": i.tipo_servicio, "Ing": i.ingeniero_a_cargo} for i in db.query(Intervencion).all()]
    st.table(int_data)
    db.close()
