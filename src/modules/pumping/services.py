# src/modules/pumping/services.py
import io
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from src.modules.operations.models import Intervencion

class PumpingService:
    """
    Servicios lógicos de Jota Energy para la gestión de bombeo, 
    logística e informes comerciales (Post-Job Reports).
    """

    @staticmethod
    def registrar_diseno_cementacion(db: Session, intervencion_id: int, resumen_texto: str) -> Intervencion:
        """Actualiza el resumen técnico en la base de datos."""
        intervencion = db.query(Intervencion).filter(Intervencion.id == intervencion_id).first()
        if intervencion:
            intervencion.resumen_calculo = resumen_texto
            db.commit()
            db.refresh(intervencion)
        return intervencion

    @staticmethod
    def simular_descuento_logistico(sacos: int, aditivo_gal: float):
        """
        Módulo de Activos y Suministros:
        Simula la trazabilidad de lotes y despacho de insumos desde la base Mendoza.
        """
        # Aquí en el futuro conectarás con tu tabla de inventarios/stock
        logistica_info = {
            "origen": "Base Logística Mendoza",
            "despacho_cemento": f"{sacos} Sks (Lote Certificado QHSE)",
            "despacho_aditivos": f"{aditivo_gal} gal (Retardador Clase 11/12)",
            "alerta_mantenimiento_bomba": "Unidad de bombeo operativo óptimo (< 250 hrs de servicio)"
        }
        return logistica_info

    @staticmethod
    def generar_pdf_post_job(intervencion: Intervencion, pozo_nombre: str, sacos: int, aditivo_gal: float) -> bytes:
        """
        Gestión Comercial: Genera un reporte PDF formal (Post-Job Report) 
        en memoria listo para su descarga por el operador o cliente.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []
        
        # Estilos corporativos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CorpTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#1E7373'),
            spaceAfter=20
        )
        subtitle_style = ParagraphStyle(
            'CorpSub',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12
        )
        normal_style = styles['Normal']

        # Encabezado
        story.append(Paragraph("⚡ JOTA ENERGY — REPORT DE FIN DE TRABAJO", title_style))
        story.append(Paragraph(f"<b>Servicio:</b> {intervencion.tipo_servicio} | <b>Estado:</b> {intervencion.estado}", normal_style))
        story.append(Paragraph(f"<b>Fecha de Operación:</b> {intervencion.fecha_operacion.strftime('%Y-%m-%d %H:%M')}", normal_style))
        story.append(Spacer(1, 15))

        # Tabla de Datos Generales
        story.append(Paragraph("📋 Información de la Intervención", subtitle_style))
        datos_generales = [
            ["Pozo Target:", pozo_nombre, "Ingeniero a Cargo:", intervencion.ingeniero_a_cargo],
            ["Presión Máx (psi):", f"{intervencion.presion_max_psi} psi", "Caudal Prom (bpm):", f"{intervencion.caudal_promedio_bpm} bpm"]
        ]
        t1 = Table(datos_generales, colWidths=[110, 140, 120, 140])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#EBF3F3')),
            ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#EBF3F3')),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#222222')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t1)
        story.append(Spacer(1, 15))

        # Tabla de Balance Volumétrico (Diseño vs Real)
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
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E7373')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9F9F9')]),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t2)
        story.append(Spacer(1, 25))

        # Firmas / Cierre de conformidad
        story.append(Paragraph("<b>Aprobación Técnica y Conformidad del Cliente:</b>", normal_style))
        story.append(Spacer(1, 40))
        datos_firmas = [["___________________________", "___________________________"], ["Firma Ingeniero Jota Energy", "Firma Supervisor de Operaciones"]]
        t3 = Table(datos_firmas, colWidths=[260, 260])
        t3.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        story.append(t3)

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
