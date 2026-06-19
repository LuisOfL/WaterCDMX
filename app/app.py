import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from clases import DimTiempo, DimAlcaldia, DimMetricasLluvia, HechoClimatico, Alcaldia
import unicodedata
import shapefile

class GestorCuboOlap:
    def __init__(self, ruta_csv, ruta_shapefile="alcaldias/poligonos_alcaldias_cdmx"):
        self.df = pd.read_csv(ruta_csv)
        self.ruta_shp = ruta_shapefile
        self.alcaldias = {}
        self._construir_cubo()

    def _construir_cubo(self):
        self.df['fecha_dt'] = pd.to_datetime(self.df['fecha']).dt.date
        
        nombres_alcaldias = self.df['alcaldia'].unique()
        for nombre in nombres_alcaldias:
            nombre_limpio = self.normalizar_texto(nombre)
            self.alcaldias[nombre_limpio] = Alcaldia(nombre_limpio)
        
        for _, fila in self.df.iterrows():
            nombre_alcaldia = self.normalizar_texto(fila['alcaldia'])
            alc_obj = self.alcaldias.get(nombre_alcaldia)
            if alc_obj:
                fecha_key = fila['fecha_dt']
                dim_t = DimTiempo(fila['fecha'])
                dim_a = DimAlcaldia(nombre_alcaldia)
                dim_m = DimMetricasLluvia(fila)
                alc_obj.agregar_hecho(fecha_key, HechoClimatico(dim_t, dim_a, dim_m))

    def get_rango_fechas(self):
        return self.df['fecha_dt'].min(), self.df['fecha_dt'].max()

    def obtener_datos_fecha(self, fecha_sel):
        datos = {}
        for nombre_limpio, alc_obj in self.alcaldias.items():
            hecho = alc_obj.obtener_hecho(fecha_sel)
            if hecho:
                datos[nombre_limpio] = {
                    "probabilidad": hecho.metricas.probabilidad,
                    "prediccion": hecho.metricas.prediccion,
                    "valor_real": hecho.metricas.valor_real,
                    "riesgo": hecho.metricas.riesgo
                }
        return datos

    def normalizar_texto(self, texto):
        if not texto: return ""
        texto = str(texto).strip()
        sub_bytes = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore')
        return sub_bytes.decode('utf-8').upper().strip()

    def extraer_geojson_desde_shp(self):
        """Extrae la estructura GeoJSON de forma nativa e inmediata."""
        try:

            sf = shapefile.Reader(self.ruta_shp, encoding="utf-8")
            geojson_base = sf.__geo_interface__
            
            features_procesadas = []
            for feature in geojson_base["features"]:
                nombre_crudo = feature["properties"]["NOMGEO"]
                nombre_normalizado = self.normalizar_texto(nombre_crudo)
  
                features_procesadas.append({
                    "type": "Feature",
                    "properties": {
                        "name": nombre_normalizado,
                        "display_name": nombre_crudo
                    },
                    "geometry": feature["geometry"]
                })
                
            return {"type": "FeatureCollection", "features": features_procesadas}
        except Exception as e:
            print(f"Error procesando shapes: {e}")
            return None

st.set_page_config(page_title="CDMX Rain Predictor Shapefile", layout="wide")

st.markdown("""
    <style>
        .reportview-container { background: #f8fafc; }
        h1 { font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 400; color: #1e293b; }
    </style>
""", unsafe_allow_html=True)

st.title("Predicción Territorial de Lluvia Intensa")
st.caption("Estructura de Datos POO con Integración de Formato Shapefile Nativo")

cubo = GestorCuboOlap(
    ruta_csv='predicciones_regresion_logistica_lluvia.csv',
    ruta_shapefile='alcaldias/poligonos_alcaldias_cdmx'
)

min_d, max_d = cubo.get_rango_fechas()

@st.cache_data
def cargar_geometria():
    geo = cubo.extraer_geojson_desde_shp()
    if not geo or len(geo["features"]) == 0:
        st.error("Error al procesar los archivos espaciales de la carpeta /alcaldias.")
        st.stop()
    return geo

geojson_data = cargar_geometria()

# Selector de fecha
col_fecha, _ = st.columns([1, 2])
with col_fecha:
    fecha_sel = st.date_input("Fecha de Consulta:", min_value=min_d, max_value=max_d, value=min_d)

datos_fecha = cubo.obtener_datos_fecha(fecha_sel)

# Paleta Coroplética
colores_riesgo = {
    'BAJO': '#10b981',
    'MEDIO': '#f59e0b',
    'ALTO': '#ef4444',
    'MUY ALTO': '#7f1d1d'
}

def estilar_alcaldia(feature):
    nombre_alc = feature['properties']['name']
    datos_alc = datos_fecha.get(nombre_alc)
    
    if datos_alc:
        color_relleno = colores_riesgo.get(datos_alc['riesgo'], '#94a3b8')
        opacidad = 0.75
    else:
        color_relleno = '#cbd5e1'
        opacidad = 0.30

    return {
        'fillColor': color_relleno,
        'color': '#ffffff',
        'weight': 2.0,
        'fillOpacity': opacidad
    }

col_mapa, col_tabla = st.columns([11, 6])

with col_mapa:
    st.subheader("Mapa Coroplético Oficial CDMX")
    m = folium.Map(location=[19.3200, -99.1333], zoom_start=10, tiles="CartoDB positron")
    
    folium.GeoJson(
        geojson_data,
        style_function=estilar_alcaldia,
        tooltip=folium.GeoJsonTooltip(
            fields=['display_name'],
            aliases=['Alcaldía:'],
            style=("background-color: white; color: #333; font-family: sans-serif; font-size: 12px; padding: 6px; border-radius: 4px;")
        )
    ).add_to(m)
    
    folium_static(m, width=720, height=540)

with col_tabla:
    st.subheader("Métricas por Alcaldía")
    if datos_fecha:
        filas_tabla = []
        for nombre, mt in datos_fecha.items():
            filas_tabla.append({
                "Alcaldía": nombre,
                "Probabilidad": mt["probabilidad"],
                "Riesgo": mt["riesgo"]
            })
            
        df_tabla = pd.DataFrame(filas_tabla).sort_values(by="Probabilidad", ascending=False)
        
        st.dataframe(
            df_tabla,
            column_config={
                "Alcaldía": st.column_config.TextColumn("Alcaldía"),
                "Probabilidad": st.column_config.NumberColumn("Probabilidad de Lluvia", format="%.2%"),
                "Riesgo": st.column_config.TextColumn("Nivel de Riesgo")
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )