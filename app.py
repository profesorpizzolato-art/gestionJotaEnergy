import sys
import os
from pathlib import Path

# --- GESTIÓN DE RUTAS (SOLUCIÓN AL KEYERROR) ---
# Forzamos la raíz del proyecto en el PATH de Python
sys.path.append(str(Path(__file__).resolve().parent))

import streamlit as st
import math
from sqlalchemy import inspect

# Importaciones tras configurar el sys.path
from src.database.connection import engine, Base, SessionLocal
from src.modules.operations.models import Pozo, Intervencion, AlmacenMendoza, HistorialAlmacen
from src.modules.pumping.calculator import CementCalculator
from src.modules.pumping.services import PumpingService

# Configuración de página
st.set_page_config(page_title="Jota Energy - Sistema de Gestión Operativa", page_icon="⚡", layout="wide")

# CSS Corporativo
st.markdown("""
<style>
    h1, h2, h3 { color: #1E7373 !important; }
    .stButton>button { background-color: #1E7373; color: white; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# Inicialización segura de Base de Datos
if not inspect(engine).has_table("pozos"):
    Base.metadata.create_all(bind=engine)

db_init = SessionLocal()
PumpingService.inicializar_almacen_si_vacio(db_init)
db_init.close()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://raw.githubusercontent.com/profesorpizzolato-art/gestionjotaenergy/main/logo_menfa.png", width=140)
    st.title("⚙️ Jota Energy")
    st.subheader("📍 Alta de Pozo Target")
    nombre_pozo = st.text_input("Nombre del Pozo")
    md = st.number_input("Profundidad MD (ft)", value=4500.0)
    tipo = st.selectbox("Tipo", ["Exploratorio", "Desarrollo", "Inyector"])
    
    if st.button("Guardar Activo Patrimonial"):
        if nombre_pozo:
            db = SessionLocal()
            try:
                db.add(Pozo(nombre_pozo=nombre_pozo, profundidad_md_ft=md, tipo_pozo=tipo))
                db.commit()
                st.success("Pozo guardado")
            finally:
                db.close()
                st.rerun()

# --- PANEL PRINCIPAL ---
tab_cem, tab_est, tab_aba, tab_aud = st.tabs(["🧪 Cementación", "⚡ Estimulación", "🛑 Abandono", "📊 Auditoría"])

with tab_cem:
    st.subheader("🧪 Ingeniería de Cementación")
    col1, col2 = st.columns(2)
    with col1:
        id_pozo = st.number_input("Diámetro Pozo (in)", value=8.5)
        od_casing = st.number_input("OD Casing (in)", value=7.0)
        long = st.number_input("Longitud (ft)", value=1000.0)
    with col2:
        ing = st.text_input("Ingeniero", key="cem_ing")
        if st.button("Ejecutar Cementación"):
            db = SessionLocal()
            vol = CementCalculator.calcular_volumen_espacio_anular(od_casing, id_pozo, long)
            sacos = math.ceil(CementCalculator.calcular_requerimiento_sacos(vol, 1.18))
            log = PumpingService.verificar_y_descontar_stock(db, sacos, 0, nombre_pozo or "Pozo Default")
            if log["status"] == "OK":
                db.add(Intervencion(pozo_id=1, tipo_servicio="CEMENTACION", ingeniero_a_cargo=ing, estado="FINALIZADO"))
                db.commit()
                st.success("Operación registrada.")
            else: st.error(log["msg"])
            db.close()

with tab_aud:
    st.subheader("📊 Auditoría Integral")
    db_a = SessionLocal()
    st.table([{"ID": i.id, "Tipo": i.tipo_servicio, "Ing": i.ingeniero_a_cargo} for i in db_a.query(Intervencion).all()])
    db_a.close()
