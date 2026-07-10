import streamlit as st
import math
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

# Inicialización segura
# Verificamos si las tablas existen antes de intentar crearlas
from sqlalchemy import inspect
inspector = inspect(engine)
if not inspector.has_table("pozos"):
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
            db.add(Pozo(nombre_pozo=nombre_pozo, profundidad_md_ft=md, tipo_pozo=tipo))
            db.commit()
            db.close()
            st.rerun()

    st.markdown("---")
    st.subheader("📦 Niveles de Stock Real")
    db_s = SessionLocal()
    for s in db_s.query(AlmacenMendoza).all():
        st.metric(label=s.item_nombre, value=f"{s.stock_actual:,.1f} {s.unidad}")
    db_s.close()

# --- PANEL PRINCIPAL ---
tab_cem, tab_est, tab_aba, tab_aud = st.tabs(["🧪 Cementación", "⚡ Estimulación", "🛑 Abandono", "📊 Auditoría"])

with tab_cem:
    st.subheader("🧪 Ingeniería de Cementación Primaria — API RP 65-2")
    col1, col2 = st.columns(2)
    with col1:
        id_pozo = st.number_input("Diámetro Pozo (in)", value=8.5)
        od_casing = st.number_input("OD Casing (in)", value=7.0)
        longitud = st.number_input("Longitud (ft)", value=1000.0)
        rend = st.number_input("Rendimiento (ft³/saco)", value=1.18)
    with col2:
        ing_cargo = st.text_input("Ingeniero a cargo")
        presion_max = st.number_input("Presión Máx (psi)", value=2500.0)
        caudal = st.number_input("Caudal Prom (bpm)", value=4.0)
    
    if st.button("Ejecutar Protocolo Cementación"):
        if not ing_cargo: st.error("⚠️ Ingeniero obligatorio.")
        else:
            vol = CementCalculator.calcular_volumen_espacio_anular(od_casing, id_pozo, longitud)
            sacos = math.ceil(CementCalculator.calcular_requerimiento_sacos(vol, rend))
            db = SessionLocal()
            log = PumpingService.verificar_y_descontar_stock(db, sacos, 0, nombre_pozo)
            if log["status"] == "OK":
                nueva = Intervencion(pozo_id=1, tipo_servicio="CEMENTACION", ingeniero_a_cargo=ing_cargo, 
                                     volumen_teorico_bbl=vol, volumen_real_bbl=vol, presion_max_psi=presion_max, 
                                     caudal_promedio_bpm=caudal, estado="FINALIZADO")
                db.add(nueva)
                db.commit()
                st.success("Cementación registrada.")
            else: st.error(log["msg"])
            db.close()

with tab_est:
    st.subheader("⚡ Estimulación y Fractura")
    lbs_arena = st.number_input("Carga de Apuntalante (lbs)", value=50000.0)
    ing_est = st.text_input("Ingeniero a cargo", key="est_ing")
    if st.button("Ejecutar Estimulación"):
        db = SessionLocal()
        log = PumpingService.verificar_y_descontar_arena(db, lbs_arena, nombre_pozo)
        if log["status"] == "OK":
            nueva = Intervencion(pozo_id=1, tipo_servicio="FRACTURA", ingeniero_a_cargo=ing_est, 
                                 volumen_teorico_bbl=0, volumen_real_bbl=0, presion_max_psi=0, caudal_promedio_bpm=0, estado="FINALIZADO")
            db.add(nueva)
            db.commit()
            st.success("Fractura registrada y stock descontado.")
        else: st.error(log["msg"])
        db.close()

with tab_aba:
    st.subheader("🛑 Abandono de Pozos (P&A)")
    herm = st.checkbox("Certificación de Hermeticidad (Check)")
    ing_aba = st.text_input("Ingeniero a cargo", key="aba_ing")
    if st.button("Ejecutar Abandono"):
        db = SessionLocal()
        nueva = Intervencion(pozo_id=1, tipo_servicio="ABANDONO", ingeniero_a_cargo=ing_aba, 
                             chk_hermeticidad=herm, volumen_teorico_bbl=0, volumen_real_bbl=0, 
                             presion_max_psi=0, caudal_promedio_bpm=0, estado="FINALIZADO")
        db.add(nueva)
        db.commit()
        db.close()
        st.success("Protocolo de abandono finalizado.")

with tab_aud:
    st.subheader("📊 Auditoría Integral (ERP)")
    db_a = SessionLocal()
    st.markdown("##### Intervenciones")
    st.table([{"ID": i.id, "Tipo": i.tipo_servicio, "Ing": i.ingeniero_a_cargo, "Estado": i.estado} for i in db_a.query(Intervencion).all()])
    st.markdown("##### Movimientos de Inventario")
    st.table([{"Fecha": m.fecha.strftime("%Y-%m-%d"), "Insumo": m.item_id, "Tipo": m.tipo_movimiento, "Cant": m.cantidad} for m in db_a.query(HistorialAlmacen).all()])
    db_a.close()
