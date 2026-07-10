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

# Inicialización de DB
Base.metadata.create_all(bind=engine)
db_init = SessionLocal()
PumpingService.inicializar_almacen_si_vacio(db_init)
db_init.close()

# Barra Lateral
with st.sidebar:
    st.title("⚙️ Jota Energy")
    st.caption("Base Logística & Control de Suministros")
    st.markdown("---")
    
    st.subheader("📍 Alta de Pozo Target")
    nombre = st.text_input("Nombre del Pozo")
    md = st.number_input("Profundidad MD (ft)", value=4500.0)
    tipo = st.selectbox("Tipo", ["Exploratorio", "Desarrollo", "Inyector"])
    
    if st.button("Guardar Activo Patrimonial"):
        if nombre:
            db = SessionLocal()
            if not db.query(Pozo).filter(Pozo.nombre_pozo == nombre).first():
                db.add(Pozo(nombre_pozo=nombre, profundidad_md_ft=md, tipo_pozo=tipo))
                db.commit()
                st.success("✔️ Pozo dado de alta.")
            db.close()
            st.rerun()

    st.markdown("---")
    st.subheader("📦 Niveles de Stock Real")
    db = SessionLocal()
    for s in db.query(AlmacenMendoza).all():
        st.metric(label=s.item_nombre, value=f"{s.stock_actual:,.1f} {s.unidad}")
    db.close()

# Panel Principal
tab1, tab2, tab3, tab4 = st.tabs(["🧪 Cementación", "⚡ Estimulación", "🛑 Abandono", "📊 Auditoría"])

with tab1:
    st.subheader("🧪 Ingeniería de Cementación Primaria")
    col1, col2 = st.columns(2)
    with col1:
        id_pozo = st.number_input("Diámetro Pozo (in)", value=8.5)
        od_casing = st.number_input("OD Casing (in)", value=7.0)
        longitud = st.number_input("Intervalo (ft)", value=1000.0)
        rend = st.number_input("Rendimiento (ft³/saco)", value=1.18)
    
    if st.button("Calcular y Registrar"):
        vol = CementCalculator.calcular_volumen_espacio_anular(od_casing, id_pozo, longitud)
        sacos = math.ceil(CementCalculator.calcular_requerimiento_sacos(vol, rend))
        st.info(f"Resultados: {vol:.2f} bbl de volumen | {sacos} sacos necesarios.")
        
        db = SessionLocal()
        nueva = Intervencion(pozo_id=1, tipo_servicio="CEMENTACION", volumen_teorico_bbl=vol)
        db.add(nueva)
        db.commit()
        db.close()
        st.success("Protocolo validado y registrado.")

with tab4:
    st.subheader("📊 Auditoría de Suministros (ERP)")
    db = SessionLocal()
    movs = db.query(HistorialAlmacen).all()
    if movs:
        data = [{"Fecha": m.fecha, "Insumo": m.item_id, "Tipo": m.tipo_movimiento, "Cant": m.cantidad} for m in movs]
        st.table(data)
    db.close()
