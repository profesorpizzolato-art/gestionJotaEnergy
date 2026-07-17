# src/modules/safety/protocols.py

class QHSEProtocolos:
    # Diccionario con los protocolos por tipo de operación
    PROTOCOLOS = {
        "CEMENTACION": [
            "Test de presión de líneas a 1.5x Presión Máxima",
            "Verificación de Válvulas de Alivio (PSV) operativas",
            "Zona de exclusión a 30 metros de línea de alta presión",
            "Control de densidad de lechada previo a bombeo"
        ],
        "FRACTURA": [
            "Prueba de integridad de casing",
            "Verificación de paradas de emergencia en bombas",
            "Checklist de mangueras de alta presión",
            "Comunicación radial confirmada con mesa"
        ],
        "ABANDONO": [
            "Verificación de profundidad de tapón de cemento",
            "Prueba de hermeticidad (Integridad de formación)",
            "Reporte de gases en boca de pozo",
            "Certificación de sellado superficial"
        ]
    }

    @staticmethod
    def obtener_protocolos(operacion):
        return QHSEProtocolos.PROTOCOLOS.get(operacion, [])
