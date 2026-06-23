import pandas as pd
import numpy as np

print("=== FEATURE ENGINEERING V2: LLUVIA INTENSA ===")



df = pd.read_csv(
    "s3://apps-proyecto/dataset_integrado.csv",
    parse_dates=["fecha"]
)

df = df.sort_values(
    ["alcaldia", "fecha"]
)

print("\nDataset inicial:")
print(df.shape)
print(df.columns.tolist())


if (
    "temp_max" in df.columns
    and "temp_min" in df.columns
):

    df["rango_temp"] = (
        df["temp_max"]
        - df["temp_min"]
    )

if (
    "temp" in df.columns
    and "punto_rocio" in df.columns
):

    df["depresion_punto_rocio"] = (
        df["temp"]
        - df["punto_rocio"]
    )

if (
    "precip" in df.columns
    and "humedad_especifica" in df.columns
):

    df["precip_x_humedad_especifica"] = (
        df["precip"]
        * df["humedad_especifica"]
    )

if (
    "precip" in df.columns
    and "punto_rocio" in df.columns
):

    df["precip_x_punto_rocio"] = (
        df["precip"]
        * df["punto_rocio"]
    )

if (
    "precip" in df.columns
    and "viento_max" in df.columns
):

    df["precip_x_viento_max"] = (
        df["precip"]
        * df["viento_max"]
    )




df["lluvia_intensa"] = (
    df["precip"] >= 5
).astype(int)

print("\nDistribución lluvia_intensa:")
print(df["lluvia_intensa"].value_counts())
print(df["lluvia_intensa"].value_counts(normalize=True) * 100)


df["mes"] = df["fecha"].dt.month
df["trimestre"] = df["fecha"].dt.quarter
df["dia_semana"] = df["fecha"].dt.dayofweek

df["temporada_lluvias"] = (
    df["mes"].isin([6, 7, 8, 9, 10])
).astype(int)


ventanas_precip = [1, 3, 7, 14, 30]

for ventana in ventanas_precip:

    if ventana == 1:
        df["precip_1d"] = (
            df.groupby("alcaldia")["precip"]
              .shift(1)
        )
    else:
        df[f"precip_{ventana}d"] = (
            df.groupby("alcaldia")["precip"]
              .transform(
                  lambda x:
                  x.shift(1)
                   .rolling(
                       ventana,
                       min_periods=1
                   )
                   .sum()
              )
        )


variables_incidentes = [
    "inundacion",
    "encharcamiento",
    "aguas_negras",
    "fuga_agua",
    "desborde_canal",
    "total_incidentes"
]

variables_incidentes = [
    var for var in variables_incidentes
    if var in df.columns
]

for var in variables_incidentes:

    df[f"{var}_1d"] = (
        df.groupby("alcaldia")[var]
          .shift(1)
    )

    df[f"{var}_3d"] = (
        df.groupby("alcaldia")[var]
          .transform(
              lambda x:
              x.shift(1)
               .rolling(
                   3,
                   min_periods=1
               )
               .sum()
          )
    )

    df[f"{var}_7d"] = (
        df.groupby("alcaldia")[var]
          .transform(
              lambda x:
              x.shift(1)
               .rolling(
                   7,
                   min_periods=1
               )
               .sum()
          )
    )



if "temp_max" in df.columns and "temp_min" in df.columns:
    df["rango_temp"] = df["temp_max"] - df["temp_min"]

if "temp" in df.columns and "punto_rocio" in df.columns:
    df["depresion_punto_rocio"] = df["temp"] - df["punto_rocio"]

if "precip" in df.columns and "humedad" in df.columns:
    df["precip_x_humedad"] = df["precip"] * df["humedad"]

if "precip_7d" in df.columns and "humedad" in df.columns:
    df["precip7_x_humedad"] = df["precip_7d"] * df["humedad"]

if "precip" in df.columns and "humedad_especifica" in df.columns:
    df["precip_x_humedad_especifica"] = (
        df["precip"] * df["humedad_especifica"]
    )

if "precip_7d" in df.columns and "humedad_especifica" in df.columns:
    df["precip7_x_humedad_especifica"] = (
        df["precip_7d"] * df["humedad_especifica"]
    )

if "precip" in df.columns and "punto_rocio" in df.columns:
    df["precip_x_punto_rocio"] = (
        df["precip"] * df["punto_rocio"]
    )

if "precip_7d" in df.columns and "punto_rocio" in df.columns:
    df["precip7_x_punto_rocio"] = (
        df["precip_7d"] * df["punto_rocio"]
    )

if "precip" in df.columns and "viento_max" in df.columns:
    df["precip_x_viento_max"] = (
        df["precip"] * df["viento_max"]
    )


df["llovio_ayer"] = (
    df["precip_1d"] >= 1
).astype(int)

df["lluvia_intensa_ayer"] = (
    df["precip_1d"] >= 5
).astype(int)

df["lluvia_acumulada_ponderada"] = (
    0.50 * df["precip_1d"].fillna(0)
    + 0.30 * (df["precip_3d"].fillna(0) / 3)
    + 0.20 * (df["precip_7d"].fillna(0) / 7)
)


columnas_log = [
    "precip",
    "precip_1d",
    "precip_3d",
    "precip_7d",
    "precip_14d",
    "precip_30d",
    "lluvia_acumulada_ponderada"
]

columnas_log = [
    col for col in columnas_log
    if col in df.columns
]

for col in columnas_log:
    df[f"{col}_log"] = np.log1p(
        df[col].fillna(0)
    )

df = df.fillna(0)


print("\nDataset final:")
print(df.shape)

print("\nDistribución final lluvia_intensa:")
print(df["lluvia_intensa"].value_counts())
print(df["lluvia_intensa"].value_counts(normalize=True) * 100)

print("\nNulos finales:")
print(
    df.isna()
      .sum()
      .sort_values(ascending=False)
      .head(20)
)

print("\nColumnas finales:")
print(df.columns.tolist())


df.to_csv(
    "dataset_modelo_lluvia1.csv",
    index=False
)

print("\nArchivo dataset_modelo_lluvia.csv generado correctamente.")
