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

st.set_page_config(page_title="Jota Energy - Sistema Integral", layout="wide")

# Inicialización segura
if not inspect(engine).has_table("pozos"): Base.metadata.create_all(bind=engine)
db = SessionLocal()
if db.query(AlmacenMendoza).count() == 0: PumpingService.inicializar_almacen_si_vacio(db)
if db.query(Pozo).count() == 0:
    db.add(Pozo(nombre_pozo="Pozo Operativo 01", profundidad_md_ft=5000, tipo_pozo="Desarrollo"))
    db.commit()
db.close()

# --- SIDEBAR (RECUPERADO) ---
with st.sidebar:
    st.image("https://raw.githubusercontent.com/profesorpizzolato-art/gestionjotaenergy/main/logo_menfa.png", width=140)
    st.title("⚙️ Jota Energy")
    st.subheader("📦 Stock Real")
    db_s = SessionLocal()
    for s in db_s.query(AlmacenMendoza).all():
        st.metric(label=s.item_nombre, value=f"{s.stock_actual:,.1f} {s.unidad}")
    db_s.close()
    
    st.markdown("---")
    nombre_p = st.text_input("Nuevo Pozo")
    if st.button("Guardar Pozo"):
        db = SessionLocal()
        db.add(Pozo(nombre_pozo=nombre_p, profundidad_md_ft=4500, tipo_pozo="Exploratorio"))
        db.commit()
        db.close()
        st.rerun()

# --- PANEL PRINCIPAL ---
st.title("⚡ Jota Energy - Gestión Operativa")
tab_cem, tab_est, tab_aba, tab_aud = st.tabs(["🧪 Cementación", "⚡ Estimulación", "🛑 Abandono", "📊 Auditoría"])

with tab_cem:
    st.subheader("🧪 Ingeniería de Cementación")
    col1, col2 = st.columns(2)
    with col1:
        diam = st.number_input("Diámetro Pozo (in)", value=8.5)
        od = st.number_input("OD Casing (in)", value=7.0)
        long = st.number_input("Longitud (ft)", value=1000.0)
    with col2:
        ing = st.text_input("Ingeniero a cargo")
        if st.button("Ejecutar Cementación"):
            db = SessionLocal()
            vol = CementCalculator.calcular_volumen_espacio_anular(od, diam, long)
            sacos = math.ceil(CementCalculator.calcular_requerimiento_sacos(vol, 1.18))
            log = PumpingService.verificar_y_descontar_stock(db, sacos, 0, "Pozo Operativo 01")
            if log["status"] == "OK":
                db.add(Intervencion(pozo_id=1, tipo_servicio="CEMENTACION", ingeniero_a_cargo=ing, estado="FINALIZADO"))
                db.commit()
                st.success("Cementación registrada con éxito.")
                st.rerun()
            else: st.error(log["msg"])
            db.close()
with tab_est:
    st.subheader("⚡ Estimulación y Fractura")
    lbs_arena = st.number_input("Carga de Apuntalante (lbs)", value=50000.0, key="est_lbs")
    ing_est = st.text_input("Ingeniero a cargo", key="est_ing")
    
    if st.button("Ejecutar Estimulación"):
        db = SessionLocal()
        try:
            # Usamos tu función de servicio original para descontar la arena
            log = PumpingService.verificar_y_descontar_arena(db, lbs_arena, "Pozo Operativo 01")
            if log["status"] == "OK":
                nueva = Intervencion(pozo_id=1, tipo_servicio="FRACTURA", ingeniero_a_cargo=ing_est, estado="FINALIZADO")
                db.add(nueva)
                db.commit()
                st.success("Fractura registrada y stock descontado.")
                st.rerun()
            else:
                st.error(log["msg"])
        finally:
            db.close()

with tab_aba:
    st.subheader("🛑 Abandono de Pozos (P&A)")
    herm = st.checkbox("Certificación de Hermeticidad")
    ing_aba = st.text_input("Ingeniero a cargo", key="aba_ing")
    
    if st.button("Ejecutar Abandono"):
        db = SessionLocal()
        try:
            nueva = Intervencion(pozo_id=1, tipo_servicio="ABANDONO", ingeniero_a_cargo=ing_aba, chk_hermeticidad=herm, estado="FINALIZADO")
            db.add(nueva)
            db.commit()
            st.success("Protocolo de abandono finalizado.")
            st.rerun()
        finally:
            db.close()
with tab_aud:
    st.subheader("📊 Auditoría de Datos")
    db = SessionLocal()
    st.table([{"ID": i.id, "Tipo": i.tipo_servicio, "Ing": i.ingeniero_a_cargo} for i in db.query(Intervencion).all()])
    db.close()
