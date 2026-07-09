# src/modules/pumping/calculator.py

class CementCalculator:
    """
    Clase encargada de los cálculos de ingeniería para cementación de pozos
    y bombeo de fluidos de Jota Energy.
    """
    
    @staticmethod
    def calcular_volumen_espacio_anular(od_casing_in: float, id_open_hole_in: float, longitud_ft: float) -> float:
        """
        Calcula el volumen del espacio anular en barriles (bbl).
        Fórmula: V = (ID_oh^2 - OD_csg^2) / 1029.4 * Longitud
        """
        if od_casing_in >= id_open_hole_in:
            raise ValueError("El diámetro del pozo abierto debe ser mayor al del casing.")
        
        factor_conversion = 1029.4
        volumen_bbl = ((id_open_hole_in ** 2) - (od_casing_in ** 2)) / factor_conversion * longitud_ft
        return round(volumen_bbl, 2)

    @staticmethod
    def calcular_requerimiento_sacos(volumen_lechada_bbl: float, rendimiento_pie3_saco: float) -> int:
        """
        Calcula la cantidad de sacos de cemento necesarios (asumiendo sacos estándar de la industria).
        1 bbl = 5.6146 pie³
        """
        if rendimiento_pie3_saco <= 0:
            raise ValueError("El rendimiento del saco debe ser mayor a cero.")
            
        volumen_pie3 = volumen_lechada_bbl * 5.6146
        sacos_necesarios = volumen_pie3 / rendimiento_pie3_saco
        return int(math.ceil(sacos_necesarios)) # Redondea hacia arriba al entero más cercano
