# app.py (Sección de Pestañas Operativas actualizadas)
import os
import sys
import streamlit as st
import math

from src.database.connection import engine, Base, SessionLocal
from src.modules.operations.models import Pozo, Intervencion, AlmacenMendoza, HistorialAlmacen
from src.modules.pumping.calculator import CementCalculator
from src.modules.pumping.services import PumpingService

Base.metadata.create_all(bind=engine)

# ... (Mantené la configuración inicial del Sidebar intacta) ...

tab_cementacion, tab_estimulacion, tab_abandono, tab_auditoria = st.tabs([
    "🧪 Cementación de Pozos", "⚡ Estimulación y Fractura", "🛑 Abandono de Pozos (P&A)", "📊 Auditoría de Suministros (ERP)"
])

db = SessionLocal()
pozos_disponibles = db.query(Pozo).all()
db.close()

if not pozos_disponibles:
    st.warning("⚠️ Registrá un pozo en la barra lateral para activar los paneles de ingeniería.")
else:
    # --- VISTA 1: CEMENTACIÓN ---
    with tab_cementacion:
        st.subheader("🧪 Ingeniería de Cementación Primaria — API RP 65-2")
        st.markdown("##### Verificación de Barreras Hidráulicas e Integridad Estructural")
        
        st.markdown("##### 🛑 Checklist HSE Pre-Bombeo Obligatorio")
        col_hse1, col_hse2, col_hse3 = st.columns(3)
        with col_hse1: chk_lineas = st.checkbox("Prueba de presión de líneas aprobada (1.2x máx)", key="cem_c1")
        with col_hse2: chk_valvulas = st.checkbox("Válvulas de alivio mecánicas (PRV) calibradas", key="cem_c2")
        with col_hse3: chk_zona = st.checkbox("Zona de peligro delimitada (Exclusión de personal)", key="cem_c3")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            pozo_sel = st.selectbox("Seleccionar Pozo Target", pozos_disponibles, format_func=lambda x: x.nombre_pozo, key="sb_cem")
            ingeniero = st.text_input("Ingeniero de Operaciones a Cargo", key="ing_cem")
            id_pozo = st.number_input("Diámetro del Pozo / Open Hole (in)", min_value=1.0, value=8.5)
            od_casing = st.number_input("Diámetro Externo Casing (in)", min_value=1.0, value=7.0)
            longitud = st.number_input("Longitud del intervalo a cementar (ft)", min_value=0.0, value=1000.0)
            rendimiento = st.number_input("Rendimiento del Cemento (ft³/saco)", min_value=0.5, value=1.18)
            agua_req = st.number_input("Agua Requerida (gal/saco)", min_value=0.0, value=5.2)
            dosis_retardador = st.number_input("Dosis Retardador (GPS)", min_value=0.0, value=0.05)
            presion_operativa = st.number_input("Presión Máxima Registrada (psi)", min_value=0.0, value=2500.0)
            caudal_real = st.number_input("Caudal Promedio (bpm)", min_value=0.0, value=4.5)
            vol_real_bbl = st.number_input("Volumen Real Bombeado (bbl)", min_value=0.0, value=120.0)

        with col2:
            st.subheader("📊 Análisis Logístico de Ejecución")
            if st.button("Cerrar Operación y Validar Protocolo API", key="btn_save_cem"):
                if not ingeniero:
                    st.error("⚠️ Ingrese el ingeniero responsable de la firma legal.")
                elif not (chk_lineas and chk_valvulas and chk_zona):
                    st.error("❌ RECHAZADO: Incumplimiento de las Normas de Seguridad Críticas Pre-Bombeo.")
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
                        st.success("🔒 Protocolo HSE Verificado y Aprobado.")
                        st.info(f"📦 {info_stock['msg']}")
                        
                        nueva_int = Intervencion(
                            pozo_id=pozo_sel.id, tipo_servicio="CEMENTACION", ingeniero_a_cargo=ingeniero,
                            volumen_teorico_bbl=vol_anular_bbl, volumen_real_bbl=vol_real_bbl,
                            presion_max_psi=presion_operativa, caudal_promedio_bpm=caudal_real,
                            chk_presion_lineas=True, chk_valvulas_alivio=True, chk_zona_exclusion=True,
                            estado="FINALIZADO"
                        )
                        db_log.add(nueva_int)
                        db_log.commit()
                        db_log.close()
                        st.rerun()

    # --- VISTA 2: ESTIMULACIÓN Y FRACTURA ---
    with tab_estimulacion:
        st.subheader("⚡ Estimulación y Fractura Hidráulica — Control Inyección")
        st.markdown("##### 🛑 Checklist Operativo de Control de Inyección Continua")
        col_f1, col_f2 = st.columns(2)
        with col_f1: chk_f_lineas = st.checkbox("Prueba de Presión de Líneas Certificada (Alta Presión)", key="f_c1")
        with col_f2: chk_f_gel = st.checkbox("Control Químico de Viscosidad y Reticulación Aprobado", key="f_c2")

        st.markdown("---")
        col_frac1, col_frac2 = st.columns(2)
        with col_frac1:
            pozo_frac = st.selectbox("Seleccionar Pozo Target", pozos_disponibles, format_func=lambda x: x.nombre_pozo, key="sb_frac")
            ing_frac = st.text_input("Ingeniero de Fractura Responsable", key="ing_frac")
            etapas = st.number_input("Número de Etapas Planificadas", min_value=1, value=4)
            proppant_lbs = st.number_input("Diseño de Arena/Apuntalante por Etapa (lbs)", min_value=0.0, value=50000.0)
            presion_frac = st.number_input("Presión de Ruptura de Formación (psi)", min_value=0.0, value=5800.0)
            caudal_frac = st.number_input("Caudal de Inyección de Diseño (bpm)", min_value=0.0, value=45.0)

        with col_frac2:
            st.subheader("📊 Monitoreo de Insumos Críticos")
            total_arena_necesaria = etapas * proppant_lbs
            st.metric("Total Arena 20/40 Comprometida", f"{total_arena_necesaria:,.1f} lbs")
            
            if st.button("Ejecutar Bombeo de Fractura e Inyectar"):
                if not ing_frac:
                    st.error("⚠️ Falta asignar el Ingeniero de Fractura.")
                elif not (chk_f_lineas and chk_f_gel):
                    st.error("❌ RECHAZADO: Complete los parámetros regulatorios del fluido y líneas.")
                else:
                    db_frac = SessionLocal()
                    info_arena = PumpingService.verificar_y_descontar_arena(db_frac, total_arena_necesaria, pozo_frac.nombre_pozo)
                    
                    if info_arena["status"] == "ERROR":
                        st.error(info_arena["msg"])
                        db_frac.close()
                    else:
                        nueva_frac = Intervencion(
                            pozo_id=pozo_frac.id, tipo_servicio="FRACTURA", ingeniero_a_cargo=ing_frac,
                            volumen_teorico_bbl=0.0, volumen_real_bbl=0.0,
                            presion_max_psi=presion_frac, caudal_promedio_bpm=caudal_frac,
                            chk_presion_lineas=True, chk_control_gel=True,
                            estado="FINALIZADO"
                        )
                        db_frac.add(nueva_frac)
                        db_frac.commit()
                        db_frac.close()
                        st.success("⚡ Inyección de etapas completada. Consumo de arena registrado.")
                        st.rerun()

    # --- VISTA 3: ABANDONO DE POZOS (P&A) ---
    with tab_abandono:
        st.subheader("🛑 Abandono Definitivo de Pozos (P&A) — Protocolo de Hermeticidad")
        st.markdown("##### 🛑 Verificación Legal de Aislamiento Sustentable")
        
        col_pa_1, col_pa_2 = st.columns(2)
        with col_pa_1: chk_tag = st.checkbox("Verificación Mecánica de Asiento del Tapón (Tag Balance Aprobado)", key="pa_c1")
        with col_pa_2: chk_presion = st.checkbox("Prueba de Presión e Hermeticidad Hidráulica Certificada (1000 psi / 15 min)", key="pa_c2")

        st.markdown("---")
        col_pa1, col_pa2 = st.columns(2)
        with col_pa1:
            pozo_pa = st.selectbox("Seleccionar Pozo Target", pozos_disponibles, format_func=lambda x: x.nombre_pozo, key="sb_pa")
            ing_pa = st.text_input("Supervisor / Inspector Operativo", key="ing_pa")
            prof_tapon = st.number_input("Profundidad del Tope del Cemento (TOC - ft)", min_value=0.0, value=3500.0)
            caida_psi = st.number_input("Caída de Presión en Prueba (psi)", min_value=0.0, value=5.0)

        with col_pa2:
            st.subheader("📋 Estado Regulatorio")
            if st.button("Asentar Cierre Definitivo de Pozo"):
                if not ing_pa:
                    st.error("⚠️ Ingrese el Inspector Responsable del Cierre.")
                elif not (chk_tag and chk_presion):
                    st.error("❌ RECHAZADO: No cumple con la normativa regulatoria de aislamiento perpetuo.")
                else:
                    db_pa = SessionLocal()
                    nuevo_pa = Intervencion(
                        pozo_id=pozo_pa.id, tipo_servicio="ABANDONO", ingeniero_a_cargo=ing_pa,
                        volumen_teorico_bbl=0.0, volumen_real_bbl=0.0,
                        presion_max_psi=1000.0, caudal_promedio_bpm=0.0,
                        chk_hermeticidad=True,
                        estado="FINALIZADO"
                    )
                    db_pa.add(nuevo_pa)
                    db_pa.commit()
                    db_pa.close()
                    st.success(f"🛑 Pozo {pozo_pa.nombre_pozo} Clausurado de forma segura y permanente.")
                    st.rerun()

    # --- VISTA 4: AUDITORÍA (ERP) ---
    with tab_auditoria:
        st.subheader("📊 Historial General Unificado de Auditoría (ERP)")
        db_audit = SessionLocal()
        movimientos = db_audit.query(HistorialAlmacen, AlmacenMendoza).join(AlmacenMendoza, HistorialAlmacen.item_id == AlmacenMendoza.id).order_by(HistorialAlmacen.fecha.desc()).all()
        if not movimientos:
            st.info("No hay transacciones registradas.")
        else:
            st.dataframe([{
                "Fecha / Hora": m.fecha.strftime("%Y-%m-%d %H:%M:%S"), "Insumo": i.item_nombre,
                "Tipo Movimiento": m.tipo_movimiento, "Cantidad": f"{m.cantidad:,.1f} {i.unidad}", "Remito / Referencia": m.referencia
            } for m, i in movimientos], use_container_width=True)
        db_audit.close()
