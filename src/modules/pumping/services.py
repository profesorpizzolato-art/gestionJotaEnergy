# src/modules/pumping/services.py
import io
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from src.modules.operations.models import Intervencion, AlmacenMendoza

class PumpingService:
    """
    Servicios lógicos de Jota Energy para la gestión de bombeo, 
    logística real de almacén Mendoza e informes comerciales.
    """

    @staticmethod
    def inicializar_almacen_si_vacio(db: Session):
        """Inicializa ítems base en el almacén si la tabla está en cero."""
        items_base = [
            {"item_nombre": "Cemento Clase G", "unidad": "Sks", "stock_actual": 1500.0, "stock_minimo_alerta": 300.0},
            {"item_nombre": "Retardador Líquido Clase 11/12", "unidad": "gal", "stock_actual": 200.0, "stock_minimo_alerta": 50.0},
            {"item_nombre": "Apuntalante / Arena 20/40", "unidad": "lbs", "stock_actual": 250000.0, "stock_minimo_alerta": 60000.0}
        ]
        for item in items_base:
            existe = db.query(AlmacenMendoza).filter(AlmacenMendoza.item_nombre == item["item_nombre"]).first()
            if not existe:
                nuevo_item = AlmacenMendoza(**item)
                db.add(nuevo_item)
        db.commit()

    @staticmethod
    def verificar_y_descontar_stock(db: Session, cemento_sks: int, aditivo_gal: float) -> dict:
        """
        Módulo de Activos y Suministros:
        Verifica disponibilidad física en la Base Mendoza y ejecuta el descuento real.
        """
        item_cemento = db.query(AlmacenMendoza).filter(AlmacenMendoza.item_nombre == "Cemento Clase G").first()
        item_aditivo = db.query(AlmacenMendoza).filter(AlmacenMendoza.item_nombre == "Retardador Líquido Clase 11/12").first()

        logistica_info = {
            "status": "OK",
            "msg": "Materiales despachados de manera exitosa de Base Mendoza.",
            "alertas": []
        }

        # Verificaciones de stock mínimo
        if item_cemento and item_cemento.stock_actual < cemento_sks:
            logistica_info["status"] = "ERROR"
            logistica_info["msg"] = f"❌ Stock Insuficiente de Cemento. Requerido: {cemento_sks} Sks | Disponible: {item_cemento.stock_actual} Sks."
            return logistica_info
        
        if item_aditivo and item_aditivo.stock_actual < aditivo_gal:
            logistica_info["status"] = "ERROR"
            logistica_info["msg"] = f"❌ Stock Insuficiente de Aditivos. Requerido: {aditivo_gal} gal | Disponible: {item_aditivo.stock_actual} gal."
            return logistica_info

        # Descuento físico
        if item_cemento and item_aditivo:
            item_cemento.stock_actual -= cemento_sks
            item_aditivo.stock_actual -= aditivo_gal
            
            # Alertas de punto de reorden
            if item_cemento.stock_actual <= item_cemento.stock_minimo_alerta:
                logistica_info["alertas"].append(f"⚠️ ¡Alerta de Stock Crítico! Cemento Clase G por debajo del mínimo ({item_cemento.stock_actual} Sks restantes).")
            if item_aditivo.stock_actual <= item_aditivo.stock_minimo_alerta:
                logistica_info["alertas"].append(f"⚠️ ¡Alerta de Stock Crítico! Retardador Líquido por debajo del mínimo ({item_aditivo.stock_actual} gal restantes).")
            
            db.commit()

        return logistica_info

    @staticmethod
    def registrar_diseno_cementacion(db: Session, intervencion_id: int, resumen_texto: str) -> Intervencion:
        intervencion = db.query(Intervencion).filter(Intervencion.id == intervencion_id).first()
        if intervencion:
            intervencion.resumen_calculo = resumen_texto
            db.commit()
            db.refresh(intervencion)
        return intervencion

    @staticmethod
    def generar_pdf_post_job(intervencion: Intervencion, pozo_nombre: str, sacos: int, aditivo_gal: float) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CorpTitle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#1E7373'), spaceAfter=20)
        subtitle_style = ParagraphStyle('CorpSub', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#333333'), spaceAfter=12)
        normal_style = styles['Normal']

        story.append(Paragraph("⚡ JOTA ENERGY — REPORT DE FIN DE TRABAJO", title_style))
        story.append(Paragraph(f"<b>Servicio:</b> {intervencion.tipo_servicio} | <b>Estado:</b> {intervencion.estado}", normal_style))
        story.append(Paragraph(f"<b>Fecha de Operación:</b> {intervencion.fecha_operacion.strftime('%Y-%m-%d %H:%M')}", normal_style))
        story.append(Spacer(1, 15))

        story.append(Paragraph("📋 Información de la Intervención", subtitle_style))
        datos_generales = [
            ["Pozo Target:", pozo_nombre, "Ingeniero a Cargo:", intervencion.ingeniero_a_cargo],
            ["Presión Máx (psi):", f"{intervencion.presion_max_psi} psi", "Caudal Prom (bpm):", f"{intervencion.caudal_promedio_bpm} bpm"]
        ]
        t1 = Table(datos_generales, colWidths=[110, 140, 120, 140])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#EBF3F3')), ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#EBF3F3')),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#222222')), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t1)
        story.append(Spacer(1, 15))

        story.append(Paragraph("📊 Balance Volumétrico de Fluidos", subtitle_style))
        desvio = round(intervencion.volumen_real_bbl - intervencion.volumen_teorico_bbl, 2)
        datos_fluidos = [
            ["Parámetro", "Diseño (Teórico)", "Campo (Real)", "Desvío"],
            ["Volumen de Lechada", f"{intervencion.volumen_teorico_bbl} bbl", f"{intervencion.volumen_real_bbl} bbl", f"{desvio} bbl"],
            ["Sacos de Cemento", f"{sacos} Sks", f"{sacos} Sks", "0 Sks"],
            ["Aditivo Líquido", f"{aditivo_gal} gal", f"{aditivo_gal} gal", "0 gal"]
        ]
        t2 = Table(datos_fluidos, colWidths=[130, 130, 130, 120])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E7373')), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9F9F9')]),
        ]))
        story.append(t2)
        story.append(Spacer(1, 25))

        story.append(Paragraph("<b>Aprobación Técnica y Conformidad del Cliente:</b>", normal_style))
        story.append(Spacer(1, 40))
        datos_firmas = [["___________________________", "___________________________"], ["Firma Ingeniero Jota Energy", "Firma Supervisor de Operaciones"]]
        t3 = Table(datos_firmas, colWidths=[260, 260])
        t3.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        story.append(t3)

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
