import streamlit as st
import pandas as pd
import requests
import json
import os
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="LaKiniela - Trading & IA", page_icon="⚽", layout="wide")

# ==========================================
# BARRA LATERAL (AJUSTES)
# ==========================================
st.sidebar.header("⚙️ Ajustes del Radar")
st.sidebar.markdown("Define los filtros para descartar apuestas improbables.")
umbral_prob = st.sidebar.slider(
    "Probabilidad Mínima IA (%)", 
    min_value=10.0, 
    max_value=60.0, 
    value=35.0, 
    step=1.0,
    help="Solo se mostrarán Value Bets si la IA cree que el resultado tiene al menos este % de opciones de ocurrir."
)
st.sidebar.markdown("---")

st.title("⚽ LaKiniela: Panel de Analítica y Predicción")
st.markdown("---")

# ==========================================
# 1. CARGA EXTERNA DEL DICCIONARIO TRADUCTOR
# ==========================================
def cargar_mapeo():
    archivo_json = 'mapeo_equipos.json'
    if os.path.exists(archivo_json):
        with open(archivo_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

MAPEO_EQUIPOS = cargar_mapeo()

def normalizar_nombre(nombre_externo):
    return MAPEO_EQUIPOS.get(str(nombre_externo).strip(), str(nombre_externo).strip())

# ==========================================
# 2. CARGA DE DATOS (HISTÓRICO Y JORNADA)
# ==========================================
try:
    df_historico = pd.read_csv('LaLiga_Dataset_Final.csv')
    lista_equipos = sorted(df_historico['HomeTeam'].dropna().unique().tolist())
except FileNotFoundError:
    df_historico = pd.DataFrame()
    lista_equipos = []
    st.error("⚠️ No se encuentra 'LaLiga_Dataset_Final.csv'.")

def obtener_ultimo_elo(equipo):
    equipo_normalizado = normalizar_nombre(equipo)
    if df_historico.empty:
        return 1.5
    df_e = df_historico[(df_historico['HomeTeam'] == equipo_normalizado) | (df_historico['AwayTeam'] == equipo_normalizado)]
    if not df_e.empty:
        fila = df_e.iloc[-1]
        return fila['elo_local'] if fila['HomeTeam'] == equipo_normalizado else fila['elo_visitante']
    return 1.5

def cargar_proxima_jornada():
    archivo = "proxima_jornada.csv"
    if os.path.exists(archivo):
        return pd.read_csv(archivo)
    return None

df_jornada = cargar_proxima_jornada()

# Crear pestañas
tab1, tab2, tab3 = st.tabs(["📅 Radar Automático (Próxima Jornada)", "🤖 Predictor Inteligente (Manual)", "📊 Estadística Avanzada"])

# ==========================================
# PESTAÑA 1: RADAR AUTOMÁTICO
# ==========================================
with tab1:
    if df_jornada is not None and not df_jornada.empty:
        st.subheader("Tabla de Partidos y Detección de Valor (Mercado 1X2)")
        
        tabla_analisis = []
        
        for index, row in df_jornada.iterrows():
            h_team = row['HomeTeam']
            a_team = row['AwayTeam']
            b365_h = float(row['B365H']) if not pd.isna(row['B365H']) else 0.0
            b365_d = float(row['B365D']) if not pd.isna(row['B365D']) else 0.0
            b365_a = float(row['B365A']) if not pd.isna(row['B365A']) else 0.0
            
            prob_b365_h = (1 / b365_h) * 100 if b365_h > 0 else 0
            prob_b365_d = (1 / b365_d) * 100 if b365_d > 0 else 0
            prob_b365_a = (1 / b365_a) * 100 if b365_a > 0 else 0
            
            datos_api = {
                "elo_local": float(obtener_ultimo_elo(h_team)),
                "elo_visitante": float(obtener_ultimo_elo(a_team)),
                "B365H": b365_h,
                "B365D": b365_d,
                "B365A": b365_a
            }
            
            prob_ia_h, prob_ia_d, prob_ia_a = 0.0, 0.0, 0.0
            try:
                res = requests.post("http://127.0.0.1:8000/predecir", json=datos_api)
                if res.status_code == 200:
                    pred = res.json()
                    prob_ia_h = float(pred['mercado_1X2']['Victoria_Local'])
                    prob_ia_d = float(pred['mercado_1X2']['Empate'])
                    prob_ia_a = float(pred['mercado_1X2']['Victoria_Visitante'])
            except:
                pass 
            
            recomendaciones = []
            ventajas = []
            
            # FILTRO ACTUALIZADO: Debe tener ventaja (> 2%) Y superar el umbral de probabilidad
            if prob_ia_h > 0:
                if prob_b365_h > 0 and prob_ia_h > (prob_b365_h + 2.0) and prob_ia_h >= umbral_prob:
                    recomendaciones.append("🏠 Local (1)")
                    ventajas.append(f"+{prob_ia_h - prob_b365_h:.1f}%")
                
                if prob_b365_d > 0 and prob_ia_d > (prob_b365_d + 2.0) and prob_ia_d >= umbral_prob:
                    recomendaciones.append("🤝 Empate (X)")
                    ventajas.append(f"+{prob_ia_d - prob_b365_d:.1f}%")
                    
                if prob_b365_a > 0 and prob_ia_a > (prob_b365_a + 2.0) and prob_ia_a >= umbral_prob:
                    recomendaciones.append("✈️ Visitante (2)")
                    ventajas.append(f"+{prob_ia_a - prob_b365_a:.1f}%")
            
            if recomendaciones:
                seleccion_final = " / ".join(recomendaciones)
                valor_final = f"💎 SÍ ({' | '.join(ventajas)})"
            else:
                seleccion_final = "-"
                valor_final = "❌ NO"
            
            h_team_norm = normalizar_nombre(h_team)
            a_team_norm = normalizar_nombre(a_team)
            
            tabla_analisis.append({
                "Fecha": row['Fecha'],
                "Partido": f"{h_team_norm} vs {a_team_norm}",
                "Cuotas (1-X-2)": f"{b365_h} - {b365_d} - {b365_a}",
                "Selección Recomendada": seleccion_final,
                "¿Apuesta de Valor?": valor_final
            })
            
        df_resultado = pd.DataFrame(tabla_analisis)
        st.dataframe(df_resultado, width='stretch')
        
    else:
        st.warning("⚠️ No se ha encontrado el archivo `proxima_jornada.csv`.")

# ==========================================
# PESTAÑA 2: PREDICTOR MANUAL (INTELIGENTE)
# ==========================================
with tab2:
    st.subheader("Consulta a la API de Predicciones")
    
    if lista_equipos:
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("🏠 Equipo Local", lista_equipos)
        with col2:
            visitante = st.selectbox("✈️ Equipo Visitante", lista_equipos)

        c1_def, cx_def, c2_def = 2.00, 3.50, 3.00
        partido_encontrado = False
        
        if df_jornada is not None and not df_jornada.empty:
            for _, row in df_jornada.iterrows():
                if normalizar_nombre(row['HomeTeam']) == local and normalizar_nombre(row['AwayTeam']) == visitante:
                    c1_def = float(row['B365H']) if not pd.isna(row['B365H']) else 2.00
                    cx_def = float(row['B365D']) if not pd.isna(row['B365D']) else 3.50
                    c2_def = float(row['B365A']) if not pd.isna(row['B365A']) else 3.00
                    partido_encontrado = True
                    break
        
        if partido_encontrado:
            st.success("🎯 **Partido detectado en la jornada actual.** Cuotas rellenadas automáticamente.")

        col3, col4, col5 = st.columns(3)
        with col3:
            cuota_1 = st.number_input("Cuota Local (1)", value=c1_def, step=0.10, format="%.2f")
        with col4:
            cuota_X = st.number_input("Cuota Empate (X)", value=cx_def, step=0.10, format="%.2f")
        with col5:
            cuota_2 = st.number_input("Cuota Visitante (2)", value=c2_def, step=0.10, format="%.2f")

        if st.button("🤖 Calcular Predicción Exacta"):
            datos_manuales = {
                "elo_local": float(obtener_ultimo_elo(local)),
                "elo_visitante": float(obtener_ultimo_elo(visitante)),
                "B365H": float(cuota_1),
                "B365D": float(cuota_X),
                "B365A": float(cuota_2)
            }
            
            try:
                res = requests.post("http://127.0.0.1:8000/predecir", json=datos_manuales)
                if res.status_code == 200:
                    pred = res.json()
                    
                    st.markdown("---")
                    
                    res_col1, res_col2 = st.columns(2)
                    with res_col1:
                        st.markdown("### 🏆 Probabilidades 1X2 (IA)")
                        st.write(f"🏠 Local: **{float(pred['mercado_1X2']['Victoria_Local']):.2f}%**")
                        st.write(f"🤝 Empate: **{float(pred['mercado_1X2']['Empate']):.2f}%**")
                        st.write(f"✈️ Visitante: **{float(pred['mercado_1X2']['Victoria_Visitante']):.2f}%**")
                    with res_col2:
                        st.markdown("### 🥅 Mercado de Goles (IA)")
                        st.write(f"🔼 Más de 2.5: **{float(pred['mercado_goles']['Mas_de_2.5']):.2f}%**")
                        st.write(f"🔽 Menos de 2.5: **{float(pred['mercado_goles']['Menos_de_2.5']):.2f}%**")

                    st.markdown("---")
                    st.markdown("### 💎 Análisis de Apuesta de Valor (Value Bet)")
                    
                    prob_casa_1 = (1 / cuota_1) * 100 if cuota_1 > 0 else 0
                    prob_casa_X = (1 / cuota_X) * 100 if cuota_X > 0 else 0
                    prob_casa_2 = (1 / cuota_2) * 100 if cuota_2 > 0 else 0
                    
                    prob_ia_1 = float(pred['mercado_1X2']['Victoria_Local'])
                    prob_ia_X = float(pred['mercado_1X2']['Empate'])
                    prob_ia_2 = float(pred['mercado_1X2']['Victoria_Visitante'])
                    
                    value_1 = prob_ia_1 > (prob_casa_1 + 2.0) and prob_ia_1 >= umbral_prob
                    value_X = prob_ia_X > (prob_casa_X + 2.0) and prob_ia_X >= umbral_prob
                    value_2 = prob_ia_2 > (prob_casa_2 + 2.0) and prob_ia_2 >= umbral_prob
                    
                    if value_1:
                        st.info(f"**Victoria Local (1):** ¡VALUE BET! Tu IA da **{prob_ia_1:.1f}%** vs **{prob_casa_1:.1f}%** de la casa. (Ventaja: +{prob_ia_1 - prob_casa_1:.1f}%)")
                    if value_X:
                        st.info(f"**Empate (X):** ¡VALUE BET! Tu IA da **{prob_ia_X:.1f}%** vs **{prob_casa_X:.1f}%** de la casa. (Ventaja: +{prob_ia_X - prob_casa_X:.1f}%)")
                    if value_2:
                        st.info(f"**Victoria Visitante (2):** ¡VALUE BET! Tu IA da **{prob_ia_2:.1f}%** vs **{prob_casa_2:.1f}%** de la casa. (Ventaja: +{prob_ia_2 - prob_casa_2:.1f}%)")
                    
                    if not any([value_1, value_X, value_2]):
                        st.warning(f"⚖️ No se detectan apuestas de valor que superen el umbral de probabilidad mínima del **{umbral_prob}%**.")
                        
                else:
                    st.error(f"Error en la respuesta de la API: Código {res.status_code}")
            except Exception as e:
                st.error(f"❌ No se pudo conectar a la API. ¿Está ejecutándose `uvicorn api_predicciones:app`?")
# ==========================================
# PESTAÑA 3: DASHBOARD ESTADÍSTICO (Desde 2000)
# ==========================================
with tab3:
    st.subheader("📊 Dashboard de Rendimiento Histórico (Factor Cancha)")
    st.markdown("Estadísticas filtradas desde el año 2000 teniendo en cuenta si el equipo juega de Local o Visitante.")
    
    if not df_historico.empty:
        # 1. Filtramos los datos desde el año 2000
        
        if 'Date' in df_historico.columns:
            df_historico['Date'] = pd.to_datetime(df_historico['Date'], dayfirst=True, errors='coerce')
            df_moderno = df_historico[df_historico['Date'].dt.year >= 2000].copy()
        elif 'Fecha' in df_historico.columns:
            df_historico['Fecha'] = pd.to_datetime(df_historico['Fecha'], dayfirst=True, errors='coerce')
            df_moderno = df_historico[df_historico['Fecha'].dt.year >= 2000].copy()
            df_moderno.rename(columns={'Fecha': 'Date'}, inplace=True)
        else:
            df_moderno = df_historico.copy() # Por si no encuentra la columna de fecha
            
        if lista_equipos:
            # Selectores de equipos
            col1, col2 = st.columns(2)
            with col1:
                eq_local = st.selectbox("🏠 Selecciona Equipo Local", lista_equipos, key="dash_loc")
            with col2:
                eq_visitante = st.selectbox("✈️ Selecciona Equipo Visitante", lista_equipos, key="dash_vis")
                
            st.markdown("---")
            
            # 2. Filtramos los DataFrames específicos para cada condición
            # 'FTHG' = Goles Local, 'FTAG' = Goles Visitante
            df_loc = df_moderno[df_moderno['HomeTeam'] == eq_local].copy()
            df_vis = df_moderno[df_moderno['AwayTeam'] == eq_visitante].copy()
            
            if not df_loc.empty and not df_vis.empty:
                # --- MÉTRICAS PRINCIPALES ---
                st.markdown("### 📈 Resumen de Rendimiento")
                
                # Cálculos Local
                partidos_loc = len(df_loc)
                victorias_loc = len(df_loc[df_loc['FTHG'] > df_loc['FTAG']])
                goles_favor_loc = df_loc['FTHG'].mean()
                goles_contra_loc = df_loc['FTAG'].mean()
                
                # Cálculos Visitante
                partidos_vis = len(df_vis)
                victorias_vis = len(df_vis[df_vis['FTAG'] > df_vis['FTHG']])
                goles_favor_vis = df_vis['FTAG'].mean()
                goles_contra_vis = df_vis['FTHG'].mean()
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric(f"Victorias {eq_local} (En casa)", f"{(victorias_loc/partidos_loc)*100:.1f}%")
                m2.metric("Goles a favor (Media)", f"{goles_favor_loc:.2f}")
                m3.metric(f"Victorias {eq_visitante} (Fuera)", f"{(victorias_vis/partidos_vis)*100:.1f}%")
                m4.metric("Goles a favor (Media)", f"{goles_favor_vis:.2f}")
                
                # --- PROBABILIDADES DE GOLES ---
                st.markdown("### 🥅 Probabilidades de Goles")
                c_loc, c_vis = st.columns(2)
                
                with c_loc:
                    st.markdown(f"**{eq_local} jugando en casa:**")
                    st.write(f"✅ Marcar +1 gol: **{(len(df_loc[df_loc['FTHG'] > 1]) / partidos_loc)*100:.1f}%**")
                    st.write(f"🔥 Marcar +2 goles: **{(len(df_loc[df_loc['FTHG'] > 2]) / partidos_loc)*100:.1f}%**")
                    st.write(f"🤯 Marcar +3 goles: **{(len(df_loc[df_loc['FTHG'] > 3]) / partidos_loc)*100:.1f}%**")
                    st.markdown("---")
                    st.write(f"⚠️ Recibir 1+ gol: **{(len(df_loc[df_loc['FTAG'] >= 1]) / partidos_loc)*100:.1f}%**")
                    st.write(f"🚨 Recibir 2+ goles: **{(len(df_loc[df_loc['FTAG'] >= 2]) / partidos_loc)*100:.1f}%**")
                    
                with c_vis:
                    st.markdown(f"**{eq_visitante} jugando fuera:**")
                    st.write(f"✅ Marcar +1 gol: **{(len(df_vis[df_vis['FTAG'] > 1]) / partidos_vis)*100:.1f}%**")
                    st.write(f"🔥 Marcar +2 goles: **{(len(df_vis[df_vis['FTAG'] > 2]) / partidos_vis)*100:.1f}%**")
                    st.write(f"🤯 Marcar +3 goles: **{(len(df_vis[df_vis['FTAG'] > 3]) / partidos_vis)*100:.1f}%**")
                    st.markdown("---")
                    st.write(f"⚠️ Recibir 1+ gol: **{(len(df_vis[df_vis['FTHG'] >= 1]) / partidos_vis)*100:.1f}%**")
                    st.write(f"🚨 Recibir 2+ goles: **{(len(df_vis[df_vis['FTHG'] >= 2]) / partidos_vis)*100:.1f}%**")
                
                st.markdown("---")
                
                # --- GRÁFICAS INTERACTIVAS ---
                st.markdown("### 📊 Evolución del ELO Histórico")
                # Graficamos el ELO local
                fig_elo_loc = px.line(df_loc, x='Date', y='elo_local', title=f"Evolución ELO de {eq_local} (En casa)")
                st.plotly_chart(fig_elo_loc, width='stretch')
                
                fig_elo_vis = px.line(df_vis, x='Date', y='elo_visitante', title=f"Evolución ELO de {eq_visitante} (Fuera)", color_discrete_sequence=['#FF4B4B'])
                st.plotly_chart(fig_elo_vis, width='stretch')
                
                # --- GRÁFICA DE CLIMA VS GOLES ---
                st.markdown("### 🌤️ Impacto del Clima en los Goles")

                col_clima = 'temp_max' if 'temp_max' in df_loc.columns else None                
                if col_clima:
                    fig_clima = px.scatter(df_loc, x=col_clima, y='FTHG', trendline="ols", 
                                           title=f"Goles marcados por {eq_local} vs Temperatura",
                                           labels={col_clima: "Temperatura (°C)", "FTHG": "Goles Marcados"})
                    st.plotly_chart(fig_clima, width='stretch')
                else:
                    st.info("💡 Para visualizar la gráfica del clima, asegúrate de que el nombre de la columna meteorológica en tu CSV coincide en el código (ej. 'temperature', 'rain').")
            else:
                st.warning("No hay suficientes datos desde el año 2000 para estos equipos.")
    else:
        st.error("No se ha podido cargar el dataset histórico.")