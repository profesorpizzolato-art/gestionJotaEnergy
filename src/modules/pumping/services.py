# src/modules/pumping/services.py
from sqlalchemy.orm import Session
from src.modules.operations.models import Intervencion
# Nota: Si extendemos los modelos para incluir consumos, los importaríamos acá

class PumpingService:
    """
    Clase encargada de persistir y gestionar los datos operativos 
    de los bombeos en la base de datos.
    """
    
    @staticmethod
    def registrar_diseno_cementacion(db: Session, intervencion_id: str, comentarios: str) -> bool:
        """
        Actualiza la intervención con los comentarios o especificaciones del diseño.
        """
        intervencion = db.query(Intervencion).filter(Intervencion.id == intervencion_id).first()
        if intervencion:
            intervencion.comentarios_diseno = comentarios
            intervencion.estado = "EN_PROCESO"
            db.commit()
            return True
        return False
