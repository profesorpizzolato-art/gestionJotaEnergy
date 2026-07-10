import streamlit as st
import math
from src.database.connection import engine, Base, SessionLocal
from src.modules.operations.models import Pozo, Intervencion, AlmacenMendoza, HistorialAlmacen
from src.modules.pumping.calculator import CementCalculator
from src.modules.pumping.services import PumpingService

# Configuración de página
st.set_page_config(page_title="Jota Energy - Sistema de Gestión Operativa", page_icon="⚡", layout="wide")

# CSS para mantener la estética sin romper la funcionalidad
st.markdown("""
<style>
    h1, h2, h3 { color: #1E7373 !important; }
    .stButton>button { background-color: #1E7373; color: white; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# Inicialización
Base.metadata.create_all(bind=engine)
db = SessionLocal()
PumpingService.inicializar_almacen_si_vacio(db)
db.close()

# --- SIDEBAR: GESTIÓN DE ACTIVOS ---
with st.sidebar:
    st.image("https://raw.githubusercontent.com/profesorpizzolato-art/gestionjotaenergy/main/logo_menfa.png", width=140)
    st.title("⚙️ Jota Energy")
    st.subheader("📍 Alta de Pozo Target")
    nombre_pozo = st.text_input("Nombre del Pozo")
    md = st.number_input("Profundidad MD (ft)", value=4500.0)
    tipo = st.selectbox("Tipo", ["Exploratorio", "Desarrollo", "Inyector"])
    
    if st.button("Guardar Activo Patrimonial"):
        db = SessionLocal()
        nuevo = Pozo(nombre_pozo=nombre_pozo, profundidad_md_ft=md, tipo_pozo=tipo)
        db.add(nuevo)
        db.commit()
        db.close()
        st.rerun()

    st.markdown("---")
    st.subheader("📦 Niveles de Stock Real")
    db_s = SessionLocal()
    for s in db_s.query(AlmacenMendoza).all():
        st.metric(label=s.item_nombre, value=f"{s.stock_actual:,.1f} {s.unidad}")
    db_s.close()

# --- PANEL PRINCIPAL: OPERACIONES ---
tab_cem, tab_est, tab_aba, tab_aud = st.tabs(["🧪 Cementación", "⚡ Estimulación", "🛑 Abandono", "📊 Auditoría"])

with tab_cem:
    st.subheader("🧪 Ingeniería de Cementación Primaria — API RP 65-2")
    col1, col2 = st.columns(2)
    with col1:
        id_pozo = st.number_input("Diámetro Pozo (in)", value=8.5)
        od_casing = st.number_input("OD Casing (in)", value=7.0)
        longitud = st.number_input("Longitud (ft)", value=1000.0)
        rend = st.number_input("Rendimiento (ft³/saco)", value=1.18)
    
    if st.button("Ejecutar Protocolo API"):
        vol = CementCalculator.calcular_volumen_espacio_anular(od_casing, id_pozo, longitud)
        sacos = math.ceil(CementCalculator.calcular_requerimiento_sacos(vol, rend))
        
        db = SessionLocal()
        # Aquí usamos el servicio que ya programaste
        PumpingService.verificar_y_descontar_stock(db, sacos, 0, nombre_pozo)
        nueva = Intervencion(pozo_id=1, tipo_servicio="CEMENTACION", volumen_teorico_bbl=vol)
        db.add(nueva)
        db.commit()
        db.close()
        st.success(f"Operación finalizada: {vol:.2f} bbl calculados y descontados de stock.")

with tab_aud:
    st.subheader("📊 Historial de Auditoría (ERP)")
    db_a = SessionLocal()
    movs = db_a.query(HistorialAlmacen).all()
    # Listado para auditoría
    st.table([{"Fecha": m.fecha, "Insumo": m.item_id, "Tipo": m.tipo_movimiento, "Cant": m.cantidad} for m in movs])
    db_a.close()
