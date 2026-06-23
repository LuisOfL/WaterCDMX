import pandas as pd

df = pd.read_csv(
    "dataset_integrado.csv"
)


df["lluvia_intensa"] = (
    df["precip"] >= 5
).astype(int)

print("\n=== BALANCE GENERAL ===")
print(
    df["lluvia_intensa"]
    .value_counts()
)

print("\n=== PORCENTAJES ===")
print(
    (
        df["lluvia_intensa"]
        .value_counts(normalize=True)
        * 100
    ).round(2)
)

print("\n=== LLUVIA INTENSA POR ALCALDÍA ===")

print(
    df.groupby("alcaldia")["lluvia_intensa"]
      .mean()
      .sort_values(ascending=False)
      * 100
)
