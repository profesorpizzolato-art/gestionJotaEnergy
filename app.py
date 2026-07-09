# app.py
import os
import sys
import streamlit as st

# --- CONFIGURACIÓN DE ENTORNO PARA PRODUCCIÓN (STREAMLIT CLOUD) ---
# Forzamos la inclusión de la raíz para resolver módulos absolutos 'src.*'
directorio_raiz = os.path.dirname(os.path.abspath(__file__))
if directorio_raiz not in sys.path:
    sys.path.append(directorio_raiz)
# ------------------------------------------------------------------

import math
# Importaciones absolutas consistentes con la estructura del repositorio
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
            st.sidebar.error("El pozo ya se encuentra registrado o hubo un error.")
        finally:
            db.close()

# --- PANEL CENTRAL: NAVEGACIÓN MULTISERVICIO ---
tab_cementacion, tab_estimulacion, tab_abandono = st.tabs([
    "🧪 Cementación de Pozos", 
    "⚡ Estimulación y Fractura", 
    "🛑 Abandono de Pozos (P&A)"
])

# =====================================================================
# VISTA 1: CEMENTACIÓN (Módulo Operativo + HSE)
# =====================================================================
with tab_cementacion:
    st.subheader("🧪 Ingeniería de Cementación e Intervención en Campo")

    db = SessionLocal()
    pozos_disponibles = db.query(Pozo).all()
    db.close()

    if not pozos_disponibles:
        st.warning("⚠️ Para empezar, registrá al menos un pozo en la barra lateral izquierda.")
    else:
        # --- SUB-MÓDULO: SEGURIDAD (HSE PRE-BOMBEO) ---
        st.markdown("### 🛑 Checklist de Seguridad Pre-Bombeo (Obligatorio)")
        col_hse1, col_hse2, col_hse3 = st.columns(3)
        
        with col_hse1:
            chk_lineas = st.checkbox("Prueba de presión de líneas aprobada (1.2x presión máxima)")
        with col_hse2:
            chk_valvulas = st.checkbox("Válvulas de alivio mecánicas calibradas y verificadas")
        with col_hse3:
            chk_zona = st.checkbox("Zona de peligro delimitada (Exclusión de personal no esencial)")

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📋 Parámetros de Diseño y Monitoreo")
            pozo_sel = st.selectbox("Seleccionar Pozo Target", pozos_disponibles, format_func=lambda x: x.nombre_pozo)
            ingeniero = st.text_input("Ingeniero de Operaciones a Cargo")
            
            st.markdown("##### Variables de Geometría")
            id_pozo = st.number_input("Diámetro del Pozo / Open Hole (pulgadas)", min_value=1.0, value=8.5, step=0.1)
            od_casing = st.number_input("Diámetro Externo del Casing (pulgadas)", min_value=1.0, value=7.0, step=0.1)
            longitud = st.number_input("Longitud del intervalo a cementar (ft)", min_value=0.0, value=1000.0, step=100.0)
            
            st.markdown("##### Variables de Mezcla (Diseño)")
            rendimiento = st.number_input("Rendimiento del Cemento (ft³/saco)", min_value=0.5, value=1.18, step=0.01)
            agua_req = st.number_input("Agua Requerida (gal/saco)", min_value=0.0, value=5.2, step=0.1)
            dosis_retardador = st.number_input("Dosis de Aditivo/Retardador (GPS)", min_value=0.0, value=0.05, step=0.01)

            st.markdown("##### 📈 Captura en Tiempo Real (Datos Reales de Campo)")
            presion_operativa = st.number_input("Presión Máxima Registrada (psi)", min_value=0.0, value=2500.0)
            caudal_real = st.number_input("Caudal Promedio de Bombeo (bpm)", min_value=0.0, value=4.5)
            vol_real_bbl = st.number_input("Volumen Real Bombeado (bbl)", min_value=0.0, value=120.0)

        with col2:
            st.subheader("📊 Resultados, Desvíos y Cierre de OT")
            
            if st.button("Validar HSE, Calcular y Guardar Servicio"):
                if not ingeniero:
                    st.error("⚠️ Por favor, ingresá el nombre del ingeniero a cargo antes de guardar.")
                elif not (chk_lineas and chk_valvulas and chk_zona):
                    st.error("❌ RECHAZADO: No se puede registrar la operación si no se aprueban todos los puntos del Checklist HSE.")
                else:
                    try:
                        # 1. Ejecutar cálculos de diseño
                        vol_anular_bbl = CementCalculator.calcular_volumen_espacio_anular(od_casing, id_pozo, longitud)
                        sacos_totales = CementCalculator.calcular_requerimiento_sacos(vol_anular_bbl, rendimiento)
                        agua_total_bbl = CementCalculator.calcular_agua_mezcla(sacos_totales, agua_req)
                        aditivo_total_gal = CementCalculator.calcular_aditivo_liquido(sacos_totales, dosis_retardador)
                        
                        st.success("🔒 Protocolo HSE Verificado Exitosamente.")
                        
                        # 2. Mostrar métricas comparativas (Diseño vs Real)
                        m1, m2 = st.columns(2)
                        with m1:
                            st.metric(label="Volumen de Diseño (Teórico)", value=f"{vol_anular_bbl} bbl")
                            st.metric(label="Cantidad de Sacos Calculados", value=f"{sacos_totales} Sks")
                            st.metric(label="Agua de Mezcla Necesaria", value=f"{agua_total_bbl} bbl")
                            st.metric(label="Aditivo Líquido Necesario", value=f"{aditivo_total_gal} gal")
                        with m2:
                            st.metric(label="Volumen Real Bombeado", value=f"{vol_real_bbl} bbl")
                            desvio = round(vol_real_bbl - vol_anular_bbl, 2)
                            st.metric(label="Desvío Operativo", value=f"{desvio} bbl", delta=f"{desvio} bbl vs Diseño")
                            st.metric(label="Presión Máxima de Línea", value=f"{presion_operativa} psi")
                            st.metric(label="Caudal de Trabajo", value=f"{caudal_real} bpm")
                        
                        # 3. Persistir en la Base de Datos con el nuevo modelo expandido
                        db = SessionLocal()
                        nueva_intervencion = Intervencion(
                            pozo_id=pozo_sel.id,
                            tipo_servicio="CEMENTACION",
                            ingeniero_a_cargo=ingeniero,
                            volumen_teorico_bbl=vol_anular_bbl,
                            volumen_real_bbl=vol_real_bbl,
                            presion_max_psi=presion_operativa,
                            caudal_promedio_bpm=caudal_real,
                            checklist_presion_lineas=chk_lineas,
                            checklist_valvulas_alivio=chk_valvulas,
                            checklist_zona_exclusion=chk_zona,
                            estado="FINALIZADO"
                        )
                        db.add(nueva_intervencion)
                        db.commit()
                        
                        # Guardar resumen en texto plano
                        resumen_texto = f"Diseño: {vol_anular_bbl} bbl lechada, {sacos_totales} Sks. Real: {vol_real_bbl} bbl bombeados a {presion_operativa} psi."
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
