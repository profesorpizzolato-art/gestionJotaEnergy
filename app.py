# app.py
import os
import sys
import streamlit as st

# --- BLINDAJE DE RUTAS PARA ENTORNO DE PRODUCCIÓN (STREAMLIT CLOUD) ---
# Agrega tanto la raíz del proyecto como la carpeta 'src' al path de Python para evitar fallos de importación
ruta_raiz = os.path.abspath(os.path.dirname(__file__))
ruta_src = os.path.join(ruta_raiz, "src")

if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)
if ruta_src not in sys.path:
    sys.path.append(ruta_src)
# -----------------------------------------------------------------------

import math
# SOLUCIÓN DE RAÍZ: Usamos importaciones absolutas apoyadas por el ajuste de path superior
from src.database.connection import engine, Base, SessionLocal
from src.modules.operations.models import Pozo, Intervencion
from src.modules.pumping.calculator import CementCalculator
from src.modules.pumping.services import PumpingService

# Crear las tablas automáticamente si no existen (SQLite local o Postgres)
Base.metadata.create_all(bind=engine)

st.set_page_config(
    page_title="Jota Energy - Operaciones",
    page_icon="⚡",
    layout="wide"
)

# Estilo corporativo con el verde azulado (#1E7373)
st.markdown("""
    <style>
    .titulo-corporativo { color: #1E7373; font-weight: bold; }
    .stButton>button { background-color: #1E7373; color: white; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="titulo-corporativo">⚡ Jota Energy — Módulo de Ingeniería</h1>', unsafe_allow_html=True)

# --- SIDEBAR: GESTIÓN DE POZOS ---
st.sidebar.header("🛠️ Administración de Activos")
with st.sidebar.form("form_pozo"):
    nombre_pozo = st.text_input("Nombre del Pozo (Ej: PM-1024)")
    profundidad = st.number_input("Profundidad MD (ft)", min_value=0.0, value=5000.0, step=500.0)
    tipo = st.selectbox("Tipo de Pozo", ["Vertical", "Dirigido", "Horizontal"])
    btn_pozo = st.form_submit_button("Registrar Pozo")
    
    if btn_pozo and nombre_pozo:
        db = SessionLocal()
        nuevo_pozo = Pozo(nombre_pozo=nombre_pozo, profundidad_md_ft=profundidad, tipo_pozo=tipo)
        try:
            db.add(nuevo_pozo)
            db.commit()
            st.sidebar.success(f"Pozo {nombre_pozo} guardado con éxito.")
        except Exception:
            db.rollback()
            st.sidebar.error("El pozo ya se encuentra registrado.")
        finally:
            db.close()

# --- PANEL CENTRAL: NAVEGACIÓN MULTISERVICIO ---
tab_cementacion, tab_estimulacion, tab_abandono = st.tabs([
    "🧪 Cementación de Pozos", 
    "⚡ Estimulación y Fractura", 
    "🛑 Abandono de Pozos (P&A)"
])

# =====================================================================
# VISTA 1: CEMENTACIÓN
# =====================================================================
with tab_cementacion:
    st.subheader("Cálculo y Registro de Diseño de Cementación")

    db = SessionLocal()
    pozos_disponibles = db.query(Pozo).all()
    db.close()

    if not pozos_disponibles:
        st.warning("⚠️ Para empezar, registrá al menos un pozo en la barra lateral izquierda.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📋 Parámetros de la Operación")
            pozo_sel = st.selectbox("Seleccionar Pozo Target", pozos_disponibles, format_func=lambda x: x.nombre_pozo)
            ingeniero = st.text_input("Ingeniero de Operaciones a Cargo")
            
            st.markdown("---")
            id_pozo = st.number_input("Diámetro del Pozo / Open Hole (pulgadas)", min_value=1.0, value=8.5, step=0.1)
            od_casing = st.number_input("Diámetro Externo del Casing (pulgadas)", min_value=1.0, value=7.0, step=0.1)
            longitud = st.number_input("Longitud del intervalo a cementar (ft)", min_value=0.0, value=1000.0, step=100.0)
            
            st.markdown("---")
            st.subheader("🧪 Propiedades de la Mezcla")
            rendimiento = st.number_input("Rendimiento del Cemento (ft³/saco)", min_value=0.5, value=1.18, step=0.01)
            agua_req = st.number_input("Agua Requerida (gal/saco)", min_value=0.0, value=5.2, step=0.1)
            dosis_retardador = st.number_input("Dosis de Aditivo/Retardador (GPS)", min_value=0.0, value=0.05, step=0.01)

        with col2:
            st.subheader("📊 Resultados del Diseño")
            
            if st.button("Calcular y Guardar en Base de Datos"):
                if not ingeniero:
                    st.error("⚠️ Por favor, ingresá el nombre del ingeniero a cargo antes de guardar.")
                else:
                    try:
                        # 1. Ejecutar cálculos
                        vol_anular_bbl = CementCalculator.calcular_volumen_espacio_anular(od_casing, id_pozo, longitud)
                        sacos_totales = CementCalculator.calcular_requerimiento_sacos(vol_anular_bbl, rendimiento)
                        agua_total_bbl = CementCalculator.calcular_agua_mezcla(sacos_totales, agua_req)
                        aditivo_total_gal = CementCalculator.calcular_aditivo_liquido(sacos_totales, dosis_retardador)
                        
                        # 2. Mostrar en pantalla con formato limpio
                        st.metric(label="Volumen Total de Lechada Requerido", value=f"{vol_anular_bbl} bbl")
                        st.metric(label="Cantidad de Sacos de Cemento", value=f"{sacos_totales} Sks")
                        st.metric(label="Agua de Mezcla Total Requerida", value=f"{agua_total_bbl} bbl")
                        st.metric(label="Aditivo Líquido Necesario", value=f"{aditivo_total_gal} gal")
                        
                        # 3. Persistir en la Base de Datos relacional
                        db = SessionLocal()
                        nueva_intervencion = Intervencion(
                            pozo_id=pozo_sel.id,
                            tipo_servicio="CEMENTACION",
                            ingeniero_a_cargo=ingeniero,
                            estado="FINALIZADO"
                        )
                        db.add(nueva_intervencion)
                        db.commit()
                        
                        # Guardar resumen del cálculo en el campo de texto de la intervención
                        resumen_texto = f"Diseño: {vol_anular_bbl} bbl lechada, {sacos_totales} Sks, {agua_total_bbl} bbl agua, {aditivo_total_gal} gal aditivo."
                        PumpingService.registrar_diseno_cementacion(db, nueva_intervencion.id, resumen_texto)
                        db.close()
                        
                        st.success(f"✅ ¡Operación guardada exitosamente en el histórico para el pozo {pozo_sel.nombre_pozo}!")
                        
                    except Exception as e:
                        st.error(f"Error en los parámetros técnicos: {e}")

# =====================================================================
# VISTA 2: ESTIMULACIÓN Y FRACTURA
# =====================================================================
with tab_estimulacion:
    st.subheader("Simulación de Etapas de Fractura Hidráulica e Inyección de Gel")
    st.info("💡 Módulo listo para recibir la lógica de concentraciones de apuntalante y geles portadores.")

# =====================================================================
# VISTA 3: ABANDONO DE POZOS
# =====================================================================
with tab_abandono:
    st.subheader("Verificación de Protocolos de Aislamiento y Tapones de Cemento (P&A)")
    st.info("💡 Módulo listo para la parametrización de pruebas de hermeticidad y corte de casing.")
