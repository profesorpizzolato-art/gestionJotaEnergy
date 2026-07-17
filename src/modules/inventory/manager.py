from src.modules.operations.models import AlmacenMendoza, HistorialAlmacen

class InventoryManager:
    @staticmethod
    def registrar_movimiento(db, item_nombre, cantidad, tipo_movimiento, referencia, costo_unitario=0.0):
        item = db.query(AlmacenMendoza).filter(AlmacenMendoza.item_nombre == item_nombre).first()
        if not item: return {"status": "ERROR", "msg": "Item no existe"}
        
        if tipo_movimiento == 'EGRESO' and item.stock_actual < cantidad:
            return {"status": "ERROR", "msg": "Stock insuficiente"}
            
        # Actualización
        item.stock_actual += cantidad if tipo_movimiento == 'INGRESO' else -cantidad
        
        # Registro con costo
        nuevo_mov = HistorialAlmacen(
            item_id=item.id,
            tipo_movimiento=tipo_movimiento,
            cantidad=cantidad,
            referencia=f"{referencia} | Costo Unit: {costo_unitario}"
        )
        db.add(nuevo_mov)
        db.commit()
        return {"status": "OK"}
