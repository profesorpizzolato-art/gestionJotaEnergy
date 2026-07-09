# src/modules/pumping/services.py
from sqlalchemy.orm import Session
# Usamos la ruta absoluta consistente con todo el proyecto:
from src.modules.operations.models import Intervencion

class PumpingService:
    """
    Servicios lógicos para la gestión de bombeo y persistencia de diseños.
    """

    @staticmethod
    def registrar_diseno_cementacion(db: Session, intervencion_id: int, resumen_texto: str) -> Intervencion:
        """
        Busca una intervención existente y le actualiza el campo de resumen técnico.
        """
        intervencion = db.query(Intervencion).filter(Intervencion.id == intervencion_id).first()
        if intervencion:
            intervencion.resumen_calculo = resumen_texto
            db.commit()
            db.refresh(intervencion)
        return intervencion
