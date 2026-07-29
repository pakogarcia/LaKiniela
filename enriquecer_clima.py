import pandas as pd
import requests
import time
import os

def cargar_diccionario_coordenadas(ruta_archivo="coordenadas_equipos.csv"):
    try:
        df_coords = pd.read_csv(ruta_archivo, sep=",")
        return df_coords.set_index('Equipo')[['Latitud', 'Longitud']].apply(tuple, axis=1).to_dict()
    except FileNotFoundError:
        print(f"❌ Error: Falta el archivo '{ruta_archivo}'.")
        exit()

def consultar_clima(lat, lon, fecha_str, reintentos=3):
    for intento in range(reintentos):
        try:
            fecha_dt = pd.to_datetime(fecha_str, format="%d/%m/%Y")
            fecha_api = fecha_dt.strftime("%Y-%m-%d")
            
            url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={fecha_api}&end_date={fecha_api}&daily=temperature_2m_max,precipitation_sum,wind_speed_10m_max&timezone=Europe/Madrid"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                datos = response.json()
                if 'daily' in datos and datos['daily']['temperature_2m_max']:
                    return datos['daily']['temperature_2m_max'][0], datos['daily']['precipitation_sum'][0], datos['daily']['wind_speed_10m_max'][0]
            elif response.status_code == 429:
                print("\n🛑 ¡Límite de API alcanzado para esta IP! Activa la VPN y reinicia el script.")
                return "LIMIT", "LIMIT", "LIMIT"
        except Exception:
            time.sleep(1) # Espera un segundo antes de reintentar
            pass
    return None, None, None

COORDENADAS_EQUIPOS = cargar_diccionario_coordenadas()

# LÓGICA DE CONTINUIDAD
archivo_salida = "SP1_con_clima.csv"
if os.path.exists(archivo_salida):
    print(f"🔄 Detectado archivo previo '{archivo_salida}'. Reanudando progreso...")
    df = pd.read_csv(archivo_salida, sep=",")
    # Asegurar que las columnas existan
    for col in ['temp_max', 'lluvia_mm', 'viento_kmh']:
        if col not in df.columns:
            df[col] = None
else:
    print("🆕 Iniciando descarga desde cero...")
    df = pd.read_csv("SP1_total.csv", sep=";")
    df['temp_max'] = None
    df['lluvia_mm'] = None
    df['viento_kmh'] = None

# Contamos cuántas filas faltan realmente
filas_vacias = df['temp_max'].isna().sum()
print(f"📊 Partidos totales en base de datos: {len(df)} | Faltan por procesar: {filas_vacias}")

if filas_vacias == 0:
    print("✅ ¡Todos los partidos ya tienen sus datos climáticos!")
    exit()

print("🚀 Procesando... Guarda automáticamente cada 100 partidos.")

# Bucle de extracción optimizado
for idx, row in df.iterrows():
    # Si la celda ya tiene datos válidos, nos la saltamos
    if pd.notna(row['temp_max']) and row['temp_max'] != "LIMIT" and row['temp_max'] != "":
        continue
        
    equipo_local = row['HomeTeam']
    fecha = row['Date']
    
    if equipo_local in COORDENADAS_EQUIPOS:
        lat, lon = COORDENADAS_EQUIPOS[equipo_local]
        temp, lluv, vien = consultar_clima(lat, lon, fecha)
        
        if temp == "LIMIT":
            df.to_csv(archivo_salida, sep=",", index=False)
            exit()
            
        # Si aun así fallara tras los reintentos, ponemos un valor por defecto o 0 para que avance y no se quede en bucle infinito
        df.at[idx, 'temp_max'] = temp if temp is not None else 0.0
        df.at[idx, 'lluvia_mm'] = lluv if lluv is not None else 0.0
        df.at[idx, 'viento_kmh'] = vien if vien is not None else 0.0
    else:
        # Por si hay algún equipo no encontrado
        df.at[idx, 'temp_max'] = 0.0
        df.at[idx, 'lluvia_mm'] = 0.0
        df.at[idx, 'viento_kmh'] = 0.0
    
    time.sleep(0.05)
    
    # Auto-guardado de seguridad cada 100 filas
    if idx % 100 == 0 and idx > 0:
        df.to_csv(archivo_salida, sep=",", index=False)
        print(f"💾 Progreso guardado. Fila {idx}/{len(df)}...")

# Guardado final
df.to_csv(archivo_salida, sep=",", index=False)
print(f"🎉 ¡Completado con éxito! El archivo final está listo en '{archivo_salida}'")