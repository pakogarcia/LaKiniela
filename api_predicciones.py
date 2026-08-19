from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import joblib

app = FastAPI(title="Motor Predictivo LaLiga")

# Cargar los modelos pre-entrenados al arrancar el servidor
modelo_1x2 = joblib.load('modelo_1x2_xgboost.pkl')
modelo_goles = joblib.load('modelo_goles_rf.pkl')
modelo_btts = joblib.load('modelo_btts_rf.pkl')
modelo_corners = joblib.load('modelo_corners_rf.pkl')

class DatosPartido(BaseModel):
    elo_local: float
    elo_visitante: float
    B365H: float
    B365D: float
    B365A: float

@app.post("/predecir")
def predecir_partido(partido: DatosPartido):
    dif_elo = partido.elo_local - partido.elo_visitante
    
    # Aquí es donde empaquetamos los datos
    datos_entrada = pd.DataFrame([[
        partido.elo_local, partido.elo_visitante, dif_elo, 
        partido.B365H, partido.B365D, partido.B365A
    ]], columns=['elo_local', 'elo_visitante', 'dif_elo', 'B365H', 'B365D', 'B365A'])

    # Pasamos 'datos_entrada' a los 4 modelos
    probabilidades_1x2 = modelo_1x2.predict_proba(datos_entrada)[0]
    probabilidades_goles = modelo_goles.predict_proba(datos_entrada)[0]
    probabilidades_btts = modelo_btts.predict_proba(datos_entrada)[0]
    probabilidades_corners = modelo_corners.predict_proba(datos_entrada)[0]

    return {
        "mercado_1X2": {
            "Victoria_Local": float(round(probabilidades_1x2[2] * 100, 2)), 
            "Empate": float(round(probabilidades_1x2[1] * 100, 2)),         
            "Victoria_Visitante": float(round(probabilidades_1x2[0] * 100, 2)) 
        },
        "mercado_goles": {
            "Menos_de_2.5": float(round(probabilidades_goles[0] * 100, 2)),
            "Mas_de_2.5": float(round(probabilidades_goles[1] * 100, 2))
        },
        "mercado_btts": {
            "Ambos_Marcan_No": float(round(probabilidades_btts[0] * 100, 2)),
            "Ambos_Marcan_Si": float(round(probabilidades_btts[1] * 100, 2))
        },
        "mercado_corners": {
            "Menos_de_9.5": float(round(probabilidades_corners[0] * 100, 2)),
            "Mas_de_9.5": float(round(probabilidades_corners[1] * 100, 2))
        }
    }