import streamlit as st
import math
from src.database.connection import engine, Base, SessionLocal
from src.modules.operations.models import Pozo, Intervencion, AlmacenMendoza, HistorialAlmacen
from src.modules.pumping.calculator import CementCalculator
from src.modules.pumping.services import PumpingService

st.set_page_config(page_title="Jota Energy - Sistema de Gestión Operativa", page_icon="⚡", layout="wide")

# CSS Corporativo
st.markdown("""
<style>
    h1, h2, h3 { color: #1E7373 !important; }
    .stButton>button { background-color: #1E7373; color: white; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# Inicialización DB
Base.metadata.create_all(bind=engine)
db_init = SessionLocal()
PumpingService.inicializar_almacen_si_vacio(db_init)
db_init.close()

# Sidebar
with st.sidebar:
    st.title("⚙️ Jota Energy")
    nombre_pozo = st.text_input("Alta Pozo Target")
    if st.button("Guardar Activo"):
        db = SessionLocal()
        db.add(Pozo(nombre_pozo=nombre_pozo, profundidad_md_ft=4500, tipo_pozo="Desarrollo"))
        db.commit()
        db.close()
        st.rerun()

# Tab 1: Cementación con toda su lógica
tab1, tab2, tab3, tab4 = st.tabs(["🧪 Cementación", "⚡ Fractura", "🛑 Abandono", "📊 Auditoría"])

with tab1:
    st.subheader("🧪 Ingeniería de Cementación Primaria")
    col1, col2 = st.columns(2)
    with col1:
        id_pozo = st.number_input("Diámetro del Pozo (in)", value=8.5)
        od_casing = st.number_input("OD Casing (in)", value=7.0)
        longitud = st.number_input("Longitud (ft)", value=1000.0)
        rendimiento = st.number_input("Rendimiento (ft³/saco)", value=1.18)
    
    if st.button("Calcular y Registrar Operación"):
        vol = CementCalculator.calcular_volumen_espacio_anular(od_casing, id_pozo, longitud)
        sacos = math.ceil(CementCalculator.calcular_requerimiento_sacos(vol, rendimiento))
        st.write(f"Volumen Anular: {vol:.2f} bbl")
        st.write(f"Sacos requeridos: {sacos}")
        
        # Registro en BD
        db = SessionLocal()
        nueva_int = Intervencion(pozo_id=1, tipo_servicio="CEMENTACION", volumen_teorico_bbl=vol)
        db.add(nueva_int)
        db.commit()
        db.close()
        st.success("Operación registrada en ERP")

# Tab 4: Auditoría Completa
with tab4:
    st.subheader("📊 Historial de Auditoría")
    db = SessionLocal()
    movs = db.query(HistorialAlmacen).all()
    if movs:
        for m in movs:
            st.write(f"Movimiento: {m.tipo_movimiento} | Cantidad: {m.cantidad}")
    db.close()
