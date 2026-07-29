import pandas as pd

# Cargar archivos
df_primera = pd.read_csv("SP1_total.csv", sep=";")
df_segunda = pd.read_csv("SP2_total.csv", sep=";")

# Unir ambos datasets alineando automáticamente las columnas
df_total = pd.concat([df_primera, df_segunda], ignore_index=True)

# Guardar el resultado unificado
df_total.to_csv("SP_total.csv", index=False, sep=";")