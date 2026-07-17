import math

class FormulasIngenieria:
    @staticmethod
    def volumen_anular(od_casing, id_pozo, longitud):
        # Fórmula: (ID_pozo^2 - OD_casing^2) / 1029.4 * L
        return ((id_pozo**2 - od_casing**2) / 1029.4) * longitud

    @staticmethod
    def requerimiento_cemento(vol_anular, rendimiento_slurry=1.18):
        # Rendimiento estándar (cu ft/sk)
        return vol_anular * 5.61 / rendimiento_slurry 

    @staticmethod
    def presion_hidrostatica(densidad_ppg, tvd_ft):
        return 0.052 * densidad_ppg * tvd_ft
