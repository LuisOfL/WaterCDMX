import pandas as pd
import numpy as np
import joblib

from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

print("=== MODELO BASE: REGRESIÓN LOGÍSTICA - LLUVIA INTENSA ===")

df = pd.read_csv(
    "dataset_modelo_lluvia.csv",
    parse_dates=["fecha"]
)

df = df.sort_values("fecha")

print("\nDataset:")
print(df.shape)

# ==========================================
# VARIABLE OBJETIVO
# ==========================================

y = df["lluvia_intensa"]

print("\nDistribución objetivo:")
print(y.value_counts())
print(y.value_counts(normalize=True) * 100)

# ==========================================
# VARIABLES PREDICTORAS SIN FUGA
# NO usar precip del mismo día ni variables derivadas de precip actual
# ==========================================

features = [
    "alcaldia",

    "temp",
    "temp_max",
    "temp_min",
    "humedad",
    "viento",
    "viento_max",
    "radiacion",
    "presion",
    "humedad_especifica",
    "punto_rocio",
    "rango_temp",
    "depresion_punto_rocio",

    "mes",
    "trimestre",
    "dia_semana",
    "temporada_lluvias",

    "precip_1d",
    "precip_3d",
    "precip_7d",
    "precip_14d",
    "precip_30d",

    "llovio_ayer",
    "lluvia_intensa_ayer",
    "lluvia_acumulada_ponderada",

    "inundacion_1d",
    "inundacion_3d",
    "inundacion_7d",

    "encharcamiento_1d",
    "encharcamiento_3d",
    "encharcamiento_7d",

    "aguas_negras_1d",
    "aguas_negras_3d",
    "aguas_negras_7d",

    "fuga_agua_1d",
    "fuga_agua_3d",
    "fuga_agua_7d",

    "desborde_canal_1d",
    "desborde_canal_3d",
    "desborde_canal_7d",

    "total_incidentes_1d",
    "total_incidentes_3d",
    "total_incidentes_7d"
]

features = [
    col for col in features
    if col in df.columns
]

X = df[features]

print("\nVariables usadas:")
print(features)
print("\nTotal variables:", len(features))

# ==========================================
# DIVISIÓN TEMPORAL
# ==========================================

corte = int(len(df) * 0.80)

X_train = X.iloc[:corte]
X_test = X.iloc[corte:]

y_train = y.iloc[:corte]
y_test = y.iloc[corte:]

print("\n--- División temporal ---")
print("Train:", X_train.shape)
print("Test:", X_test.shape)

print("\nRango train:")
print(df["fecha"].iloc[:corte].min(), "a", df["fecha"].iloc[:corte].max())

print("\nRango test:")
print(df["fecha"].iloc[corte:].min(), "a", df["fecha"].iloc[corte:].max())

# ==========================================
# PREPROCESAMIENTO
# ==========================================

categoricas = ["alcaldia"]

numericas = [
    col for col in features
    if col not in categoricas
]

preprocesador = ColumnTransformer(
    transformers=[
        (
            "cat",
            OneHotEncoder(handle_unknown="ignore"),
            categoricas
        ),
        (
            "num",
            StandardScaler(),
            numericas
        )
    ]
)

# ==========================================
# MODELO
# ==========================================

modelo = Pipeline(
    steps=[
        ("preprocesador", preprocesador),
        (
            "clasificador",
            LogisticRegression(
                max_iter=3000,
                class_weight="balanced",
                random_state=42
            )
        )
    ]
)

modelo.fit(X_train, y_train)

# ==========================================
# PREDICCIONES
# ==========================================

y_prob = modelo.predict_proba(X_test)[:, 1]

# ==========================================
# BUSCAR MEJOR UMBRAL POR F1
# ==========================================

mejor_umbral = 0
mejor_f1 = 0

for umbral in np.arange(0.01, 1.00, 0.01):

    y_pred_temp = (
        y_prob >= umbral
    ).astype(int)

    f1 = f1_score(
        y_test,
        y_pred_temp
    )

    if f1 > mejor_f1:
        mejor_f1 = f1
        mejor_umbral = umbral

y_pred = (
    y_prob >= mejor_umbral
).astype(int)

print("\n========================")
print("MEJOR UMBRAL")
print("========================")
print("Umbral:", mejor_umbral)
print("Mejor F1:", mejor_f1)

# ==========================================
# MÉTRICAS
# ==========================================

print("\n=== MÉTRICAS ===")
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Precision:", precision_score(y_test, y_pred))
print("Recall:", recall_score(y_test, y_pred))
print("F1:", f1_score(y_test, y_pred))
print("ROC AUC:", roc_auc_score(y_test, y_prob))

print("\n=== MATRIZ DE CONFUSIÓN ===")
print(confusion_matrix(y_test, y_pred))

print("\n=== REPORTE ===")
print(classification_report(y_test, y_pred))

# ==========================================
# REPORTE COMPLETO DE PREDICCIONES
# ==========================================

print("\nGenerando reporte completo de predicciones...")

y_prob_total = modelo.predict_proba(X)[:, 1]

y_pred_total = (
    y_prob_total >= mejor_umbral
).astype(int)

reporte_completo = pd.DataFrame({
    "fecha": df["fecha"],
    "alcaldia": df["alcaldia"],
    "probabilidad_lluvia_intensa": y_prob_total,
    "prediccion_lluvia_intensa": y_pred_total,
    "valor_real": y
})

reporte_completo["riesgo"] = pd.cut(
    reporte_completo["probabilidad_lluvia_intensa"],
    bins=[0, 0.33, 0.66, 1],
    labels=["BAJO", "MEDIO", "ALTO"],
    include_lowest=True
)

reporte_completo = reporte_completo.sort_values(
    ["fecha", "alcaldia"]
)

reporte_completo.to_csv(
    "predicciones_regresion_logistica_lluvia.csv",
    index=False
)

print(
    "\nArchivo predicciones_regresion_logistica_lluvia.csv generado correctamente."
)

print("\nDistribución de riesgo:")
print(
    reporte_completo["riesgo"]
    .value_counts()
)