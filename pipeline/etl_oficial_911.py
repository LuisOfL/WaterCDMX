import pandas as pd
import unicodedata

print("=== ETL 911: INCIDENTES HÍDRICOS CONFIRMADOS ===")




def limpiar_texto(texto):
    if not isinstance(texto, str):
        return ""

    texto_limpio = ''.join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )

    texto_limpio = (
        texto_limpio
        .strip()
        .lower()
    )

    texto_limpio = " ".join(
        texto_limpio.split()
    )

    return texto_limpio


def normalizar_alcaldia(texto):
    if pd.isna(texto):
        return None

    texto = ''.join(
        c for c in unicodedata.normalize("NFKD", str(texto))
        if not unicodedata.combining(c)
    )

    return texto.strip().upper()


def limpiar_nombre_columna(texto):
    return (
        str(texto)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )




df_911 = pd.read_csv(
    "s3://apps-proyecto/911_sin_filtrar.csv",
    encoding="latin1"
)

print(f"\nRegistros iniciales: {df_911.shape[0]:,}")
print("\nColumnas originales:")
print(df_911.columns.tolist())




col_alcaldia = "alcaldia_cierre"
col_fecha = "fecha_creacion"
col_lat = "latitud"
col_lon = "longitud"
col_folio = "folio"
col_incidente = "incidente_c4"
col_cierre = "codigo_cierre"


columnas_necesarias = [
    col_alcaldia,
    col_fecha,
    col_lat,
    col_lon,
    col_folio,
    col_incidente,
    col_cierre
]

faltantes = [
    col for col in columnas_necesarias
    if col not in df_911.columns
]

if faltantes:
    raise ValueError(
        f"Faltan columnas en 911_sin_filtrar.csv: {faltantes}"
    )




df_911[col_incidente] = (
    df_911[col_incidente]
    .apply(limpiar_texto)
)

df_911[col_cierre] = (
    df_911[col_cierre]
    .astype(str)
    .str.strip()
)

df_911[col_cierre] = (
    df_911[col_cierre]
    .apply(limpiar_texto)
)

df_911[col_alcaldia] = (
    df_911[col_alcaldia]
    .apply(normalizar_alcaldia)
)



incidentes_interes = [
    "inundacion",
    "encharcamiento",
    "aguas negras",
    "fuga de agua",
    "desborde canal rio presa"
]

df_911 = df_911[
    df_911[col_incidente].isin(incidentes_interes)
].copy()

print(f"\nTras filtrar incidentes hídricos: {df_911.shape[0]:,}")

print("\nTipos detectados después del filtro:")
print(
    df_911[col_incidente]
    .value_counts()
)



codigos_afirmativos = [
    "a",
    "afirmativo"
]

df_911 = df_911[
    df_911[col_cierre].isin(codigos_afirmativos)
].copy()

print(f"\nIncidentes confirmados: {df_911.shape[0]:,}")

print("\nTipos confirmados:")
print(
    df_911[col_incidente]
    .value_counts()
)



df_911["fecha"] = pd.to_datetime(
    df_911[col_fecha],
    errors="coerce"
)

df_911 = df_911.dropna(
    subset=["fecha"]
)

df_911["fecha"] = df_911["fecha"].dt.normalize()



df_911[col_lat] = pd.to_numeric(
    df_911[col_lat],
    errors="coerce"
)

df_911[col_lon] = pd.to_numeric(
    df_911[col_lon],
    errors="coerce"
)

df_911 = df_911.dropna(
    subset=[
        col_lat,
        col_lon
    ]
)



df_911 = df_911[
    (df_911[col_lat] >= 19.0) &
    (df_911[col_lat] <= 19.6) &
    (df_911[col_lon] >= -99.4) &
    (df_911[col_lon] <= -98.9)
].copy()

print(f"\nTras filtro geográfico CDMX: {df_911.shape[0]:,}")



df_911 = df_911.dropna(
    subset=[col_alcaldia]
)

df_911 = df_911[
    df_911[col_alcaldia] != ""
].copy()



df_911_limpio = df_911[
    [
        col_folio,
        "fecha",
        col_alcaldia,
        col_lat,
        col_lon,
        col_incidente,
        col_cierre
    ]
].rename(
    columns={
        col_folio: "id_incidente",
        col_alcaldia: "alcaldia",
        col_lat: "latitud",
        col_lon: "longitud",
        col_incidente: "tipo_incidente",
        col_cierre: "codigo_cierre"
    }
)

df_911_limpio["tipo_incidente"] = (
    df_911_limpio["tipo_incidente"]
    .apply(limpiar_texto)
)

df_911_limpio["alcaldia"] = (
    df_911_limpio["alcaldia"]
    .apply(normalizar_alcaldia)
)



tabla_incidentes = pd.crosstab(
    index=[
        df_911_limpio["fecha"],
        df_911_limpio["alcaldia"]
    ],
    columns=df_911_limpio["tipo_incidente"]
).reset_index()

tabla_incidentes.columns.name = None

tabla_incidentes.columns = [
    limpiar_nombre_columna(col)
    for col in tabla_incidentes.columns
]

tabla_incidentes = tabla_incidentes.rename(
    columns={
        "aguas_negras": "aguas_negras",
        "desborde_canal_rio_presa": "desborde_canal",
        "encharcamiento": "encharcamiento",
        "fuga_de_agua": "fuga_agua",
        "inundacion": "inundacion"
    }
)

columnas_incidentes = [
    "aguas_negras",
    "desborde_canal",
    "encharcamiento",
    "fuga_agua",
    "inundacion"
]

for col in columnas_incidentes:
    if col not in tabla_incidentes.columns:
        tabla_incidentes[col] = 0

tabla_incidentes["total_incidentes"] = (
    tabla_incidentes[columnas_incidentes]
    .sum(axis=1)
)

tabla_incidentes["hubo_inundacion"] = (
    tabla_incidentes["inundacion"] > 0
).astype(int)

tabla_incidentes["hubo_incidente_hidrico"] = (
    (
        tabla_incidentes["inundacion"]
        + tabla_incidentes["encharcamiento"]
        + tabla_incidentes["aguas_negras"]
        + tabla_incidentes["fuga_agua"]
        + tabla_incidentes["desborde_canal"]
    ) > 0
).astype(int)



print("\n=== RESUMEN FINAL DETALLADO ===")

print(f"Registros finales 911_limpio.csv: {df_911_limpio.shape[0]:,}")

print("\nIncidentes detallados:")
print(
    df_911_limpio["tipo_incidente"]
    .value_counts()
)

print("\nAlcaldías detalladas:")
print(
    df_911_limpio["alcaldia"]
    .value_counts()
    .sort_index()
)

print("\n=== RESUMEN FINAL AGREGADO ===")

print(f"Registros 911_alcaldia_dia.csv: {tabla_incidentes.shape[0]:,}")

print("\nColumnas agregadas:")
print(tabla_incidentes.columns.tolist())

print("\nTotales por tipo:")
print(
    tabla_incidentes[columnas_incidentes]
    .sum()
)

print("\nDistribución hubo_inundacion:")
print(
    tabla_incidentes["hubo_inundacion"]
    .value_counts()
)

print("\nDistribución hubo_incidente_hidrico:")
print(
    tabla_incidentes["hubo_incidente_hidrico"]
    .value_counts()
)

print("\nNúmero de alcaldías:")
print(df_911_limpio["alcaldia"].nunique())

print("\nListado de alcaldías:")
print(sorted(df_911_limpio["alcaldia"].unique()))

print("\nFecha mínima:")
print(df_911_limpio["fecha"].min())

print("\nFecha máxima:")
print(df_911_limpio["fecha"].max())



df_911_limpio.to_csv(
    "911_limpio.csv",
    index=False
)

tabla_incidentes.to_csv(
    "911_alcaldia_dia.csv",
    index=False
)

print("\nArchivos generados correctamente:")
print("- 911_limpio.csv")
print("- 911_alcaldia_dia.csv")
