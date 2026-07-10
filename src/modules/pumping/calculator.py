# src/modules/pumping/calculator.py
import math

class CementCalculator:
    @staticmethod
    def calcular_volumen_espacio_anular(casing_od: float, hole_id: float, longitud_ft: float) -> float:
        """Calcula el volumen del espacio anular en barriles (bbl)."""
        vol_ft3 = (math.pi / 4) * ((hole_id ** 2) - (casing_od ** 2)) * longitud_ft / 144
        vol_bbl = vol_ft3 * 0.178107
        return round(vol_bbl, 2)

    @staticmethod
    def calcular_requerimiento_sacos(volumen_bbl: float, rendimiento_ft3_saco: float) -> float:
        """Determina la cantidad de sacos de cemento necesarios."""
        volumen_ft3 = volumen_bbl / 0.178107
        return round(volumen_ft3 / rendimiento_ft3_saco, 2)

    @staticmethod
    def calcular_agua_mezcla(sacos: float, agua_req_gal_saco: float) -> float:
        """Calcula el agua total requerida para la mezcla en barriles."""
        total_gal = sacos * agua_req_gal_saco
        return round(total_gal / 42, 2)

    @staticmethod
    def calcular_aditivo_liquido(sacos: float, dosis_gps: float) -> float:
        """Calcula los galones totales del aditivo/retardador."""
        return round(sacos * dosis_gps, 2)
