import os
import sys
import glob
import json
import time
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
import xgboost as xgb
import joblib

try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

load_dotenv()

def log_header(titulo):
    print("\n" + "="*60)
    print(f"  {titulo}")
    print("="*60)

def cargar_mapeo():
    if os.path.exists('mapeo_equipos.json'):
        with open('mapeo_equipos.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

MAPEO_EQUIPOS = cargar_mapeo()

def normalizar_nombre(nombre_raw):
    if not nombre_raw or pd.isna(nombre_raw):
        return ""
    nombre = str(nombre_raw).strip()
    if nombre in MAPEO_EQUIPOS:
        return MAPEO_EQUIPOS[nombre]
    
    nombre_limpio = nombre
    for prefijo in ["FC ", "CD ", "UD ", "SD ", "RC ", "RCD ", "CF ", "AD ", "CE ", "CA "]:
        if nombre_limpio.startswith(prefijo):
            nombre_limpio = nombre_limpio[len(prefijo):].strip()
    for sufijo in [" CF", " FC", " CD", " UD", " SD", " SAD", " Seville", " San Sebastian", " San Sebastián", " Barcelona", " Madrid"]:
        if nombre_limpio.endswith(sufijo):
            nombre_limpio = nombre_limpio[:-len(sufijo)].strip()
            
    return MAPEO_EQUIPOS.get(nombre_limpio, nombre)

def paso_1_descargar_temporada_actual():
    log_header("[1/5] Descargando resultados de la temporada actual (Football-Data)")
    fuentes = [
        ("SP1", "https://www.football-data.co.uk/mmz4281/2526/SP1.csv", "SP1/SP1_2026.csv"),
        ("SP2", "https://www.football-data.co.uk/mmz4281/2526/SP2.csv", "SP2/SP2_2026.csv")
    ]
    headers = {'User-Agent': 'Mozilla/5.0'}
    for div, url, destino in fuentes:
        try:
            print(f"📥 Descargando {div} desde {url}...")
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200 and len(res.text) > 500:
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                with open(destino, 'w', encoding='utf-8') as f:
                    f.write(res.text)
                print(f"✅ {div} actualizado correctamente en '{destino}'.")
            else:
                print(f"⚠️ No se pudo descargar {div} (Status {res.status_code}). Se conserva archivo local.")
        except Exception as e:
            print(f"⚠️ Error al conectar con Football-Data para {div}: {e}")

def paso_2_unificar_historicos():
    log_header("[2/5] Consolidando y limpiando historicos (SP1_total y SP2_total)")
    columnas_oficiales = [
        'Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 
        'HTHG', 'HTAG', 'HTR', 'HS', 'AS', 'HST', 'AST', 'HF', 'AF', 
        'HC', 'AC', 'HY', 'AY', 'HR', 'AR', 'B365H', 'B365D', 'B365A', 
        'BbAvH', 'BbAvD', 'BbAvA', 'BbAv>2.5', 'BbAv<2.5', 'BbAvAHH', 'BbAvAHA'
    ]
    def procesar_carpeta(carpeta, archivo_salida):
        archivos = sorted(glob.glob(os.path.join(carpeta, "*.csv")))
        dfs = []
        for arch in archivos:
            if os.path.basename(arch).endswith('_total.csv'):
                continue
            try:
                df_temp = pd.read_csv(arch, sep=None, engine='python', encoding='utf-8-sig', on_bad_lines='skip')
                df_temp.columns = [str(c).strip().replace('\ufeff', '') for c in df_temp.columns]
                cols_validas = [c for c in columnas_oficiales if c in df_temp.columns]
                if 'HomeTeam' in df_temp.columns and 'AwayTeam' in df_temp.columns:
                    df_temp = df_temp[cols_validas]
                    dfs.append(df_temp)
            except Exception as e:
                print(f"⚠️ Aviso leyendo {arch}: {e}")
                
        if dfs:
            df_concatenado = pd.concat(dfs, ignore_index=True)
            df_concatenado['HomeTeam'] = df_concatenado['HomeTeam'].apply(normalizar_nombre)
            df_concatenado['AwayTeam'] = df_concatenado['AwayTeam'].apply(normalizar_nombre)
            df_concatenado = df_concatenado.dropna(subset=['HomeTeam', 'AwayTeam', 'Date'])
            df_concatenado.to_csv(archivo_salida, sep=';', index=False)
            print(f"✅ {archivo_salida} generado con {len(df_concatenado)} partidos procesados.")
            return df_concatenado
        return pd.DataFrame()

    df_sp1 = procesar_carpeta('SP1', 'SP1_total.csv')
    df_sp2 = procesar_carpeta('SP2', 'SP2_total.csv')
    if not df_sp2.empty:
        df_sp2.to_csv('SP2/SP2_total.csv', sep=';', index=False)

def paso_3_enriquecer_clima():
    log_header("[3/5] Enriqueciendo datos climaticos (Open-Meteo incremental)")
    try:
        df_coords = pd.read_csv('coordenadas_equipos.csv', sep=',')
        coords_dict = df_coords.set_index('Equipo')[['Latitud', 'Longitud']].apply(tuple, axis=1).to_dict()
    except Exception as e:
        print(f"⚠️ Error cargando 'coordenadas_equipos.csv': {e}. Saltando clima...")
        return

    archivo_clima = 'SP1_con_clima.csv'
    if os.path.exists(archivo_clima):
        df_clima = pd.read_csv(archivo_clima, sep=',')
    else:
        df_clima = pd.read_csv('SP1_total.csv', sep=';')
        for col in ['temp_max', 'lluvia_mm', 'viento_kmh']:
            df_clima[col] = None

    df_sp1 = pd.read_csv('SP1_total.csv', sep=';')
    if len(df_sp1) > len(df_clima):
        filas_nuevas = df_sp1.iloc[len(df_clima):].copy()
        for col in ['temp_max', 'lluvia_mm', 'viento_kmh']:
            filas_nuevas[col] = None
        df_clima = pd.concat([df_clima, filas_nuevas], ignore_index=True)

    faltantes = df_clima['temp_max'].isna().sum()
    print(f"📊 Partidos totales: {len(df_clima)} | Partidos sin clima: {faltantes}")
    
    if faltantes > 0:
        def consultar_api_clima(lat, lon, fecha_str):
            try:
                fecha_dt = pd.to_datetime(fecha_str, dayfirst=True)
                fecha_api = fecha_dt.strftime("%Y-%m-%d")
                url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={fecha_api}&end_date={fecha_api}&daily=temperature_2m_max,precipitation_sum,wind_speed_10m_max&timezone=Europe/Madrid"
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    d = r.json()
                    if 'daily' in d and d['daily']['temperature_2m_max']:
                        return d['daily']['temperature_2m_max'][0], d['daily']['precipitation_sum'][0], d['daily']['wind_speed_10m_max'][0]
            except Exception:
                pass
            return 18.0, 0.0, 10.0
            
        contador = 0
        for idx, row in df_clima.iterrows():
            if pd.isna(row['temp_max']) or row['temp_max'] == '':
                eq = row['HomeTeam']
                fecha = row['Date']
                if eq in coords_dict:
                    lat, lon = coords_dict[eq]
                    t, ll, v = consultar_api_clima(lat, lon, fecha)
                    df_clima.at[idx, 'temp_max'] = t
                    df_clima.at[idx, 'lluvia_mm'] = ll
                    df_clima.at[idx, 'viento_kmh'] = v
                else:
                    df_clima.at[idx, 'temp_max'] = 18.0
                    df_clima.at[idx, 'lluvia_mm'] = 0.0
                    df_clima.at[idx, 'viento_kmh'] = 10.0
                contador += 1
                time.sleep(0.05)
                if contador % 50 == 0:
                    print(f"   - Procesados {contador}/{faltantes} partidos nuevos...")
                    
        print(f"✅ {contador} partidos nuevos enriquecidos con clima.")
    else:
        print("✅ Todos los partidos ya cuentan con variables meteorologicas.")
        
    df_clima.to_csv(archivo_clima, sep=',', index=False)

def paso_4_fusion_y_reentrenamiento():
    log_header("[4/5] Fusion de datos y reentrenamiento de modelos de IA")
    
    df_clima = pd.read_csv('SP1_con_clima.csv', sep=',')
    df_elo = pd.read_csv('EloSP1.csv', sep=';').dropna(subset=['date', 'club'])
    
    df_clima['Date'] = pd.to_datetime(df_clima['Date'], dayfirst=True, errors='coerce')
    df_clima = df_clima.dropna(subset=['Date']).sort_values('Date')
    
    df_elo['date'] = pd.to_datetime(df_elo['date'], dayfirst=True, errors='coerce')
    df_elo = df_elo.dropna(subset=['date']).sort_values('date')
    
    df_elo['club'] = df_elo['club'].apply(normalizar_nombre)
    
    df_final = pd.merge_asof(
        df_clima,
        df_elo[['date', 'club', 'elo']].rename(columns={'elo': 'elo_local'}),
        left_on='Date', right_on='date', left_by='HomeTeam', right_by='club',
        direction='backward'
    ).drop(columns=['date', 'club'], errors='ignore')
    
    df_final = pd.merge_asof(
        df_final,
        df_elo[['date', 'club', 'elo']].rename(columns={'elo': 'elo_visitante'}),
        left_on='Date', right_on='date', left_by='AwayTeam', right_by='club',
        direction='backward'
    ).drop(columns=['date', 'club'], errors='ignore')
    
    media_elo = df_final['elo_local'].dropna().mean()
    if pd.isna(media_elo): media_elo = 160000.0
    
    df_final['elo_local'] = df_final['elo_local'].fillna(media_elo)
    df_final['elo_visitante'] = df_final['elo_visitante'].fillna(media_elo)
    
    if df_final['elo_local'].mean() > 5000:
        df_final['elo_local'] = df_final['elo_local'] / 100.0
        df_final['elo_visitante'] = df_final['elo_visitante'] / 100.0
        
    df_final['dif_elo'] = df_final['elo_local'] - df_final['elo_visitante']
    
    df_final_guardar = df_final.copy()
    df_final_guardar['Date'] = df_final_guardar['Date'].dt.strftime("%d/%m/%Y")
    df_final_guardar.to_csv('LaLiga_Dataset_Final.csv', sep=',', index=False)
    print(f"✅ Dataset maestro guardado en 'LaLiga_Dataset_Final.csv' con {len(df_final_guardar)} partidos.")
    
    df_ml = df_final.dropna(subset=['elo_local', 'elo_visitante', 'FTR']).copy()
    df_ml['Over_2_5'] = np.where((df_ml['FTHG'] + df_ml['FTAG']) > 2.5, 1, 0)
    df_ml['BTTS'] = np.where((df_ml['FTHG'] > 0) & (df_ml['FTAG'] > 0), 1, 0)
    
    cols = ['elo_local', 'elo_visitante', 'dif_elo', 'B365H', 'B365D', 'B365A', 'FTR', 'Over_2_5', 'BTTS']
    df_ml = df_ml[[c for c in cols if c in df_ml.columns]].dropna()
    
    X = df_ml[['elo_local', 'elo_visitante', 'dif_elo', 'B365H', 'B365D', 'B365A']]
    y_1x2 = df_ml['FTR']
    y_goles = df_ml['Over_2_5']
    y_btts = df_ml['BTTS']
    
    le = LabelEncoder()
    y_1x2_enc = le.fit_transform(y_1x2)
    pesos = compute_sample_weight(class_weight='balanced', y=y_1x2_enc)
    
    modelo_xgb = xgb.XGBClassifier(
        objective='multi:softprob',
        num_class=3, n_estimators=150, learning_rate=0.05, max_depth=4, random_state=42
    )
    modelo_xgb.fit(X, y_1x2_enc, sample_weight=pesos)
    
    modelo_rf = RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42)
    modelo_rf.fit(X, y_goles)
    
    modelo_btts = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)
    modelo_btts.fit(X, y_btts)

    # 4. Random Forest Córners (> 9.5)
    df_corners = df_final.dropna(subset=['elo_local', 'elo_visitante', 'HC', 'AC', 'B365H', 'B365D', 'B365A']).copy()
    df_corners['Over_9_5_Corners'] = np.where((df_corners['HC'] + df_corners['AC']) > 9.5, 1, 0)
    X_corners = df_corners[['elo_local', 'elo_visitante', 'dif_elo', 'B365H', 'B365D', 'B365A']]
    y_corners = df_corners['Over_9_5_Corners']

    modelo_corners = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)
    modelo_corners.fit(X_corners, y_corners)
    
    joblib.dump(modelo_xgb, 'modelo_1x2_xgboost.pkl')
    joblib.dump(modelo_rf, 'modelo_goles_rf.pkl')
    joblib.dump(modelo_btts, 'modelo_btts_rf.pkl')
    joblib.dump(modelo_corners, 'modelo_corners_rf.pkl')
    joblib.dump(le, 'label_encoder.pkl')
    
    print("🏆 ¡Modelos de Inteligencia Artificial (1X2, Goles, BTTS y Córners) reentrenados y serializados!")

def paso_5_descargar_proxima_jornada():
    log_header("[5/5] Descargando cuotas live de Bet365 para la proxima jornada")
    from descargar_cuotas_live import descargar_jornada_odds_io
    descargar_jornada_odds_io()

def main():
    inicio = time.time()
    print("🚀 INICIANDO ACTUALIZACIÓN AUTOMÁTICA DEL SISTEMA LAKINIELA...")
    
    paso_1_descargar_temporada_actual()
    paso_2_unificar_historicos()
    paso_3_enriquecer_clima()
    paso_4_fusion_y_reentrenamiento()
    paso_5_descargar_proxima_jornada()
    
    duracion = time.time() - inicio
    log_header(f"🎉 ¡TODO EL SISTEMA SE HA ACTUALIZADO CON ÉXITO EN {duracion:.1f}s!")

if __name__ == '__main__':
    main()
