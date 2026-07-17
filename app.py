import sys
import os
from pathlib import Path
import json
import math
import streamlit as st
from sqlalchemy import inspect

# Configuración de rutas y entorno
sys.path.append(str(Path(__file__).resolve().parent))

from src.database.connection import engine, Base, SessionLocal
from src.modules.operations.models import Pozo, Intervencion, AlmacenMendoza, HistorialAlmacen
from src.modules.pumping.calculator import CementCalculator
from src.modules.pumping.services import PumpingService
from src.modules.safety.protocols import QHSEProtocolos

st.set_page_config(page_title="Jota Energy - Sistema Integral", layout="wide")

# --- FUNCIONES AUXILIARES ---
def renderizar_protocolo_con_evidencias(tipo_operacion):
    st.subheader(f"📋 Protocolos y Evidencia Técnica: {tipo_operacion}")
    protocolos = QHSEProtocolos.obtener_protocolos(tipo_operacion)
    
    check_results = {p: st.checkbox(p, key=f"check_{p}_{tipo_operacion}") for p in protocolos}
    
    st.markdown("---")
    st.markdown("### 📝 Datos de Campo")
    col1, col2 = st.columns(2)
    with col1:
        presion = st.number_input("Presión Final (PSI)", value=0.0, key=f"psi_{tipo_operacion}")
        densidad = st.number_input("Densidad (PPG)", value=0.0, key=f"ppg_{tipo_operacion}")
    with col2:
        obs = st.text_area("Observaciones técnicas", key=f"obs_{tipo_operacion}")
        
    return check_results, {"presion_psi": presion, "densidad_ppg": densidad, "observaciones": obs}

# --- INICIALIZACIÓN ---
if not inspect(engine).has_table("pozos"): Base.metadata.create_all(bind=engine)
db = SessionLocal()
if db.query(AlmacenMendoza).count() == 0: PumpingService.inicializar_almacen_si_vacio(db)
if db.query(Pozo).count() == 0:
    db.add(Pozo(nombre_pozo="Pozo Operativo 01", profundidad_md_ft=5000, tipo_pozo="Desarrollo"))
    db.commit()
db.close()

# --- PANEL PRINCIPAL ---
st.title("⚡ Jota Energy - Gestión Operativa")
# 1. Definición correcta de pestañas
tab_cem, tab_est, tab_aba, tab_alm, tab_aud = st.tabs(["🧪 Cementación", "⚡ Estimulación", "🛑 Abandono", "📦 Almacén", "📊 Auditoría"])

with tab_cem:
    # ... (tu código de cementación igual) ...

with tab_est:
    # ... (tu código de estimulación igual) ...

with tab_aba:
    # ... (tu código de abandono igual) ...

with tab_alm:
    st.subheader("📦 Gestión de Inventario")
    db = SessionLocal() # Abrimos sesión local
    # 2. Asegúrate de tener la clase InventoryManager importada al inicio de tu archivo
    # from src.modules.inventory.manager import InventoryManager
    
    items = db.query(AlmacenMendoza).all()
    item_nombres = [i.item_nombre for i in items]
    
    col1, col2 = st.columns(2)
    with col1:
        item = st.selectbox("Item", item_nombres)
        cant = st.number_input("Cantidad", value=0.0)
    with col2:
        tipo = st.radio("Tipo de Movimiento", ["INGRESO", "EGRESO"])
        ref = st.text_input("Referencia / Remito")
        
        if st.button("Confirmar Movimiento"):
            res = InventoryManager.registrar_movimiento(db, item, cant, tipo, ref)
            if res["status"] == "OK":
                st.success("Movimiento registrado con éxito.")
                st.rerun()
            else:
                st.error(res["msg"])
    db.close()

with tab_aud:
    st.subheader("📊 Auditoría de Datos")
    db = SessionLocal()
    for i in db.query(Intervencion).all():
        ev = json.loads(i.resumen_calculo) if i.resumen_calculo else {}
        with st.expander(f"{i.tipo_servicio} - Ing: {i.ingeniero_a_cargo}"):
            st.write(f"**Evidencia:** {ev}")
    db.close()
