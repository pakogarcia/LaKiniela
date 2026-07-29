import pandas as pd

# 1. Cargar tu archivo maestro con los datos mezclados
# (Asegúrate de poner el separador correcto, suele ser ';' o ',')
df = pd.read_csv("SP1_total.csv", sep=";")

# 2. Definir tu lista oficial de 32 columnas limpias
columnas_limpias = [
    'Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 
    'HTHG', 'HTAG', 'HTR', 'HS', 'AS', 'HST', 'AST', 'HF', 'AF', 
    'HC', 'AC', 'HY', 'AY', 'HR', 'AR', 'B365H', 'B365D', 'B365A', 
    'BbAvH', 'BbAvD', 'BbAvA', 'BbAv>2.5', 'BbAv<2.5', 'BbAvAHH', 'BbAvAHA'
]

# 3. Filtrar el dataset para que solo se quede con las que queremos
df_limpio = df[columnas_limpias]

# 4. Sobrescribir el archivo ya limpio
df_limpio.to_csv("SP1_total.csv", index=False, sep=";")

print("¡Listo! Las columnas intrusas han sido eliminadas.")