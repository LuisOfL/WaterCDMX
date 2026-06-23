import pandas as pd
import unicodedata

print("=== INTEGRACIÓN DATASETS: NASA + 911 ===")



def normalizar_alcaldia(texto):
    if pd.isna(texto):
        return None

    texto = ''.join(
        c for c in unicodedata.normalize("NFKD", str(texto))
        if not unicodedata.combining(c)
    )

    return texto.strip().upper()



nasa = pd.read_csv(
    "s3://apps-proyecto/nasa_limpio.csv",
    parse_dates=["fecha"]
)

incidentes = pd.read_csv(
    "s3://apps-proyecto/911_alcaldia_dia.csv",
    parse_dates=["fecha"]
)

print("\nNASA limpio:")
print(nasa.shape)
print(nasa.columns.tolist())

print("\n911 agregado:")
print(incidentes.shape)
print(incidentes.columns.tolist())



nasa["alcaldia"] = nasa["alcaldia"].apply(normalizar_alcaldia)
incidentes["alcaldia"] = incidentes["alcaldia"].apply(normalizar_alcaldia)



columnas_no_clima = [
    "fecha",
    "lat",
    "lon",
    "alcaldia"
]

columnas_clima = [
    col for col in nasa.columns
    if col not in columnas_no_clima
]

print("\nColumnas climáticas usadas:")
print(columnas_clima)

clima_alcaldia_dia = (
    nasa
    .groupby(
        ["fecha", "alcaldia"],
        as_index=False
    )[columnas_clima]
    .mean()
)

print("\nNASA agrupado por fecha-alcaldía:")
print(clima_alcaldia_dia.shape)


dataset = clima_alcaldia_dia.merge(
    incidentes,
    on=["fecha", "alcaldia"],
    how="left"
)



columnas_incidentes = [
    "aguas_negras",
    "desborde_canal",
    "encharcamiento",
    "fuga_agua",
    "inundacion",
    "total_incidentes",
    "hubo_inundacion",
    "hubo_incidente_hidrico"
]

for col in columnas_incidentes:
    if col not in dataset.columns:
        dataset[col] = 0

dataset[columnas_incidentes] = (
    dataset[columnas_incidentes]
    .fillna(0)
)

for col in columnas_incidentes:
    dataset[col] = dataset[col].astype(int)


print("\n=== VALIDACIÓN DATASET INTEGRADO ===")

print("\nDimensiones finales:")
print(dataset.shape)

print("\nColumnas finales:")
print(dataset.columns.tolist())

print("\nDistribución hubo_inundacion:")
print(
    dataset["hubo_inundacion"]
    .value_counts()
)

print("\nDistribución hubo_incidente_hidrico:")
print(
    dataset["hubo_incidente_hidrico"]
    .value_counts()
)

print("\nTotales por tipo de incidente:")
print(
    dataset[
        [
            "aguas_negras",
            "desborde_canal",
            "encharcamiento",
            "fuga_agua",
            "inundacion"
        ]
    ].sum()
)

print("\nNulos finales:")
print(
    dataset
    .isna()
    .sum()
    .sort_values(ascending=False)
    .head(20)
)

print("\nFechas:")
print("Mínima:", dataset["fecha"].min())
print("Máxima:", dataset["fecha"].max())

print("\nAlcaldías:")
print(dataset["alcaldia"].nunique())
print(sorted(dataset["alcaldia"].unique()))



dataset.to_csv(
    "dataset_integrado1.csv",
    index=False
)

print("\nArchivo dataset_integrado.csv generado correctamente.")
