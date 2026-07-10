# app.py
import os
import sys
import streamlit as st

directorio_raiz = os.path.dirname(os.path.abspath(__file__))
if directorio_raiz not in sys.path:
    sys.path.append(directorio_raiz)

import math
from src.database.connection import engine, Base, SessionLocal
from src.modules.operations.models import Pozo, Intervencion, AlmacenMendoza, HistorialAlmacen
from src.modules.pumping.calculator import CementCalculator
from src.modules.pumping.services import PumpingService

Base.metadata.create_all(bind=engine)

db_init = SessionLocal()
PumpingService.inicializar_almacen_si_vacio(db_init)
db_init.close()

st.set_page_config(page_title="Jota Energy - Operaciones", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .titulo-corporativo { color: #1E7373; font-weight: bold; }
    .stButton>button { background-color: #1E7373; color: white; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="titulo-corporativo">⚡ Jota Energy — Módulo de Ingeniería</h1>', unsafe_allow_html=True)

# --- SIDEBAR: ASSETS & INVENTARIO ---
st.sidebar.header("🛠️ Administración de Activos")
with st.sidebar.form("form_pozo"):
    nombre_pozo = st.text_input("Nombre del Pozo (Ej: PM-1024)")
    profundidad = st.number_input("Profundidad MD (ft)", min_value=0.0, value=5000.0, step=500.0)
    tipo = st.selectbox("Tipo de Pozo", ["Vertical", "Dirigido", "Horizontal"])
    btn_pozo = st.form_submit_button("Registrar Pozo")
    if btn_pozo and nombre_pozo:
        db = SessionLocal()
        try:
            db.add(Pozo(nombre_pozo=nombre_pozo, profundidad_md_ft=profundidad, tipo_pozo=tipo))
            db.commit()
            st.sidebar.success(f"Pozo {nombre_pozo} guardado con éxito.")
        except Exception:
            db.rollback()
            st.sidebar.error("El pozo ya existe.")
        finally:
            db.close()

st.sidebar.markdown("---")
st.sidebar.header("📦 Inventario - Base Mendoza")
db_alm = SessionLocal()
items_inventario = db_alm.query(AlmacenMendoza).all()

for item in items_inventario:
    if item.stock_actual <= item.stock_minimo_alerta:
        st.sidebar.error(f"🚨 **{item.item_nombre}**: {item.stock_actual:,.1f} {item.unidad} (CRÍTICO)")
    else:
        st.sidebar.success(f"✔️ **{item.item_nombre}**: {item.stock_actual:,.1f} {item.unidad}")

with st.sidebar.expander("🔄 Reponer Entrada de Insumos"):
    item_a_reponer = st.selectbox("Seleccionar Ítem", items_inventario, format_func=lambda x: x.item_nombre)
    cantidad_refill = st.number_input("Cantidad", min_value=0.0, value=100.0)
    if st.button("Confirmar Entrada"):
        item_db = db_alm.query(AlmacenMendoza).filter(AlmacenMendoza.id == item_a_reponer.id).first()
        if item_db:
            item_db.stock_actual += cantidad_refill
            PumpingService.registrar_movimiento_almacen(db_alm, item_db.id, "INGRESO", cantidad_refill, "Entrada por Compra Corporativa")
            db_alm.commit()
            db_alm.close()
            st.rerun()
db_alm.close()

# --- TABS DE OPERACIONES ---
tab_cementacion, tab_estimulacion, tab_abandono, tab_auditoria = st.tabs([
    "🧪 Cementación de Pozos", "⚡ Estimulación y Fractura", "🛑 Abandono de Pozos (P&A)", "📊 Auditoría de Suministros (ERP)"
])

db = SessionLocal()
pozos_disponibles = db.query(Pozo).all()
db.close()

if not pozos_disponibles:
    st.warning("⚠️ Registrá un pozo en la barra lateral para activar los paneles de ingeniería.")
else:
    with tab_cementacion:
        st.subheader("🧪 Ingeniería de Cementación")
        st.markdown("### 🛑 Checklist de Seguridad Pre-Bombeo (Obligatorio)")
        col_hse1, col_hse2, col_hse3 = st.columns(3)
        with col_hse1: chk_lineas = st.checkbox("Prueba de presión de líneas aprobada (1.2x máx)")
        with col_hse2: chk_valvulas = st.checkbox("Válvulas de alivio mecánicas calibradas")
        with col_hse3: chk_zona = st.checkbox("Zona de peligro delimitada (Exclusión)")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            pozo_sel = st.selectbox("Seleccionar Pozo Target", pozos_disponibles, format_func=lambda x: x.nombre_pozo)
            ingeniero = st.text_input("Ingeniero de Operaciones a Cargo")
            id_pozo = st.number_input("Diámetro del Pozo (in)", min_value=1.0, value=8.5)
            od_casing = st.number_input("Diámetro Externo Casing (in)", min_value=1.0, value=7.0)
            longitud = st.number_input("Longitud del intervalo (ft)", min_value=0.0, value=1000.0)
            rendimiento = st.number_input("Rendimiento Cemento (ft³/saco)", min_value=0.5, value=1.18)
            agua_req = st.number_input("Agua Requerida (gal/saco)", min_value=0.0, value=5.2)
            dosis_retardador = st.number_input("Dosis Retardador (GPS)", min_value=0.0, value=0.05)
            presion_operativa = st.number_input("Presión Máxima Registrada (psi)", min_value=0.0, value=2500.0)
            caudal_real = st.number_input("Caudal Promedio (bpm)", min_value=0.0, value=4.5)
            vol_real_bbl = st.number_input("Volumen Real Bombeado (bbl)", min_value=0.0, value=120.0)

        with col2:
            st.subheader("📊 Análisis, Logística y Cierre")
            if st.button("Validar HSE, Calcular y Guardar Servicio"):
                if not ingeniero:
                    st.error("⚠️ Ingrese el ingeniero a cargo.")
                elif not (chk_lineas and chk_valvulas and chk_zona):
                    st.error("❌ RECHAZADO: Incumplimiento de Protocolos HSE.")
                else:
                    vol_anular_bbl = CementCalculator.calcular_volumen_espacio_anular(od_casing, id_pozo, longitud)
                    sacos_totales = math.ceil(CementCalculator.calcular_requerimiento_sacos(vol_anular_bbl, rendimiento))
                    aditivo_total_gal = CementCalculator.calcular_aditivo_liquido(sacos_totales, dosis_retardador)
                    
                    db_log = SessionLocal()
                    info_stock = PumpingService.verificar_y_descontar_stock(db_log, sacos_totales, aditivo_total_gal, pozo_sel.nombre_pozo)
                    
                    if info_stock["status"] == "ERROR":
                        st.error(info_stock["msg"])
                        db_log.close()
                    else:
                        st.success("🔒 Protocolo HSE Verificado Exitosamente.")
                        st.success(f"📦 {info_stock['msg']}")
                        for alerta in info_stock["alertas"]:
                            st.warning(alerta)
                        
                        nueva_int = Intervencion(
                            pozo_id=pozo_sel.id, tipo_servicio="CEMENTACION", ingeniero_a_cargo=ingeniero,
                            volumen_teorico_bbl=vol_anular_bbl, volumen_real_bbl=vol_real_bbl,
                            presion_max_psi=presion_operativa, caudal_promedio_bpm=caudal_real,
                            checklist_presion_lineas=chk_lineas, checklist_valvulas_alivio=chk_valvulas, checklist_zona_exclusion=chk_zona,
                            estado="FINALIZADO"
                        )
                        db_log.add(nueva_int)
                        db_log.commit()
                        
                        PumpingService.registrar_diseno_cementacion(db_log, nueva_int.id, f"Consumo {sacos_totales} Sks.")
                        pdf_data = PumpingService.generar_pdf_post_job(nueva_int, pozo_sel.nombre_pozo, sacos_totales, aditivo_total_gal)
                        db_log.close()
                        
                        st.metric(label="Desvío de Volumen", value=f"{round(vol_real_bbl - vol_anular_bbl, 2)} bbl")
                        st.download_button(label="📥 Descargar Post-Job Report (PDF)", data=pdf_data, file_name=f"PostJob_{pozo_sel.nombre_pozo}.pdf", mime="application/pdf")
                        st.rerun()

    with tab_estimulacion:
        st.subheader("⚡ Estimulación y Fractura Hidráulica")
        col_frac1, col_frac2 = st.columns(2)
        with col_frac1:
            pozo_frac = st.selectbox("Seleccionar Pozo Target", pozos_disponibles, format_func=lambda x: x.nombre_pozo, key="f_p")
            etapas = st.number_input("Etapas de Fractura", min_value=1, value=4)
            tipo_gel = st.selectbox("Fluido Portador", ["Slickwater", "Gel Lineal", "Gel Reticulado"])
            proppant_lbs = st.number_input("Apuntalante por Etapa (lbs)", min_value=0.0, value=50000.0)
        with col_frac2:
            st.metric("Total Apuntalante Requerido", f"{etapas * proppant_lbs:,.2f} lbs")
            if st.button("Guardar Diseño de Fractura"):
                st.success("✅ Estructura pre-guardada.")

    with tab_abandono:
        st.subheader("🛑 Abandono de Pozos (P&A)")
        pozo_pa = st.selectbox("Seleccionar Pozo Target", pozos_disponibles, format_func=lambda x: x.nombre_pozo, key="p_a")
        prueba_hermeticidad = st.checkbox("Prueba de Hermeticidad Estructural Aprobada")
        if st.button("Registrar Protocolo P&A"):
            if not prueba_hermeticidad:
                st.error("Rechazado por normativa: Requiere aprobación de hermeticidad.")
            else:
                st.success("✅ Protocolo de aislamiento definitivo asentado.")

    with tab_auditoria:
        st.subheader("📊 Control Patrimonial e Historial de Movimientos — Kardex")
        db_audit = SessionLocal()
        movimientos = db_audit.query(HistorialAlmacen, AlmacenMendoza).join(AlmacenMendoza, HistorialAlmacen.item_id == AlmacenMendoza.id).order_by(HistorialAlmacen.fecha.desc()).all()
        if not movimientos:
            st.info("No hay transacciones registradas.")
        else:
            st.dataframe([{
                "Fecha": m.fecha.strftime("%Y-%m-%d %H:%M:%S"), "Insumo": i.item_nombre,
                "Tipo": m.tipo_movimiento, "Cantidad": f"{m.cantidad:,.1f} {i.unidad}", "Referencia": m.referencia
            } for m, i in movimientos], use_container_width=True)
        db_audit.close()
