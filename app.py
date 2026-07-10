# app.py
import os
import sys
import streamlit as st

# --- CONFIGURACIÓN DE ENTORNO PARA PRODUCCIÓN (STREAMLIT CLOUD) ---
directorio_raiz = os.path.dirname(os.path.abspath(__file__))
if directorio_raiz not in sys.path:
    sys.path.append(directorio_raiz)
# ------------------------------------------------------------------

import math
from src.database.connection import engine, Base, SessionLocal
from src.modules.operations.models import Pozo, Intervencion, AlmacenMendoza
from src.modules.pumping.calculator import CementCalculator
from src.modules.pumping.services import PumpingService

Base.metadata.create_all(bind=engine)

# Inicializamos Almacén con stock base si es una base de datos nueva
db_init = SessionLocal()
PumpingService.inicializar_almacen_si_vacio(db_init)
db_init.close()

st.set_page_config(
    page_title="Jota Energy - Operaciones",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
    <style>
    .titulo-corporativo { color: #1E7373; font-weight: bold; }
    .stButton>button { background-color: #1E7373; color: white; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="titulo-corporativo">⚡ Jota Energy — Módulo de Ingeniería</h1>', unsafe_allow_html=True)

# --- SIDEBAR: GESTIÓN DE POZOS Y ALMACÉN ---
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

# --- SIDEBAR INTERFAZ: MONITOREO DE INVENTARIO REAL ---
st.sidebar.markdown("---")
st.sidebar.header("📦 Inventario - Base Mendoza")

db_alm = SessionLocal()
items_inventario = db_alm.query(AlmacenMendoza).all()

for item in items_inventario:
    if item.stock_actual <= item.stock_minimo_alerta:
        st.sidebar.error(f"🚨 **{item.item_nombre}**: {item.stock_actual:,.1f} {item.unidad} (BAJO MÍNIMO)")
    else:
        st.sidebar.success(f"✔️ **{item.item_nombre}**: {item.stock_actual:,.1f} {item.unidad}")

# Formulario para reponer o ingresar stock físico
with st.sidebar.expander("🔄 Reponer Stock / Entrada de Insumos"):
    item_a_reponer = st.selectbox("Seleccionar Ítem", items_inventario, format_func=lambda x: x.item_nombre)
    cantidad_refill = st.number_input("Cantidad a Ingresar", min_value=0.0, value=100.0, step=10.0)
    if st.button("Confirmar Entrada de Almacén"):
        item_db = db_alm.query(AlmacenMendoza).filter(AlmacenMendoza.id == item_a_reponer.id).first()
        if item_db:
            item_db.stock_actual += cantidad_refill
            db_alm.commit()
            st.sidebar.info(f"Ingresados {cantidad_refill} {item_db.unidad} a {item_db.item_nombre}.")
            db_alm.close()
            st.rerun()
db_alm.close()


# --- PANEL CENTRAL: MULTISERVICIO ---
tab_cementacion, tab_estimulacion, tab_abandono = st.tabs([
    "🧪 Cementación de Pozos", 
    "⚡ Estimulación y Fractura", 
    "🛑 Abandono de Pozos (P&A)"
])

db = SessionLocal()
pozos_disponibles = db.query(Pozo).all()
db.close()

if not pozos_disponibles:
    st.warning("⚠️ Para empezar, registrá al menos un pozo en la barra lateral izquierda.")
else:
    # =====================================================================
    # VISTA 1: CEMENTACIÓN (CON DESCUENTO REAL DE STOCK)
    # =====================================================================
    with tab_cementacion:
        st.subheader("🧪 Ingeniería de Cementación e Intervención en Campo")
        
        st.markdown("### 🛑 Checklist de Seguridad Pre-Bombeo (Obligatorio)")
        col_hse1, col_hse2, col_hse3 = st.columns(3)
        with col_hse1: chk_lineas = st.checkbox("Prueba de presión de líneas aprobada (1.2x máx)")
        with col_hse2: chk_valvulas = st.checkbox("Válvulas de alivio mecánicas calibradas")
        with col_hse3: chk_zona = st.checkbox("Zona de peligro delimitada (Exclusión de personal)")

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📋 Parámetros de Diseño y Monitoreo")
            pozo_sel = st.selectbox("Seleccionar Pozo Target", pozos_disponibles, format_func=lambda x: x.nombre_pozo, key="cem_pozo")
            ingeniero = st.text_input("Ingeniero de Operaciones a Cargo", key="cem_ing")
            
            id_pozo = st.number_input("Diámetro del Pozo / Open Hole (pulgadas)", min_value=1.0, value=8.5, step=0.1)
            od_casing = st.number_input("Diámetro Externo del Casing (pulgadas)", min_value=1.0, value=7.0, step=0.1)
            longitud = st.number_input("Longitud del intervalo a cementar (ft)", min_value=0.0, value=1000.0, step=100.0)
            
            rendimiento = st.number_input("Rendimiento del Cemento (ft³/saco)", min_value=0.5, value=1.18, step=0.01)
            agua_req = st.number_input("Agua Requerida (gal/saco)", min_value=0.0, value=5.2, step=0.1)
            dosis_retardador = st.number_input("Dosis de Aditivo/Retardador (GPS)", min_value=0.0, value=0.05, step=0.01)

            presion_operativa = st.number_input("Presión Máxima Registrada (psi)", min_value=0.0, value=2500.0)
            caudal_real = st.number_input("Caudal Promedio de Bombeo (bpm)", min_value=0.0, value=4.5)
            vol_real_bbl = st.number_input("Volumen Real Bombeado (bbl)", min_value=0.0, value=120.0)

        with col2:
            st.subheader("📊 Análisis, Logística y Cierre")
            if st.button("Validar HSE, Calcular y Guardar Servicio", key="btn_cem"):
                if not ingeniero:
                    st.error("⚠️ Ingrese el nombre del ingeniero a cargo.")
                elif not (chk_lineas and chk_valvulas and chk_zona):
                    st.error("❌ RECHAZADO: Complete el Checklist HSE de seguridad.")
                else:
                    vol_anular_bbl = CementCalculator.calcular_volumen_espacio_anular(od_casing, id_pozo, longitud)
                    sacos_totales = math.ceil(CementCalculator.calcular_requerimiento_sacos(vol_anular_bbl, rendimiento))
                    agua_total_bbl = CementCalculator.calcular_agua_mezcla(sacos_totales, agua_req)
                    aditivo_total_gal = CementCalculator.calcular_aditivo_liquido(sacos_totales, dosis_retardador)
                    
                    # EJECUCIÓN LOGÍSTICA REAL DE STOCK
                    db_log = SessionLocal()
                    info_stock = PumpingService.verificar_y_descontar_stock(db_log, sacos_totales, aditivo_total_gal)
                    
                    if info_stock["status"] == "ERROR":
                        st.error(info_stock["msg"])
                        db_log.close()
                    else:
                        st.success("🔒 Protocolo HSE Verificado Exitosamente.")
                        st.success(f"📦 {info_stock['msg']}")
                        
                        # Mostrar advertencias de reorden si las hay
                        for alerta in info_stock["alertas"]:
                            st.warning(alerta)
                        
                        # Guardado de la intervención en el histórico
                        nueva_int = Intervencion(
                            pozo_id=pozo_sel.id, tipo_servicio="CEMENTACION", ingeniero_a_cargo=ingeniero,
                            volumen_teorico_bbl=vol_anular_bbl, volumen_real_bbl=vol_real_bbl,
                            presion_max_psi=presion_operativa, caudal_promedio_bpm=caudal_real,
                            checklist_presion_lineas=chk_lineas, checklist_valvulas_alivio=chk_valvulas, checklist_zona_exclusion=chk_zona,
                            estado="FINALIZADO"
                        )
                        db_log.add(nueva_int)
                        db_log.commit()
                        
                        resumen = f"Diseño: {vol_anular_bbl} bbl. Real: {vol_real_bbl} bbl. Consumidos {sacos_totales} Sks."
                        PumpingService.registrar_diseno_cementacion(db_log, nueva_int.id, resumen)
                        
                        # Generación Comercial del PDF
                        pdf_data = PumpingService.generar_pdf_post_job(nueva_int, pozo_sel.nombre_pozo, sacos_totales, aditivo_total_gal)
                        db_log.close()
                        
                        st.metric(label="Desvío de Volumen", value=f"{round(vol_real_bbl - vol_anular_bbl, 2)} bbl")
                        st.download_button(
                            label="📥 Descargar Post-Job Report (PDF Cliente)",
                            data=pdf_data,
                            file_name=f"PostJob_Cementacion_{pozo_sel.nombre_pozo}.pdf",
                            mime="application/pdf"
                        )
                        # Forzar refresco de interfaz para actualizar cantidades del sidebar
                        st.rerun()

    # =====================================================================
    # VISTA 2: ESTIMULACIÓN Y FRACTURA
    # =====================================================================
    with tab_estimulacion:
        st.subheader("⚡ Estimulación y Fractura Hidráulica")
        col_frac1, col_frac2 = st.columns(2)
        
        with col_frac1:
            pozo_frac = st.selectbox("Seleccionar Pozo Target", pozos_disponibles, format_func=lambda x: x.nombre_pozo, key="frac_pozo")
            etapas = st.number_input("Número de Etapas de Fractura", min_value=1, value=4, step=1)
            tipo_gel = st.selectbox("Fluido Portador / Sistema de Gel", ["Slickwater", "Gel Lineal", "Gel Reticulado (Crosslinked)"])
            proppant_lbs = st.number_input("Diseño de Apuntalante Total por Etapa (lbs)", min_value=0.0, value=50000.0, step=5000.0)
        
        with col_frac2:
            st.subheader("📊 Resumen del Plan de Inyección")
            total_proppant_proyecto = etapas * proppant_lbs
            st.info(f"Concentración estimada para el sistema: **{tipo_gel}**")
            st.metric("Total Arena/Apuntalante Necesario", f"{total_proppant_proyecto:,.2f} lbs")
            
            if st.button("Guardar Diseño de Fractura"):
                st.success(f"✅ Diseño de estimulación pre-guardado exitosamente para el pozo {pozo_frac.nombre_pozo}.")

    # =====================================================================
    # VISTA 3: ABANDONO DE POZOS
    # =====================================================================
    with tab_abandono:
        st.subheader("🛑 Abandono de Pozos (P&A - Plug and Abandon)")
        st.markdown("##### Verificación de Protocolos de Aislamiento y Hermeticidad")
        
        col_pa1, col_pa2 = st.columns(2)
        with col_pa1:
            pozo_pa = st.selectbox("Seleccionar Pozo Target", pozos_disponibles, format_func=lambda x: x.nombre_pozo, key="pa_pozo")
            prof_tapón = st.number_input("Profundidad del Tapón de Cemento (Top of Cement - ft)", min_value=0.0, value=3000.0)
            long_tapon = st.number_input("Longitud Mínima Requerida del Tapón (ft)", min_value=100.0, value=200.0)
            prueba_hermeticidad = chk_zona = st.checkbox("Prueba de Presión / Hermeticidad de Tapón Mecánico Aprobada")
            
        with col_pa2:
            st.subheader("📋 Verificación Normativa")
            if prueba_hermeticidad:
                st.success("✔️ Requisito de Hermeticidad Estructural Cubierto.")
            else:
                st.warning("⚠️ Falta realizar la prueba de presión en el tapón para validación regulatoria.")
                
            if st.button("Registrar Protocolo P&A"):
                if not prueba_hermeticidad:
                    st.error("No se puede cerrar el protocolo sin registrar la prueba de hermeticidad aprobada.")
                else:
                    st.success(f"✅ Protocolo de aislamiento e inyección de tapón para {pozo_pa.nombre_pozo} registrado correctamente.")
