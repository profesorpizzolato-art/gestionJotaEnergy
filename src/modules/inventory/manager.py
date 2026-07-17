from src.modules.operations.models import AlmacenMendoza, HistorialAlmacen

class InventoryManager:
    @staticmethod
    def registrar_movimiento(db, item_nombre, cantidad, tipo_movimiento, referencia):
        """
        tipo_movimiento: 'INGRESO' o 'EGRESO'
        """
        item = db.query(AlmacenMendoza).filter(AlmacenMendoza.item_nombre == item_nombre).first()
        if not item:
            return {"status": "ERROR", "msg": "Item no encontrado"}
        
        # Actualizar stock
        if tipo_movimiento == 'INGRESO':
            item.stock_actual += cantidad
        elif tipo_movimiento == 'EGRESO':
            if item.stock_actual < cantidad:
                return {"status": "ERROR", "msg": "Stock insuficiente"}
            item.stock_actual -= cantidad
            
        # Registrar historial
        nuevo_mov = HistorialAlmacen(
            item_id=item.id,
            tipo_movimiento=tipo_movimiento,
            cantidad=cantidad,
            referencia=referencia
        )
        db.add(nuevo_mov)
        db.commit()
        return {"status": "OK"}
