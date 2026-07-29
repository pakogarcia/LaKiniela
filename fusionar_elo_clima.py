import pandas as pd

print("⏳ Iniciando la fusión de Datos: Clima + Elo...")

# 1. Cargar el dataset que está generando tu script de clima (Separado por comas)
try:
    df_clima = pd.read_csv("SP1_con_clima.csv", sep=",")
    print(f"✅ Dataset de clima cargado: {len(df_clima)} partidos.")
except FileNotFoundError:
    print("❌ Error: Todavía no ha terminado el script de clima o no encuentra 'SP1_con_clima.csv'")
    exit()

# 2. Cargar el dataset de Elo (Separado por punto y coma)
try:
    df_elo = pd.read_csv("EloSP1.csv", sep=";")
    print(f"✅ Dataset de Elo cargado: {len(df_elo)} registros históricos.")
except FileNotFoundError:
    print("❌ Error: No se encuentra el archivo 'EloSP1.csv' en la carpeta.")
    exit()

# 3. Estandarizar formatos de fecha para que coincidan perfectamente
df_clima['Date'] = pd.to_datetime(df_clima['Date'], format="%d/%m/%Y")
df_elo['date'] = pd.to_datetime(df_elo['date'], format="%d/%m/%Y")

# 4. Crear columnas nuevas en nuestro dataset principal para el Elo
df_clima['elo_local'] = None
df_clima['elo_visitante'] = None

print("🔄 Cruzando datos partido a partido (esto será rápido)...")

# Convertimos el dataframe de elo en un diccionario indexado por (fecha, club) 
# Esto hace que la búsqueda pase de tardar minutos a tardar solo un par de segundos
diccionario_elo = df_elo.set_index(['date', 'club'])['elo'].to_dict()

# 5. Bucle para asignar el Elo correspondiente a cada partido
for idx, row in df_clima.iterrows():
    fecha = row['Date']
    local = row['HomeTeam']
    visitante = row['AwayTeam']
    
    # Buscamos el Elo de ambos equipos en esa fecha exacta
    elo_h = diccionario_elo.get((fecha, local))
    elo_a = diccionario_elo.get((fecha, visitante))
    
    # Nota de analista: Tu archivo de Elo divide por 100 para tener el formato estándar (ej: 1750.32)
    if elo_h is not None:
        df_clima.at[idx, 'elo_local'] = elo_h / 100.0
    if elo_a is not None:
        df_clima.at[idx, 'elo_visitante'] = elo_a / 100.0

# 6. Calcular la diferencia de Elo (métrica clave para el modelo predictivo)
# Convertimos a numérico por seguridad antes de restar
df_clima['elo_local'] = pd.to_numeric(df_clima['elo_local'])
df_clima['elo_visitante'] = pd.to_numeric(df_clima['elo_visitante'])
df_clima['dif_elo'] = df_clima['elo_local'] - df_clima['elo_visitante']

# 7. Formatear la fecha de vuelta a su estado original por comodidad visual
df_clima['Date'] = df_clima['Date'].dt.strftime("%d/%m/%Y")

# 8. Guardar el Santo Grial: El dataset definitivo para tu Master
archivo_final = "LaLiga_Dataset_Final.csv"
df_clima.to_csv(archivo_final, sep=",", index=False)

print("\n" + "="*50)
print(f"🎉 ¡FUSIÓN COMPLETADA CON ÉXITO!")
print(f"📁 Tu dataset definitivo se ha guardado como '{archivo_final}'")
print(f"📊 Dimensiones finales: {df_clima.shape[0]} filas y {df_clima.shape[1]} columnas.")
print("="*50)