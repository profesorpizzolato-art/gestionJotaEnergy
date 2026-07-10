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
""", unsafe_allow_html=True)  # <--- CORREGIDO AQUÍ

# Inicialización
Base.metadata.create_all(bind=engine)
db = SessionLocal()
PumpingService.inicializar_almacen_si_vacio(db)
db.close()

# Barra Lateral (Sidebar)
with st.sidebar:
    st.title("⚙️ Jota Energy")
    st.markdown("---")
    # Formulario de Pozo
    nombre = st.text_input("Nombre del Pozo")
    if st.button("Guardar Activo"):
        db = SessionLocal()
        db.add(Pozo(nombre_pozo=nombre, profundidad_md_ft=4500, tipo_pozo="Desarrollo"))
        db.commit()
        db.close()
        st.rerun()
    # Visualización de Stock
    st.subheader("📦 Stock en Base Mendoza")
    db = SessionLocal()
    for s in db.query(AlmacenMendoza).all():
        st.metric(s.item_nombre, f"{s.stock_actual} {s.unidad}")
    db.close()

# Panel Principal
tab1, tab2, tab3, tab4 = st.tabs(["🧪 Cementación", "⚡ Fractura", "🛑 Abandono", "📊 Auditoría"])

with tab1:
    st.subheader("Ingeniería de Cementación")
    # Aquí puedes insertar los campos de entrada que teníamos (id_pozo, od_casing, etc.)
    # Y llamar a CementCalculator como lo hacíamos antes

with tab4:
    st.subheader("Auditoría ERP")
    db = SessionLocal()
    movs = db.query(HistorialAlmacen).all()
    st.table([{"Insumo": m.item_id, "Cantidad": m.cantidad} for m in movs])
    db.close()
