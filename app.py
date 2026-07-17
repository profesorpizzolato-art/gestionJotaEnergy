import sys, json, math, streamlit as st
from pathlib import Path
from sqlalchemy import inspect
sys.path.append(str(Path(__file__).resolve().parent))

from src.database.connection import engine, Base, SessionLocal
from src.modules.operations.models import Pozo, Intervencion, AlmacenMendoza
from src.modules.pumping.calculator import CementCalculator
from src.modules.pumping.services import PumpingService
from src.modules.safety.protocols import QHSEProtocolos
from src.modules.inventory.manager import InventoryManager

st.set_page_config(page_title="Jota Energy - Sistema Integral", layout="wide")

def renderizar_protocolo(tipo):
    st.subheader(f"📋 Protocolos: {tipo}")
    # Usamos el 'tipo' para que las keys de los checkboxes sean únicas
    checks = {p: st.checkbox(p, key=f"chk_{tipo}_{p}") for p in QHSEProtocolos.obtener_protocolos(tipo)}
    
    col1, col2 = st.columns(2)
    # AÑADIMOS KEY ÚNICA a los inputs usando el 'tipo'
    ev = {
        "presion": col1.number_input("PSI", 0.0, key=f"psi_{tipo}"), 
        "obs": col2.text_area("Notas", key=f"notas_{tipo}")
    }
    return checks, ev

# --- INICIALIZACIÓN ---
if not inspect(engine).has_table("pozos"): Base.metadata.create_all(bind=engine)
db = SessionLocal()
if db.query(AlmacenMendoza).count() == 0: 
    PumpingService.inicializar_almacen_si_vacio(db)
    db.commit()
db.close()

# --- SIDEBAR ---
with st.sidebar:
    st.image("jota_ene.jpg", width=140)
    st.title("⚙️ Jota Energy")
    db_s = SessionLocal()
    for s in db_s.query(AlmacenMendoza).all():
        st.metric(s.item_nombre, f"{s.stock_actual:,.1f} {s.unidad}")
    db_s.close()

# --- PESTAÑAS ---
tab_cem, tab_est, tab_aba, tab_alm, tab_aud = st.tabs(["🧪 Cementación", "⚡ Estimulación", "🛑 Abandono", "📦 Almacén y Costos", "📊 Auditoría"])

with tab_cem:
    col1, col2 = st.columns(2)
    diam = col1.number_input("Diámetro (in)", 8.5)
    od = col1.number_input("OD Casing (in)", 7.0)
    long = col1.number_input("Longitud (ft)", 1000.0)
    ing = col2.text_input("Ingeniero")
    checks, ev = renderizar_protocolo("CEMENTACION")
    if st.button("Ejecutar Cementación"):
        if not all(checks.values()): st.warning("Completa los protocolos.")
        else:
            db = SessionLocal()
            vol = CementCalculator.calcular_volumen_espacio_anular(od, diam, long)
            sacos = math.ceil(CementCalculator.calcular_requerimiento_sacos(vol, 1.18))
            log = PumpingService.verificar_y_descontar_stock(db, sacos, 0, "Pozo Operativo 01")
            if log["status"] == "OK":
                db.add(Intervencion(tipo_servicio="CEMENTACION", ingeniero_a_cargo=ing, resumen_calculo=json.dumps(ev), estado="FINALIZADO"))
                db.commit()
                st.success("Registrado.")
            db.close()

with tab_est:
    st.subheader("⚡ Estimulación y Fractura")
    lbs_arena = st.number_input("Carga de Apuntalante (lbs)", 50000.0)
    ing_est = st.text_input("Ingeniero a cargo", key="est_ing")
    checks, ev = renderizar_protocolo("FRACTURA")
    if st.button("Ejecutar Estimulación"):
        if not all(checks.values()): st.warning("Completa los protocolos.")
        else:
            db = SessionLocal()
            log = PumpingService.verificar_y_descontar_arena(db, lbs_arena, "Pozo Operativo 01")
            if log["status"] == "OK":
                db.add(Intervencion(tipo_servicio="FRACTURA", ingeniero_a_cargo=ing_est, resumen_calculo=json.dumps(ev), estado="FINALIZADO"))
                db.commit()
                st.success("Fractura registrada.")
            db.close()

with tab_aba:
    st.subheader("🛑 Abandono de Pozos (P&A)")
    ing_aba = st.text_input("Ingeniero a cargo", key="aba_ing")
    checks, ev = renderizar_protocolo("ABANDONO")
    if st.button("Ejecutar Abandono"):
        if not all(checks.values()): st.warning("Completa los protocolos.")
        else:
            db = SessionLocal()
            db.add(Intervencion(tipo_servicio="ABANDONO", ingeniero_a_cargo=ing_aba, resumen_calculo=json.dumps(ev), estado="FINALIZADO"))
            db.commit()
            st.success("Abandono registrado.")
            db.close()

with tab_alm:
    st.subheader("📦 Gestión de Inventario y Costos")
    db = SessionLocal()
    items = db.query(AlmacenMendoza).all()
    item = st.selectbox("Item", [i.item_nombre for i in items])
    cant = st.number_input("Cantidad", 0.0)
    costo = st.number_input("Costo Unitario ($)", 0.0)
    tipo = st.radio("Movimiento", ["INGRESO", "EGRESO"])
    if st.button("Confirmar Movimiento"):
        res = InventoryManager.registrar_movimiento(db, item, cant, tipo, "Operación Manual", costo)
        if res["status"] == "OK": st.success("Guardado.")
        else: st.error(res["msg"])
    db.close()

with tab_aud:
    st.subheader("📊 Auditoría de Datos")
    db = SessionLocal()
    for i in db.query(Intervencion).all():
        st.write(f"**{i.tipo_servicio}** | Ing: {i.ingeniero_a_cargo} | Datos: {i.resumen_calculo}")
    db.close()
