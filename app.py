# app.py
import streamlit as st
import math
from src.modules.pumping.calculator import CementCalculator

# Configuración de página e Identidad Visual
st.set_page_config(
    page_title="Jota Energy - Operaciones",
    page_icon="⚡",
    layout="wide"
)

# Estilo personalizado para usar el verde azulado (#1E7373) en elementos clave
st.markdown(f"""
    <style>
    .titulo-corporativo {{
        color: #1E7373;
        font-weight: bold;
    }}
    .stButton>button {{
        background-color: #1E7373;
        color: white;
        border-radius: 5px;
    }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="titulo-corporativo">⚡ Jota Energy — Módulo de Ingeniería</h1>', unsafe_allow_html=True)
st.subheader("Cálculo de Diseño de Lechada de Cementación")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Parámetros del Pozo y Cañería")
    id_pozo = st.number_input("Diámetro del Pozo / Open Hole (pulgadas)", min_value=1.0, value=8.5, step=0.1)
    od_casing = st.number_input("Diámetro Externo del Casing (pulgadas)", min_value=1.0, value=7.0, step=0.1)
    longitud = st.number_input("Longitud del intervalo a cementar (ft)", min_value=0.0, value=1000.0, step=100.0)
    
    st.markdown("---")
    st.subheader("🧪 Propiedades de la Mezcla")
    rendimiento = st.number_input("Rendimiento del Cemento (ft³/saco)", min_value=0.5, value=1.18, step=0.01)

with col2:
    st.subheader("📊 Resultados del Diseño")
    
    if st.button("Calcular Volúmenes e Insumos"):
        try:
            # Ejecutar cálculos del motor
            vol_anular_bbl = CementCalculator.calcular_volumen_espacio_anular(od_casing, id_pozo, longitud)
            sacos_totales = CementCalculator.calcular_requerimiento_sacos(vol_anular_bbl, rendimiento)
            
            # Mostrar resultados usando tarjetas visuales (KPIs)
            st.metric(label="Volumen Total de Lechada Requerido", value=f"{vol_anular_bbl} bbl")
            st.metric(label="Cantidad de Sacos de Cemento", value=f"{sacos_totales} Sks")
            
            st.success("✅ Cálculos realizados bajo estándares API de cementación.")
            
        except Exception as e:
            st.error(f"Error en los parámetros: {e}")
