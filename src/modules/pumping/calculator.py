# src/modules/pumping/calculator.py
import math

class CementCalculator:
    """
    Clase encargada de los cálculos de ingeniería para cementación de pozos
    y bombeo de fluidos de Jota Energy.
    """
    
    @staticmethod
    def calcular_volumen_espacio_anular(od_casing_in: float, id_open_hole_in: float, longitud_ft: float) -> float:
        if od_casing_in >= id_open_hole_in:
            raise ValueError("El diámetro del pozo abierto debe ser mayor al del casing.")
        factor_conversion = 1029.4
        volumen_bbl = ((id_open_hole_in ** 2) - (od_casing_in ** 2)) / factor_conversion * longitud_ft
        return round(volumen_bbl, 2)

    @staticmethod
    def calcular_requerimiento_sacos(volumen_lechada_bbl: float, rendimiento_pie3_saco: float) -> int:
        if rendimiento_pie3_saco <= 0:
            raise ValueError("El rendimiento del saco debe ser mayor a cero.")
        volumen_pie3 = volumen_lechada_bbl * 5.6146
        sacos_necesarios = volumen_pie3 / rendimiento_pie3_saco
        return int(math.ceil(sacos_necesarios))

    # --- NUEVOS MÉTODOS PARA LOGÍSTICA Y QUÍMICOS ---

    @staticmethod
    def calcular_agua_mezcla(sacos_totales: int, agua_por_saco_gal: float) -> float:
        """
        Calcula el agua de mezcla total requerida en barriles (bbl).
        Fórmula: (Sacos * Galones por saco) / 42 (galones por bbl)
        """
        if agua_por_saco_gal < 0:
            raise ValueError("El requerimiento de agua por saco no puede ser negativo.")
        
        total_galones = sacos_totales * agua_por_saco_gal
        total_barriles = total_galones / 42.0
        return round(total_barriles, 2)

    @staticmethod
    def calcular_aditivo_liquido(sacos_totales: int, dosis_gps: float) -> float:
        """
        Calcula el volumen de un aditivo líquido requerido en galones (gal).
        Falsamente abreviado en la industria como GPS (Gallons Per Sack).
        """
        if dosis_gps < 0:
            raise ValueError("La dosis del aditivo no puede ser negativa.")
            
        total_galones = sacos_totales * dosis_gps
        return round(total_galones, 2)
