# src/modules/pumping/services.py
import io
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from src.modules.operations.models import Intervencion, AlmacenMendoza, HistorialAlmacen

class PumpingService:
    @staticmethod
    def inicializar_almacen_si_vacio(db: Session):
        items_base = [
            {"item_nombre": "Cemento Clase G", "unidad": "Sks", "stock_actual": 1500.0, "stock_minimo_alerta": 300.0},
            {"item_nombre": "Retardador Líquido Clase 11/12", "unidad": "gal", "stock_actual": 200.0, "stock_minimo_alerta": 50.0},
            {"item_nombre": "Apuntalante / Arena 20/40", "unidad": "lbs", "stock_actual": 250000.0, "stock_minimo_alerta": 60000.0}
        ]
        for item in items_base:
            existe = db.query(AlmacenMendoza).filter(AlmacenMendoza.item_nombre == item["item_nombre"]).first()
            if not existe:
                db.add(AlmacenMendoza(**item))
        db.commit()

    @staticmethod
    def registrar_movimiento_almacen(db: Session, item_id: int, tipo: str, cantidad: float, referencia: str):
        nuevo_registro = HistorialAlmacen(item_id=item_id, tipo_movimiento=tipo, cantidad=cantidad, referencia=referencia)
        db.add(nuevo_registro)
        db.commit()

    @staticmethod
    def verificar_y_descontar_stock(db: Session, cemento_sks: int, aditivo_gal: float, pozo_nombre: str) -> dict:
        item_cemento = db.query(AlmacenMendoza).filter(AlmacenMendoza.item_nombre == "Cemento Clase G").first()
        item_aditivo = db.query(AlmacenMendoza).filter(AlmacenMendoza.item_nombre == "Retardador Líquido Clase 11/12").first()
        logistica_info = {"status": "OK", "msg": "Materiales validados y despachados de Base Mendoza.", "alertas": []}

        if item_cemento and item_cemento.stock_actual < cemento_sks:
            logistica_info["status"] = "ERROR"
            logistica_info["msg"] = f"❌ Stock Insuficiente de Cemento. Requerido: {cemento_sks} Sks | En Almacén: {item_cemento.stock_actual} Sks."
            return logistica_info
        if item_aditivo and item_aditivo.stock_actual < aditivo_gal:
            logistica_info["status"] = "ERROR"
            logistica_info["msg"] = f"❌ Stock Insuficiente de Aditivos. Requerido: {aditivo_gal} gal | En Almacén: {item_aditivo.stock_actual} gal."
            return logistica_info

        if item_cemento and item_aditivo:
            item_cemento.stock_actual -= cemento_sks
            item_aditivo.stock_actual -= aditivo_gal
            PumpingService.registrar_movimiento_almacen(db, item_cemento.id, "EGRESO", cemento_sks, f"Consumo Operativo Pozo {pozo_nombre}")
            PumpingService.registrar_movimiento_almacen(db, item_aditivo.id, "EGRESO", aditivo_gal, f"Consumo Operativo Pozo {pozo_nombre}")
            if item_cemento.stock_actual <= item_cemento.stock_minimo_alerta:
                logistica_info["alertas"].append(f"⚠️ Stock Crítico: Cemento Clase G por debajo del mínimo de seguridad.")
            if item_aditivo.stock_actual <= item_aditivo.stock_minimo_alerta:
                logistica_info["alertas"].append(f"⚠️ Stock Crítico: Aditivo Líquido por debajo del mínimo de seguridad.")
            db.commit()
        return logistica_info

    @staticmethod
    def registrar_diseno_cementacion(db: Session, intervencion_id: int, resumen_texto: str) -> Intervencion:
        intervencion = db.query(Intervencion).filter(Intervencion.id == intervencion_id).first()
        if intervencion:
            intervencion.resumen_calculo = resumen_texto
            db.commit()
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
        story.append(Paragraph(f"<b>Fecha:</b> {intervencion.fecha_operacion.strftime('%Y-%m-%d %H:%M')}", normal_style))
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
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
@staticmethod
    def verificar_y_descontar_arena(db: Session, proppant_lbs: float, pozo_nombre: str) -> dict:
        """Valida y descuenta stock físico de apuntalante para Fracturas."""
        item_arena = db.query(AlmacenMendoza).filter(AlmacenMendoza.item_nombre == "Apuntalante / Arena 20/40").first()
        logistica_info = {"status": "OK", "msg": "Logística: Arena despachada desde Base Mendoza.", "alertas": []}

        if item_arena and item_arena.stock_actual < proppant_lbs:
            logistica_info["status"] = "ERROR"
            logistica_info["msg"] = f"❌ Quiebre de Stock: Requiere {proppant_lbs:,.1f} lbs | Disponible: {item_arena.stock_actual:,.1f} lbs."
            return logistica_info

        if item_arena:
            item_arena.stock_actual -= proppant_lbs
            PumpingService.registrar_movimiento_almacen(db, item_arena.id, "EGRESO", proppant_lbs, f"Inyección Fractura Pozo {pozo_nombre}")
            if item_arena.stock_actual <= item_arena.stock_minimo_alerta:
                logistica_info["alertas"].append("⚠️ Alerta Patrimonial: Stock de Arena por debajo del límite operativo de seguridad.")
            db.commit()
            
        return logistica_info
