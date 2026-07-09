# src/modules/pumping/services.py
from sqlalchemy.orm import Session
# SOLUCIÓN: Quitamos el prefijo 'src.' para que sea consistente con la estructura de la nube
from modules.operations.models import Intervencion

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
