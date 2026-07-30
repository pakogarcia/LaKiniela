import streamlit as st
import requests
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Predicción LaLiga", layout="centered")

st.title("⚽ Predictor Inteligente LaLiga")
st.write("Selecciona los equipos y las cuotas para obtener la predicción.")

# Cargar equipos (desde el archivo que generó tu entrenamiento)
df = pd.read_csv('LaLiga_Dataset_Final.csv')
lista_equipos = sorted(df['HomeTeam'].dropna().unique().tolist())

# Crear la interfaz
col1, col2 = st.columns(2)
with col1:
    local = st.selectbox("🏠 Equipo Local", lista_equipos)
with col2:
    visitante = st.selectbox("✈️ Equipo Visitante", lista_equipos)

col3, col4, col5 = st.columns(3)
with col3:
    cuota_1 = st.number_input("Cuota Local (1)", value=2.0)
with col4:
    cuota_X = st.number_input("Cuota Empate (X)", value=3.5)
with col5:
    cuota_2 = st.number_input("Cuota Visitante (2)", value=3.0)

# Lógica para obtener ELO
def obtener_ultimo_elo(equipo):
    df_e = df[(df['HomeTeam'] == equipo) | (df['AwayTeam'] == equipo)]
    if not df_e.empty:
        fila = df_e.iloc[-1]
        return fila['elo_local'] if fila['HomeTeam'] == equipo else fila['elo_visitante']
    return 1.5

if st.button("🤖 Calcular Predicción"):
    datos = {
        "elo_local": float(obtener_ultimo_elo(local)),
        "elo_visitante": float(obtener_ultimo_elo(visitante)),
        "B365H": float(cuota_1),
        "B365D": float(cuota_X),
        "B365A": float(cuota_2)
    }
    
    # Consultar a la API (asegúrate de que esté corriendo)
    try:
        res = requests.post("http://127.0.0.1:8000/predecir", json=datos)
        pred = res.json()
        
        st.success("¡Predicción calculada!")
        
        st.subheader("🏆 Probabilidades 1X2")
        st.write(f"Local: **{pred['mercado_1X2']['Victoria_Local']}%**")
        st.write(f"Empate: **{pred['mercado_1X2']['Empate']}%**")
        st.write(f"Visitante: **{pred['mercado_1X2']['Victoria_Visitante']}%**")
        
        st.subheader("🥅 Mercado de Goles")
        st.write(f"Más de 2.5: **{pred['mercado_goles']['Mas_de_2.5']}%**")
        st.write(f"Menos de 2.5: **{pred['mercado_goles']['Menos_de_2.5']}%**")
        
    except:
        st.error("❌ No se pudo conectar a la API. ¿Está ejecutándose `uvicorn api_predicciones:app`?")