import pandas as pd


class DimTiempo:
    def __init__(self, fecha_str):
        self.fecha = pd.to_datetime(fecha_str)
        self.anio = self.fecha.year
        self.mes = self.fecha.month
        self.dia = self.fecha.day
        


class DimAlcaldia:
    def __init__(self, nombre):
        self.nombre = nombre


class DimMetricasLluvia:
    def __init__(self, fila):
        self.probabilidad = float(fila['probabilidad_lluvia_intensa'])
        self.prediccion = int(fila['prediccion_lluvia_intensa'])
        self.valor_real = int(fila['valor_real'])
        self.riesgo = str(fila['riesgo']).upper()


class HechoClimatico:
    def __init__(self, dim_tiempo, dim_alcaldia, dim_metricas):
        self.tiempo = dim_tiempo
        self.alcaldia = dim_alcaldia
        self.metricas = dim_metricas


class Alcaldia:
    def __init__(self, nombre):
        self.nombre = nombre
        self.hechos_historial = {}

    def agregar_hecho(self, fecha, hecho: HechoClimatico):
        self.hechos_historial[fecha] = hecho

    def obtener_hecho(self, fecha):
        return self.hechos_historial.get(fecha, None)

