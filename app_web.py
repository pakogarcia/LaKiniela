import streamlit as st
import pandas as pd
import requests
import json
import os
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="LaKiniela - Trading & IA", page_icon="⚽", layout="wide")

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


# ==========================================
# BARRA LATERAL (AJUSTES GLOBALES)
# ==========================================
st.sidebar.header("⚙️ Configuración del Partido")
st.sidebar.markdown("Selecciona los equipos para analizar:")

local = st.sidebar.selectbox("🏠 Equipo Local", lista_equipos, index=0)
visitante = st.sidebar.selectbox("✈️ Equipo Visitante", lista_equipos, index=1)

st.sidebar.markdown("---")

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


# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
st.title("⚽ LaKiniela: Panel de Analítica y Predicción")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📅 Radar Automático (Próxima Jornada)", "🤖 Predictor Inteligente (Manual)", "📊 Estadística Avanzada"])

# ==========================================
# PESTAÑA 1: RADAR AUTOMÁTICO (ACTUALIZADO CON 3 MERCADOS)
# ==========================================
with tab1:
    if df_jornada is not None and not df_jornada.empty:
        st.subheader("Radar de Apuestas de Valor (1X2, Goles y Ambos Marcan)")
        
        tabla_analisis = []
        
        for index, row in df_jornada.iterrows():
            h_team = row['HomeTeam']
            a_team = row['AwayTeam']
            
            # --- 1. LEER CUOTAS DE LA CASA DE APUESTAS ---
            # Mercado 1X2
            b365_h = float(row.get('B365H', 0.0)) if pd.notna(row.get('B365H', 0.0)) else 0.0
            b365_d = float(row.get('B365D', 0.0)) if pd.notna(row.get('B365D', 0.0)) else 0.0
            b365_a = float(row.get('B365A', 0.0)) if pd.notna(row.get('B365A', 0.0)) else 0.0
            
            # Mercado Goles (NUEVO)
            b365_over = float(row.get('B365_Over25', 0.0)) if pd.notna(row.get('B365_Over25', 0.0)) else 0.0
            b365_under = float(row.get('B365_Under25', 0.0)) if pd.notna(row.get('B365_Under25', 0.0)) else 0.0
            
            # Mercado BTTS (NUEVO)
            b365_btts_y = float(row.get('B365_BTTS_Y', 0.0)) if pd.notna(row.get('B365_BTTS_Y', 0.0)) else 0.0
            b365_btts_n = float(row.get('B365_BTTS_N', 0.0)) if pd.notna(row.get('B365_BTTS_N', 0.0)) else 0.0
            
            # --- 2. CONVERTIR A PORCENTAJES MATEMÁTICOS ---
            prob_b365_h = (1 / b365_h) * 100 if b365_h > 0 else 0
            prob_b365_d = (1 / b365_d) * 100 if b365_d > 0 else 0
            prob_b365_a = (1 / b365_a) * 100 if b365_a > 0 else 0
            prob_b365_over = (1 / b365_over) * 100 if b365_over > 0 else 0
            prob_b365_under = (1 / b365_under) * 100 if b365_under > 0 else 0
            prob_b365_btts_y = (1 / b365_btts_y) * 100 if b365_btts_y > 0 else 0
            prob_b365_btts_n = (1 / b365_btts_n) * 100 if b365_btts_n > 0 else 0
            
            # --- 3. CONSULTAR A NUESTRA INTELIGENCIA ARTIFICIAL ---
            datos_api = {
                "elo_local": float(obtener_ultimo_elo(h_team)),
                "elo_visitante": float(obtener_ultimo_elo(a_team)),
                "B365H": b365_h, "B365D": b365_d, "B365A": b365_a
            }
            
            prob_ia_h, prob_ia_d, prob_ia_a = 0.0, 0.0, 0.0
            prob_ia_over, prob_ia_under = 0.0, 0.0
            prob_ia_btts_y, prob_ia_btts_n = 0.0, 0.0
            
            try:
                res = requests.post("http://127.0.0.1:8000/predecir", json=datos_api)
                if res.status_code == 200:
                    pred = res.json()
                    # Extraer las 7 probabilidades
                    prob_ia_h = float(pred['mercado_1X2']['Victoria_Local'])
                    prob_ia_d = float(pred['mercado_1X2']['Empate'])
                    prob_ia_a = float(pred['mercado_1X2']['Victoria_Visitante'])
                    prob_ia_under = float(pred['mercado_goles']['Menos_de_2.5'])
                    prob_ia_over = float(pred['mercado_goles']['Mas_de_2.5'])
                    prob_ia_btts_n = float(pred['mercado_btts']['Ambos_Marcan_No'])
                    prob_ia_btts_y = float(pred['mercado_btts']['Ambos_Marcan_Si'])
            except:
                pass 
            
            # --- 4. DETECCIÓN AUTOMÁTICA DE VALUE BETS ---
            recomendaciones = []
            
            if prob_ia_h > 0: # Solo si la API respondió correctamente
                # Mercado 1X2
                if prob_b365_h > 0 and prob_ia_h > (prob_b365_h + 2.0) and prob_ia_h >= umbral_prob:
                    recomendaciones.append(f"🏠 1 (+{prob_ia_h - prob_b365_h:.1f}%)")
                if prob_b365_d > 0 and prob_ia_d > (prob_b365_d + 2.0) and prob_ia_d >= umbral_prob:
                    recomendaciones.append(f"🤝 X (+{prob_ia_d - prob_b365_d:.1f}%)")
                if prob_b365_a > 0 and prob_ia_a > (prob_b365_a + 2.0) and prob_ia_a >= umbral_prob:
                    recomendaciones.append(f"✈️ 2 (+{prob_ia_a - prob_b365_a:.1f}%)")
                
                # Mercado Goles
                if prob_b365_over > 0 and prob_ia_over > (prob_b365_over + 2.0) and prob_ia_over >= umbral_prob:
                    recomendaciones.append(f"🔼 +2.5 Goles (+{prob_ia_over - prob_b365_over:.1f}%)")
                if prob_b365_under > 0 and prob_ia_under > (prob_b365_under + 2.0) and prob_ia_under >= umbral_prob:
                    recomendaciones.append(f"🔽 -2.5 Goles (+{prob_ia_under - prob_b365_under:.1f}%)")
                    
                # Mercado BTTS
                if prob_b365_btts_y > 0 and prob_ia_btts_y > (prob_b365_btts_y + 2.0) and prob_ia_btts_y >= umbral_prob:
                    recomendaciones.append(f"⚽ BTTS: SÍ (+{prob_ia_btts_y - prob_b365_btts_y:.1f}%)")
                if prob_b365_btts_n > 0 and prob_ia_btts_n > (prob_b365_btts_n + 2.0) and prob_ia_btts_n >= umbral_prob:
                    recomendaciones.append(f"🚫 BTTS: NO (+{prob_ia_btts_n - prob_b365_btts_n:.1f}%)")
            
            if recomendaciones:
                seleccion_final = " | ".join(recomendaciones)
                valor_final = "💎 SÍ"
            else:
                seleccion_final = "-"
                valor_final = "❌ NO"
            
            h_team_norm = normalizar_nombre(h_team)
            a_team_norm = normalizar_nombre(a_team)
            
            tabla_analisis.append({
                "Fecha": row['Date'] if 'Date' in row else row.get('Fecha', '-'),
                "Partido": f"{h_team_norm} vs {a_team_norm}",
                "¿Hay Valor?": valor_final,
                "Inversiones Recomendadas (IA Ventaja %)": seleccion_final
            })
            
        df_resultado = pd.DataFrame(tabla_analisis)
        st.dataframe(df_resultado, width='stretch')
        
    else:
        st.warning("⚠️ No se ha encontrado el archivo `proxima_jornada.csv`.")

# ==========================================
# PESTAÑA 2: PREDICTOR MANUAL (INTELIGENTE)
# ==========================================
with tab2:
    st.subheader("Consulta a la API de Predicciones y Análisis de Valor")
    
    if lista_equipos:
        # Valores por defecto
        c1_def, cx_def, c2_def = 2.00, 3.50, 3.00
        co_def, cu_def = 1.90, 1.90
        cby_def, cbn_def = 1.90, 1.90
        partido_encontrado = False
        
        # Autorellenar si el partido está en el CSV de la jornada
        if df_jornada is not None and not df_jornada.empty:
            for _, row in df_jornada.iterrows():
                if normalizar_nombre(row['HomeTeam']) == local and normalizar_nombre(row['AwayTeam']) == visitante:
                    c1_def = float(row.get('B365H', 2.00)) if pd.notna(row.get('B365H')) else 2.00
                    cx_def = float(row.get('B365D', 3.50)) if pd.notna(row.get('B365D')) else 3.50
                    c2_def = float(row.get('B365A', 3.00)) if pd.notna(row.get('B365A')) else 3.00
                    co_def = float(row.get('B365_Over25', 1.90)) if pd.notna(row.get('B365_Over25')) else 1.90
                    cu_def = float(row.get('B365_Under25', 1.90)) if pd.notna(row.get('B365_Under25')) else 1.90
                    cby_def = float(row.get('B365_BTTS_Y', 1.90)) if pd.notna(row.get('B365_BTTS_Y')) else 1.90
                    cbn_def = float(row.get('B365_BTTS_N', 1.90)) if pd.notna(row.get('B365_BTTS_N')) else 1.90
                    partido_encontrado = True
                    break
        
        if partido_encontrado:
            st.success("🎯 **Partido detectado en la jornada actual.** Cuotas de los 3 mercados rellenadas automáticamente.")

        st.markdown("**Introduce o verifica las cuotas de la casa de apuestas:**")
        
        # Fila 1: Cuotas 1X2
        col_q1, col_qx, col_q2 = st.columns(3)
        with col_q1: cuota_1 = st.number_input("Local (1)", value=c1_def, step=0.10, format="%.2f")
        with col_qx: cuota_X = st.number_input("Empate (X)", value=cx_def, step=0.10, format="%.2f")
        with col_q2: cuota_2 = st.number_input("Visitante (2)", value=c2_def, step=0.10, format="%.2f")

        # Fila 2: Cuotas Goles y BTTS
        col_qo, col_qu, col_qby, col_qbn = st.columns(4)
        with col_qo: cuota_over = st.number_input("Más +2.5", value=co_def, step=0.10, format="%.2f")
        with col_qu: cuota_under = st.number_input("Menos -2.5", value=cu_def, step=0.10, format="%.2f")
        with col_qby: cuota_btts_si = st.number_input("BTTS (SÍ)", value=cby_def, step=0.10, format="%.2f")
        with col_qbn: cuota_btts_no = st.number_input("BTTS (NO)", value=cbn_def, step=0.10, format="%.2f")

        if st.button("🤖 Calcular Predicción y Analizar Valor"):
            datos_manuales = {
                "elo_local": float(obtener_ultimo_elo(local)),
                "elo_visitante": float(obtener_ultimo_elo(visitante)),
                "B365H": float(cuota_1), "B365D": float(cuota_X), "B365A": float(cuota_2)
            }
            
            try:
                res = requests.post("http://127.0.0.1:8000/predecir", json=datos_manuales)
                if res.status_code == 200:
                    pred = res.json()
                    
                    st.markdown("---")
                    
                    res_col1, res_col2, res_col3 = st.columns(3)
                    with res_col1:
                        st.markdown("### 🏆 Probabilidades 1X2")
                        st.write(f"🏠 Local: **{float(pred['mercado_1X2']['Victoria_Local']):.2f}%**")
                        st.write(f"🤝 Empate: **{float(pred['mercado_1X2']['Empate']):.2f}%**")
                        st.write(f"✈️ Visitante: **{float(pred['mercado_1X2']['Victoria_Visitante']):.2f}%**")
                    with res_col2:
                        st.markdown("### 🥅 Goles (Más/Menos)")
                        st.write(f"🔼 Más de 2.5: **{float(pred['mercado_goles']['Mas_de_2.5']):.2f}%**")
                        st.write(f"🔽 Menos de 2.5: **{float(pred['mercado_goles']['Menos_de_2.5']):.2f}%**")
                    with res_col3:
                        st.markdown("### ⚽ Ambos Marcan (BTTS)")
                        st.write(f"✅ SÍ marcan: **{float(pred['mercado_btts']['Ambos_Marcan_Si']):.2f}%**")
                        st.write(f"❌ NO marcan: **{float(pred['mercado_btts']['Ambos_Marcan_No']):.2f}%**")

                    st.markdown("---")
                    st.markdown("### 💎 Análisis Integral de Apuesta de Valor (Todos los Mercados)")
                    st.markdown("*La IA compara sus probabilidades con las cuotas que has introducido para buscar ventajas matemáticas.*")
                    
                    # 1. Calcular probabilidades implícitas de la casa de apuestas
                    prob_casa_1 = (1 / cuota_1) * 100 if cuota_1 > 0 else 0
                    prob_casa_X = (1 / cuota_X) * 100 if cuota_X > 0 else 0
                    prob_casa_2 = (1 / cuota_2) * 100 if cuota_2 > 0 else 0
                    prob_casa_over = (1 / cuota_over) * 100 if cuota_over > 0 else 0
                    prob_casa_under = (1 / cuota_under) * 100 if cuota_under > 0 else 0
                    prob_casa_btts_si = (1 / cuota_btts_si) * 100 if cuota_btts_si > 0 else 0
                    prob_casa_btts_no = (1 / cuota_btts_no) * 100 if cuota_btts_no > 0 else 0
                    
                    # 2. Extraer probabilidades de la IA
                    prob_ia_1 = float(pred['mercado_1X2']['Victoria_Local'])
                    prob_ia_X = float(pred['mercado_1X2']['Empate'])
                    prob_ia_2 = float(pred['mercado_1X2']['Victoria_Visitante'])
                    prob_ia_over = float(pred['mercado_goles']['Mas_de_2.5'])
                    prob_ia_under = float(pred['mercado_goles']['Menos_de_2.5'])
                    prob_ia_btts_si = float(pred['mercado_btts']['Ambos_Marcan_Si'])
                    prob_ia_btts_no = float(pred['mercado_btts']['Ambos_Marcan_No'])
                    
                    # 3. Evaluar condiciones de Value Bet
                    val_1 = prob_ia_1 > (prob_casa_1 + 2.0) and prob_ia_1 >= umbral_prob
                    val_X = prob_ia_X > (prob_casa_X + 2.0) and prob_ia_X >= umbral_prob
                    val_2 = prob_ia_2 > (prob_casa_2 + 2.0) and prob_ia_2 >= umbral_prob
                    val_over = prob_ia_over > (prob_casa_over + 2.0) and prob_ia_over >= umbral_prob
                    val_under = prob_ia_under > (prob_casa_under + 2.0) and prob_ia_under >= umbral_prob
                    val_btts_si = prob_ia_btts_si > (prob_casa_btts_si + 2.0) and prob_ia_btts_si >= umbral_prob
                    val_btts_no = prob_ia_btts_no > (prob_casa_btts_no + 2.0) and prob_ia_btts_no >= umbral_prob
                    
                    hay_valor = False
                    
                    # 4. Imprimir informes detallados
                    if val_1:
                        st.info(f"🏠 **Victoria Local (1):** ¡INVERSIÓN RECOMENDADA! La cuota {cuota_1} asume un {prob_casa_1:.1f}% de éxito. Tu IA calcula un **{prob_ia_1:.1f}%**. Ventaja matemática: **+{prob_ia_1 - prob_casa_1:.1f}%** (Supera tu filtro del **{umbral_prob}%**).")
                        hay_valor = True
                    if val_X:
                        st.info(f"🤝 **Empate (X):** ¡INVERSIÓN RECOMENDADA! La cuota {cuota_X} asume un {prob_casa_X:.1f}% de éxito. Tu IA calcula un **{prob_ia_X:.1f}%**. Ventaja matemática: **+{prob_ia_X - prob_casa_X:.1f}%** (Supera tu filtro del **{umbral_prob}%**).")
                        hay_valor = True
                    if val_2:
                        st.info(f"✈️ **Victoria Visitante (2):** ¡INVERSIÓN RECOMENDADA! La cuota {cuota_2} asume un {prob_casa_2:.1f}% de éxito. Tu IA calcula un **{prob_ia_2:.1f}%**. Ventaja matemática: **+{prob_ia_2 - prob_casa_2:.1f}%** (Supera tu filtro del **{umbral_prob}%**).")
                        hay_valor = True
                    if val_over:
                        st.success(f"🔼 **Más de 2.5 Goles:** ¡INVERSIÓN RECOMENDADA! La cuota {cuota_over} asume un {prob_casa_over:.1f}% de éxito. Tu IA calcula un **{prob_ia_over:.1f}%**. Ventaja matemática: **+{prob_ia_over - prob_casa_over:.1f}%** (Supera tu filtro del **{umbral_prob}%**).")
                        hay_valor = True
                    if val_under:
                        st.success(f"🔽 **Menos de 2.5 Goles:** ¡INVERSIÓN RECOMENDADA! La cuota {cuota_under} asume un {prob_casa_under:.1f}% de éxito. Tu IA calcula un **{prob_ia_under:.1f}%**. Ventaja matemática: **+{prob_ia_under - prob_casa_under:.1f}%** (Supera tu filtro del **{umbral_prob}%**).")
                        hay_valor = True
                    if val_btts_si:
                        st.success(f"⚽ **Ambos Marcan (SÍ):** ¡INVERSIÓN RECOMENDADA! La cuota {cuota_btts_si} asume un {prob_casa_btts_si:.1f}% de éxito. Tu IA calcula un **{prob_ia_btts_si:.1f}%**. Ventaja matemática: **+{prob_ia_btts_si - prob_casa_btts_si:.1f}%** (Supera tu filtro del **{umbral_prob}%**).")
                        hay_valor = True
                    if val_btts_no:
                        st.success(f"🚫 **Ambos Marcan (NO):** ¡INVERSIÓN RECOMENDADA! La cuota {cuota_btts_no} asume un {prob_casa_btts_no:.1f}% de éxito. Tu IA calcula un **{prob_ia_btts_no:.1f}%**. Ventaja matemática: **+{prob_ia_btts_no - prob_casa_btts_no:.1f}%** (Supera tu filtro del **{umbral_prob}%**).")
                        hay_valor = True
                    
                    if not hay_valor:
                        st.warning(f"⚖️ **Mala inversión:** Las cuotas ofrecidas por la casa de apuestas están demasiado ajustadas. No se detecta ninguna ventaja matemática clara que supere tu filtro del **{umbral_prob}%** de seguridad en ninguno de los mercados. Es mejor no apostar en este partido.")
                        
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
        if 'Date' in df_historico.columns:
            df_historico['Date'] = pd.to_datetime(df_historico['Date'], dayfirst=True, errors='coerce')
            df_moderno = df_historico[df_historico['Date'].dt.year >= 2000].copy()
        elif 'Fecha' in df_historico.columns:
            df_historico['Fecha'] = pd.to_datetime(df_historico['Fecha'], dayfirst=True, errors='coerce')
            df_moderno = df_historico[df_historico['Fecha'].dt.year >= 2000].copy()
            df_moderno.rename(columns={'Fecha': 'Date'}, inplace=True)
        else:
            df_moderno = df_historico.copy()
            
        if lista_equipos:
            
            df_loc = df_moderno[df_moderno['HomeTeam'] == local].copy()
            df_vis = df_moderno[df_moderno['AwayTeam'] == visitante].copy()
            
            if not df_loc.empty and not df_vis.empty:
                st.markdown("### 📈 Resumen de Rendimiento")
                
                partidos_loc = len(df_loc)
                victorias_loc = len(df_loc[df_loc['FTHG'] > df_loc['FTAG']])
                goles_favor_loc = df_loc['FTHG'].mean()
                
                partidos_vis = len(df_vis)
                victorias_vis = len(df_vis[df_vis['FTAG'] > df_vis['FTHG']])
                goles_favor_vis = df_vis['FTAG'].mean()
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric(f"Victorias {local} (En casa)", f"{(victorias_loc/partidos_loc)*100:.1f}%")
                m2.metric("Goles a favor (Media)", f"{goles_favor_loc:.2f}")
                m3.metric(f"Victorias {visitante} (Fuera)", f"{(victorias_vis/partidos_vis)*100:.1f}%")
                m4.metric("Goles a favor (Media)", f"{goles_favor_vis:.2f}")
                
                st.markdown("### 🥅 Probabilidades de Goles")
                c_loc, c_vis = st.columns(2)
                
                with c_loc:
                    st.markdown(f"**{local} jugando en casa:**")
                    st.write(f"✅ Marcar +1 gol: **{(len(df_loc[df_loc['FTHG'] > 1]) / partidos_loc)*100:.1f}%**")
                    st.write(f"🔥 Marcar +2 goles: **{(len(df_loc[df_loc['FTHG'] > 2]) / partidos_loc)*100:.1f}%**")
                    st.write(f"🤯 Marcar +3 goles: **{(len(df_loc[df_loc['FTHG'] > 3]) / partidos_loc)*100:.1f}%**")
                    st.markdown("---")
                    st.write(f"⚠️ Recibir 1+ gol: **{(len(df_loc[df_loc['FTAG'] >= 1]) / partidos_loc)*100:.1f}%**")
                    st.write(f"🚨 Recibir 2+ goles: **{(len(df_loc[df_loc['FTAG'] >= 2]) / partidos_loc)*100:.1f}%**")
                    
                with c_vis:
                    st.markdown(f"**{visitante} jugando fuera:**")
                    st.write(f"✅ Marcar +1 gol: **{(len(df_vis[df_vis['FTAG'] > 1]) / partidos_vis)*100:.1f}%**")
                    st.write(f"🔥 Marcar +2 goles: **{(len(df_vis[df_vis['FTAG'] > 2]) / partidos_vis)*100:.1f}%**")
                    st.write(f"🤯 Marcar +3 goles: **{(len(df_vis[df_vis['FTAG'] > 3]) / partidos_vis)*100:.1f}%**")
                    st.markdown("---")
                    st.write(f"⚠️ Recibir 1+ gol: **{(len(df_vis[df_vis['FTHG'] >= 1]) / partidos_vis)*100:.1f}%**")
                    st.write(f"🚨 Recibir 2+ goles: **{(len(df_vis[df_vis['FTHG'] >= 2]) / partidos_vis)*100:.1f}%**")
                
                st.markdown("---")
                
                st.markdown("### 📊 Evolución del ELO Histórico")
                fig_elo_loc = px.line(df_loc, x='Date', y='elo_local', title=f"Evolución ELO de {local} (En casa)")
                st.plotly_chart(fig_elo_loc, width='stretch')
                
                fig_elo_vis = px.line(df_vis, x='Date', y='elo_visitante', title=f"Evolución ELO de {visitante} (Fuera)", color_discrete_sequence=['#FF4B4B'])
                st.plotly_chart(fig_elo_vis, width='stretch')
                
                st.markdown("### 🌤️ Impacto del Clima en los Goles")
                col_clima = 'temp_max' if 'temp_max' in df_loc.columns else None                
                if col_clima:
                    fig_clima = px.scatter(df_loc, x=col_clima, y='FTHG', trendline="ols", 
                                           title=f"Goles marcados por {local} vs Temperatura",
                                           labels={col_clima: "Temperatura (°C)", "FTHG": "Goles Marcados"})
                    st.plotly_chart(fig_clima, width='stretch')
                else:
                    st.info("💡 Para visualizar la gráfica del clima, asegúrate de que el nombre de la columna meteorológica en tu CSV coincide en el código (ej. 'temp_max').")
            else:
                st.warning("No hay suficientes datos desde el año 2000 para estos equipos.")
    else:
        st.error("No se ha podido cargar el dataset histórico.")