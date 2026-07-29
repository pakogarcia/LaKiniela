import requests
import pandas as pd
from datetime import datetime

# Configuración
API_URL = "http://clubelo.com/api/Elo"
ARCHIVO_ELO = "EloSP1.csv"
FECHA_INICIO = "2025-06-01"

def obtener_elo_api(equipo, fecha):
    # ClubElo a veces usa nombres ligeramente distintos (ej: Real Madrid vs Real Madrid CF)
    params = {'club': equipo, 'date': fecha}
    try:
        response = requests.get(API_URL, params=params)
        if response.status_code == 200:
            return response.json() # Retorna el valor ELO directo
        return None
    except:
        return None

# 1. Cargar tu archivo actual
df_elo = pd.read_csv(ARCHIVO_ELO, sep=';')
df_elo['date'] = pd.to_datetime(df_elo['date'], format="%d/%m/%Y")

# 2. Identificar qué equipos y qué fechas faltan
# Aquí puedes añadir la lógica para iterar desde 2025-06-01 hasta hoy
print("🚀 Conectando a la API de ClubElo para actualizar datos...")

# Ejemplo de uso:
# elo_actual = obtener_elo_api("Real Madrid", "2026-07-13")
# print(f"El ELO recuperado es: {elo_actual}")