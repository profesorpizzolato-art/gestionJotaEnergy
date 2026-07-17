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

# --- SIDEBAR ---
with st.sidebar:
    # Como el archivo está en la raíz, usamos simplemente el nombre del archivo
    st.image("jota_ene.jpg", width=140) 
    st.title("⚙️ Jota Energy")
    st.subheader("📦 Stock Real")
    db_s = SessionLocal()
    for s in db_s.query(AlmacenMendoza).all():
        st.metric(label=s.item_nombre, value=f"{s.stock_actual:,.1f} {s.unidad}")
    db_s.close()

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
        checks, evidencia = renderizar_protocolo_con_evidencias("CEMENTACION")
        if st.button("Ejecutar Cementación"):
            if not all(checks.values()): st.warning("⚠️ Completa los protocolos QHSE.")
            else:
                db = SessionLocal()
                vol = CementCalculator.calcular_volumen_espacio_anular(od, diam, long)
                sacos = math.ceil(CementCalculator.calcular_requerimiento_sacos(vol, 1.18))
                log = PumpingService.verificar_y_descontar_stock(db, sacos, 0, "Pozo Operativo 01")
                if log["status"] == "OK":
                    db.add(Intervencion(pozo_id=1, tipo_servicio="CEMENTACION", ingeniero_a_cargo=ing, resumen_calculo=json.dumps(evidencia), estado="FINALIZADO"))
                    db.commit()
                    st.success("Cementación y evidencias registradas.")
                    st.rerun()
                else: st.error(log["msg"])
                db.close()

with tab_est:
    st.subheader("⚡ Estimulación y Fractura")
    lbs_arena = st.number_input("Carga de Apuntalante (lbs)", value=50000.0)
    ing_est = st.text_input("Ingeniero a cargo", key="est_ing")
    checks, evidencia = renderizar_protocolo_con_evidencias("FRACTURA")
    if st.button("Ejecutar Estimulación"):
        if not all(checks.values()): st.warning("⚠️ Completa los protocolos QHSE.")
        else:
            db = SessionLocal()
            log = PumpingService.verificar_y_descontar_arena(db, lbs_arena, "Pozo Operativo 01")
            if log["status"] == "OK":
                db.add(Intervencion(pozo_id=1, tipo_servicio="FRACTURA", ingeniero_a_cargo=ing_est, resumen_calculo=json.dumps(evidencia), estado="FINALIZADO"))
                db.commit()
                st.success("Fractura y evidencias registradas.")
                st.rerun()
            else: st.error(log["msg"])
            db.close()

with tab_aba:
    st.subheader("🛑 Abandono de Pozos (P&A)")
    ing_aba = st.text_input("Ingeniero a cargo", key="aba_ing")
    checks, evidencia = renderizar_protocolo_con_evidencias("ABANDONO")
    if st.button("Ejecutar Abandono"):
        if not all(checks.values()): st.warning("⚠️ Completa los protocolos QHSE.")
        else:
            db = SessionLocal()
            db.add(Intervencion(pozo_id=1, tipo_servicio="ABANDONO", ingeniero_a_cargo=ing_aba, resumen_calculo=json.dumps(evidencia), estado="FINALIZADO"))
            db.commit()
            st.success("Abandono y protocolos registrados.")
            st.rerun()
            db.close()

with tab_aud:
    st.subheader("📊 Auditoría de Datos")
    db = SessionLocal()
    for i in db.query(Intervencion).all():
        ev = json.loads(i.resumen_calculo) if i.resumen_calculo else {}
        with st.expander(f"{i.tipo_servicio} - Ing: {i.ingeniero_a_cargo}"):
            st.write(f"**Evidencia:** {ev}")
    db.close()
    
with tab_alm: # Agrega esta pestaña en st.tabs
    st.subheader("📦 Gestión de Inventario")
    col1, col2 = st.columns(2)
    with col1:
        item = st.selectbox("Item", [i.item_nombre for i in db.query(AlmacenMendoza).all()])
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
