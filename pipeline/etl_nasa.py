import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import unicodedata


# ==================================================
# FUNCIÓN PARA NORMALIZAR ALCALDÍAS
# ==================================================

def normalizar_alcaldia(texto):

    if pd.isna(texto):
        return None

    texto = ''.join(
        c for c in unicodedata.normalize(
            'NFKD',
            str(texto)
        )
        if not unicodedata.combining(c)
    )

    return texto.strip().upper()


print("=== ETL NASA CON VARIABLES NUEVAS ===")

# ==================================================
# 1. CARGAR NASA
# ==================================================

df_nasa = pd.read_csv(
    "clima_nasa_crudo.csv"
)

print(f"\nRegistros iniciales: {df_nasa.shape[0]:,}")

print("\nColumnas detectadas:")
print(df_nasa.columns.tolist())

# ==================================================
# 2. RENOMBRAR COLUMNAS SI VIENEN CON NOMBRES NASA
# ==================================================

renombrar_columnas = {
    "PRECTOTCORR": "precip",
    "T2M": "temp",
    "T2M_MAX": "temp_max",
    "T2M_MIN": "temp_min",
    "RH2M": "humedad",
    "WS2M": "viento",
    "WS2M_MAX": "viento_max",
    "ALLSKY_SFC_SW_DWN": "radiacion",
    "PS": "presion",
    "QV2M": "humedad_especifica",
    "T2MDEW": "punto_rocio"
}

df_nasa = df_nasa.rename(
    columns=renombrar_columnas
)

print("\nColumnas después de renombrar:")
print(df_nasa.columns.tolist())

# ==================================================
# 3. VALIDAR COLUMNAS BÁSICAS
# ==================================================

columnas_obligatorias = [
    "fecha",
    "lat",
    "lon",
    "precip",
    "temp",
    "humedad",
    "viento",
    "radiacion",
    "presion"
]

faltantes = [
    col for col in columnas_obligatorias
    if col not in df_nasa.columns
]

if faltantes:
    raise ValueError(
        f"Faltan columnas obligatorias en clima_nasa_crudo.csv: {faltantes}"
    )

# ==================================================
# 4. CARGAR SHAPEFILE
# ==================================================

cdmx = gpd.read_file(
    "../alcaldias/poligonos_alcaldias_cdmx.shp"
)

cdmx = cdmx.to_crs(epsg=4326)

cdmx["geometry"] = cdmx["geometry"].buffer(0)

# ==================================================
# 5. PUNTOS ÚNICOS
# ==================================================

puntos_unicos = (
    df_nasa[["lat", "lon"]]
    .drop_duplicates()
    .copy()
)

print(
    f"\nPuntos únicos: "
    f"{puntos_unicos.shape[0]}"
)

# ==================================================
# 6. CREAR GEOMETRÍA DE PUNTOS
# ==================================================

geometry = [
    Point(xy)
    for xy in zip(
        puntos_unicos["lon"],
        puntos_unicos["lat"]
    )
]

gdf_puntos = gpd.GeoDataFrame(
    puntos_unicos,
    geometry=geometry,
    crs="EPSG:4326"
)

# ==================================================
# 7. ASIGNAR ALCALDÍA
# ==================================================

puntos_cdmx = gpd.sjoin(
    gdf_puntos,
    cdmx[["NOMGEO", "geometry"]],
    how="inner",
    predicate="intersects"
)

puntos_cdmx = (
    puntos_cdmx[
        ["lat", "lon", "NOMGEO"]
    ]
    .drop_duplicates(
        subset=["lat", "lon"]
    )
    .rename(
        columns={
            "NOMGEO": "alcaldia"
        }
    )
)

print(
    f"Puntos dentro de CDMX: "
    f"{puntos_cdmx.shape[0]}"
)

# ==================================================
# 8. FILTRAR NASA A PUNTOS DENTRO DE CDMX
# ==================================================

if "alcaldia" in df_nasa.columns:

    # Si el archivo crudo ya trae alcaldía, solo filtramos por los puntos válidos
    df_nasa = pd.merge(
        df_nasa,
        puntos_cdmx[["lat", "lon"]],
        on=["lat", "lon"],
        how="inner"
    )

else:

    # Si el archivo crudo no trae alcaldía, la agregamos desde el shapefile
    df_nasa = pd.merge(
        df_nasa,
        puntos_cdmx,
        on=["lat", "lon"],
        how="inner"
    )

print(
    f"Registros dentro de CDMX: "
    f"{df_nasa.shape[0]:,}"
)
# ==================================================
# 9. FECHA
# ==================================================

df_nasa["fecha"] = pd.to_datetime(
    df_nasa["fecha"].astype(str),
    format="%Y%m%d",
    errors="coerce"
)

df_nasa = df_nasa.dropna(
    subset=["fecha"]
)

# ==================================================
# 10. VARIABLES CLIMÁTICAS DISPONIBLES
# ==================================================

variables_clima_posibles = [
    "precip",
    "temp",
    "temp_max",
    "temp_min",
    "humedad",
    "viento",
    "viento_max",
    "radiacion",
    "presion",
    "humedad_especifica",
    "punto_rocio"
]

variables_clima = [
    col for col in variables_clima_posibles
    if col in df_nasa.columns
]

print("\nVariables climáticas utilizadas:")
print(variables_clima)

# ==================================================
# 11. CONVERTIR A NUMÉRICO
# ==================================================

for col in variables_clima:

    df_nasa[col] = pd.to_numeric(
        df_nasa[col],
        errors="coerce"
    )

# ==================================================
# 12. CONTROL DE CALIDAD NASA
# ==================================================

print("\n=== CONTROL DE CALIDAD ===")

for col in variables_clima:

    errores = (
        df_nasa[col] <= -99
    ).sum()

    print(
        f"{col}: {errores} valores inválidos"
    )

    df_nasa[col] = df_nasa[col].mask(
        df_nasa[col] <= -99
    )

# ==================================================
# 13. IMPUTACIÓN POR PUNTO GEOGRÁFICO
# ==================================================

df_nasa = df_nasa.sort_values(
    by=["lat", "lon", "fecha"]
)

df_nasa[variables_clima] = (
    df_nasa
    .groupby(["lat", "lon"])[variables_clima]
    .ffill()
    .bfill()
)

# ==================================================
# 14. NORMALIZAR ALCALDÍAS
# ==================================================

df_nasa["alcaldia"] = (
    df_nasa["alcaldia"]
    .apply(normalizar_alcaldia)
)

df_nasa = df_nasa.dropna(
    subset=["alcaldia"]
)


# ==================================================
# 16. VALIDACIÓN FINAL
# ==================================================

print("\n=== VALIDACIÓN FINAL ===")

print("\nNulos finales en variables climáticas:")
print(
    df_nasa[
        [
            col for col in variables_clima
            if col in df_nasa.columns
        ]
    ]
    .isnull()
    .sum()
)

print("\nDimensiones finales:")
print(df_nasa.shape)

print("\nNúmero de alcaldías:")
print(
    df_nasa["alcaldia"]
    .nunique()
)

print("\nListado de alcaldías:")
print(
    sorted(
        df_nasa["alcaldia"]
        .unique()
    )
)

print("\nRegistros por alcaldía:")
print(
    df_nasa["alcaldia"]
    .value_counts()
    .sort_index()
)

print("\nPuntos únicos por alcaldía:")
print(
    df_nasa
    .groupby("alcaldia")[["lat", "lon"]]
    .nunique()
)

print("\nFechas:")
print("Fecha mínima:", df_nasa["fecha"].min())
print("Fecha máxima:", df_nasa["fecha"].max())

print("\nColumnas finales:")
print(df_nasa.columns.tolist())

# ==================================================
# 17. EXPORTAR
# ==================================================

df_nasa.to_csv(
    "nasa_limpio.csv",
    index=False
)

print(
    "\nArchivo nasa_limpio.csv generado correctamente."
)