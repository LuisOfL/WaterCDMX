import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import requests
import time

print("=== EXTRACCIÓN NASA POWER SOLO PUNTOS CDMX ===")

# ==================================================
# 1. GENERAR MALLA DE COORDENADAS
# ==================================================

minx, maxx = -99.36, -98.94
miny, maxy = 19.03, 19.59

grid_size = 0.009

lats = np.arange(miny, maxy, grid_size)
lons = np.arange(minx, maxx, grid_size)

puntos_coordenadas = []

for lat in lats:
    for lon in lons:
        puntos_coordenadas.append((lat, lon))

print(f"Puntos generados inicialmente: {len(puntos_coordenadas)}")

# ==================================================
# 2. CARGAR SHAPEFILE DE ALCALDÍAS
# ==================================================

cdmx = gpd.read_file(
    "../alcaldias/poligonos_alcaldias_cdmx.shp"
)

cdmx = cdmx.to_crs(epsg=4326)
cdmx["geometry"] = cdmx["geometry"].buffer(0)

# ==================================================
# 3. CONVERTIR MALLA A GEODATAFRAME
# ==================================================

df_puntos = pd.DataFrame(
    puntos_coordenadas,
    columns=["lat", "lon"]
)

geometry = [
    Point(lon, lat)
    for lat, lon in puntos_coordenadas
]

gdf_puntos = gpd.GeoDataFrame(
    df_puntos,
    geometry=geometry,
    crs="EPSG:4326"
)

# ==================================================
# 4. FILTRAR SOLO PUNTOS DENTRO DE CDMX
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

puntos_coordenadas = list(
    zip(
        puntos_cdmx["lat"],
        puntos_cdmx["lon"]
    )
)

total_puntos = len(puntos_coordenadas)

print(f"Puntos dentro de CDMX: {total_puntos}")
print(f"Registros estimados: {total_puntos * 1095:,}")

# ==================================================
# 5. CONFIGURACIÓN DE LA API NASA POWER
# ==================================================

start_date = "20190102"
end_date = "20211231"

parameters = (
    "PRECTOTCORR,"
    "T2M,"
    "T2M_MAX,"
    "T2M_MIN,"
    "RH2M,"
    "WS2M,"
    "WS2M_MAX,"
    "ALLSKY_SFC_SW_DWN,"
    "PS,"
    "QV2M,"
    "T2MDEW"
)

# ==================================================
# 6. EXTRACCIÓN DE LA API
# ==================================================

rows = []

for idx, (lat, lon) in enumerate(puntos_coordenadas, 1):

    url = (
        "https://power.larc.nasa.gov/api/temporal/daily/point"
        f"?parameters={parameters}"
        "&community=RE"
        f"&longitude={lon}"
        f"&latitude={lat}"
        f"&start={start_date}"
        f"&end={end_date}"
        "&format=JSON"
    )

    intentos = 3
    exito = False

    while intentos > 0 and not exito:

        try:
            response = requests.get(
                url,
                timeout=30
            )

            if response.status_code == 429:
                print("Límite de peticiones alcanzado. Esperando 10 segundos...")
                time.sleep(10)
                intentos -= 1
                continue

            if response.status_code != 200:
                print(
                    f"Error HTTP {response.status_code} "
                    f"en punto {lat}, {lon}"
                )
                intentos -= 1
                time.sleep(3)
                continue

            data = response.json()

            clima = data["properties"]["parameter"]

            precip = clima.get("PRECTOTCORR", {})
            temp = clima.get("T2M", {})
            temp_max = clima.get("T2M_MAX", {})
            temp_min = clima.get("T2M_MIN", {})
            hum = clima.get("RH2M", {})
            wind = clima.get("WS2M", {})
            wind_max = clima.get("WS2M_MAX", {})
            rad = clima.get("ALLSKY_SFC_SW_DWN", {})
            pres = clima.get("PS", {})
            qv2m = clima.get("QV2M", {})
            dew = clima.get("T2MDEW", {})

            for fecha in precip:

                rows.append({
                    "fecha": fecha,
                    "lat": lat,
                    "lon": lon,
                    "alcaldia": puntos_cdmx[
                        (puntos_cdmx["lat"] == lat)
                        &
                        (puntos_cdmx["lon"] == lon)
                    ]["alcaldia"].iloc[0],

                    "precip": precip.get(fecha),
                    "temp": temp.get(fecha),
                    "temp_max": temp_max.get(fecha),
                    "temp_min": temp_min.get(fecha),
                    "humedad": hum.get(fecha),
                    "viento": wind.get(fecha),
                    "viento_max": wind_max.get(fecha),
                    "radiacion": rad.get(fecha),
                    "presion": pres.get(fecha),
                    "humedad_especifica": qv2m.get(fecha),
                    "punto_rocio": dew.get(fecha)
                })

            exito = True

            print(
                f"{idx}/{total_puntos} puntos descargados correctamente."
            )

            time.sleep(0.6)

        except Exception as e:
            print(
                f"Error en punto {lat}, {lon}. "
                f"Intentos restantes: {intentos - 1}"
            )
            print(e)

            intentos -= 1
            time.sleep(3)

    if idx % 100 == 0:
        df_temporal = pd.DataFrame(rows)

        df_temporal.to_csv(
            "clima_nasa_crudo_RESPALDO.csv",
            index=False
        )

        print(f"--- Respaldo guardado en punto {idx} ---")

# ==================================================
# 7. EXPORTAR DATASET CRUDO
# ==================================================

if rows:

    df = pd.DataFrame(rows)

    print("\nDataset crudo final generado con éxito.")
    print("Dimensiones:", df.shape)
    print("Columnas:")
    print(df.columns.tolist())

    df.to_csv(
        "clima_nasa_crudo.csv",
        index=False
    )

    print("\nArchivo clima_nasa_crudo.csv generado correctamente.")

else:
    print("\nNo se logró recuperar ningún registro de la API.")