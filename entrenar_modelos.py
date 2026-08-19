import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
import xgboost as xgb
import joblib
import warnings
warnings.filterwarnings('ignore')

print(" Iniciando procesamiento de datos...")

# 1. Cargar datos desde la misma carpeta
df_clima = pd.read_csv('SP1_con_clima.csv', sep=',')
df_elo = pd.read_csv('EloSP1.csv', sep=';').dropna(subset=['date', 'club'])

# 2. Formatear fechas y ordenar
df_clima['Date'] = pd.to_datetime(df_clima['Date'], dayfirst=True, errors='coerce')
df_clima = df_clima.dropna(subset=['Date']).sort_values('Date')
df_elo['date'] = pd.to_datetime(df_elo['date'], dayfirst=True, errors='coerce')
df_elo = df_elo.dropna(subset=['date']).sort_values('date')

# 3. Cruzar datos (Merge asof)
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

# 4. Calcular métricas
media_elo = df_final['elo_local'].dropna().mean()
if pd.isna(media_elo): media_elo = 160000.0
df_final['elo_local'] = df_final['elo_local'].fillna(media_elo)
df_final['elo_visitante'] = df_final['elo_visitante'].fillna(media_elo)

if df_final['elo_local'].mean() > 5000:
    df_final['elo_local'] = df_final['elo_local'] / 100.0
    df_final['elo_visitante'] = df_final['elo_visitante'] / 100.0

df_final['dif_elo'] = df_final['elo_local'] - df_final['elo_visitante']

# Guardar dataset final para la interfaz de usuario
df_final['Date'] = df_final['Date'].dt.strftime("%d/%m/%Y")
df_final.to_csv('LaLiga_Dataset_Final.csv', sep=",", index=False)
print("✅ Datos limpios guardados. Entrenando modelos...")

# 5. Preparar Machine Learning
df_ml = df_final.dropna(subset=['elo_local', 'elo_visitante', 'FTR']).copy()

# Variables objetivo de goles y córners
df_ml['Over_2_5'] = np.where((df_ml['FTHG'] + df_ml['FTAG']) > 2.5, 1, 0)
df_ml['BTTS'] = np.where((df_ml['FTHG'] > 0) & (df_ml['FTAG'] > 0), 1, 0)

# Columnas a conservar
cols = ['elo_local', 'elo_visitante', 'dif_elo', 'B365H', 'B365D', 'B365A', 'FTR', 'Over_2_5', 'BTTS']
df_ml_clean = df_ml[cols].dropna()

# Definir variables de entrada (X) y salidas (y)
X = df_ml_clean[['elo_local', 'elo_visitante', 'dif_elo', 'B365H', 'B365D', 'B365A']]
y_1x2 = df_ml_clean['FTR']
y_goles = df_ml_clean['Over_2_5']
y_btts = df_ml_clean['BTTS']

# Entrenar XGBoost (1X2)
le = LabelEncoder()
y_1x2_encoded = le.fit_transform(y_1x2)
pesos = compute_sample_weight(class_weight='balanced', y=y_1x2_encoded)

modelo_xgb = xgb.XGBClassifier(
    objective='multi:softprob',
    num_class=3, n_estimators=150, learning_rate=0.05, max_depth=4, random_state=42
)
modelo_xgb.fit(X, y_1x2_encoded, sample_weight=pesos)

# Entrenar Random Forest (Goles > 2.5)
modelo_rf = RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42)
modelo_rf.fit(X, y_goles)

# Entrenar Random Forest (BTTS - Ambos Marcan)
modelo_btts = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)
modelo_btts.fit(X, y_btts)

# Entrenar Random Forest (Córners > 9.5)
df_corners = df_final.dropna(subset=['elo_local', 'elo_visitante', 'HC', 'AC', 'B365H', 'B365D', 'B365A']).copy()
df_corners['Over_9_5_Corners'] = np.where((df_corners['HC'] + df_corners['AC']) > 9.5, 1, 0)
X_corners = df_corners[['elo_local', 'elo_visitante', 'dif_elo', 'B365H', 'B365D', 'B365A']]
y_corners = df_corners['Over_9_5_Corners']

modelo_corners = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)
modelo_corners.fit(X_corners, y_corners)

# 6. Guardar Modelos
joblib.dump(modelo_xgb, 'modelo_1x2_xgboost.pkl')
joblib.dump(modelo_rf, 'modelo_goles_rf.pkl')
joblib.dump(modelo_btts, 'modelo_btts_rf.pkl')
joblib.dump(modelo_corners, 'modelo_corners_rf.pkl')
joblib.dump(le, 'label_encoder.pkl')

print("🏆 ¡Modelos entrenados y guardados con éxito (1X2, Goles, BTTS y Córners)!")