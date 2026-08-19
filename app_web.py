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
        return 1550.0
    
    # Filtrar partidos del equipo donde el ELO esté registrado
    df_e = df_historico[
        ((df_historico['HomeTeam'] == equipo_normalizado) & df_historico['elo_local'].notna()) |
        ((df_historico['AwayTeam'] == equipo_normalizado) & df_historico['elo_visitante'].notna())
    ]
    if not df_e.empty:
        fila = df_e.iloc[-1]
        val = fila['elo_local'] if fila['HomeTeam'] == equipo_normalizado else fila['elo_visitante']
        if pd.notna(val):
            return float(val)
            
    # Fallback: media general de ELO de la base de datos
    media_elo = df_historico['elo_local'].dropna().mean()
    return float(media_elo) if pd.notna(media_elo) else 1550.0

def cargar_proxima_jornada():
    archivo = "proxima_jornada.csv"
    if os.path.exists(archivo):
        try:
            return pd.read_csv(archivo, sep=None, engine='python', encoding='utf-8')
        except Exception:
            return pd.read_csv(archivo, sep=';', encoding='utf-8')
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

tab1, tab2, tab3, tab4 = st.tabs([
    "📅 Radar Automático (Próxima Jornada)", 
    "🤖 Predictor Inteligente (Manual)", 
    "📊 Estadística Avanzada",
    "⏱️ Tracker In-Play & Live Sniper"
])


# ==========================================
# PESTAÑA 1: RADAR AUTOMÁTICO (ACTUALIZADO CON 4 MERCADOS)
# ==========================================
with tab1:
    if df_jornada is not None and not df_jornada.empty:
        st.subheader("Radar de Apuestas de Valor (1X2, Goles, Ambos Marcan y Córners)")
        
        tabla_analisis = []
        
        for index, row in df_jornada.iterrows():
            h_team = row['HomeTeam']
            a_team = row['AwayTeam']
            
            # --- 1. LEER CUOTAS DE LA CASA DE APUESTAS ---
            # Mercado 1X2
            b365_h = float(row.get('B365H', 0.0)) if pd.notna(row.get('B365H', 0.0)) else 0.0
            b365_d = float(row.get('B365D', 0.0)) if pd.notna(row.get('B365D', 0.0)) else 0.0
            b365_a = float(row.get('B365A', 0.0)) if pd.notna(row.get('B365A', 0.0)) else 0.0
            
            # Mercado Goles
            b365_over = float(row.get('B365_Over25', 0.0)) if pd.notna(row.get('B365_Over25', 0.0)) else 0.0
            b365_under = float(row.get('B365_Under25', 0.0)) if pd.notna(row.get('B365_Under25', 0.0)) else 0.0
            
            # Mercado BTTS
            b365_btts_y = float(row.get('B365_BTTS_Y', 0.0)) if pd.notna(row.get('B365_BTTS_Y', 0.0)) else 0.0
            b365_btts_n = float(row.get('B365_BTTS_N', 0.0)) if pd.notna(row.get('B365_BTTS_N', 0.0)) else 0.0
            
            # Mercado Córners (NUEVO)
            b365_cor_over = float(row.get('B365_Over95_Corners', 0.0)) if pd.notna(row.get('B365_Over95_Corners', 0.0)) else 0.0
            b365_cor_under = float(row.get('B365_Under95_Corners', 0.0)) if pd.notna(row.get('B365_Under95_Corners', 0.0)) else 0.0

            # --- 2. CONVERTIR A PORCENTAJES MATEMÁTICOS ---
            prob_b365_h = (1 / b365_h) * 100 if b365_h > 0 else 0
            prob_b365_d = (1 / b365_d) * 100 if b365_d > 0 else 0
            prob_b365_a = (1 / b365_a) * 100 if b365_a > 0 else 0
            prob_b365_over = (1 / b365_over) * 100 if b365_over > 0 else 0
            prob_b365_under = (1 / b365_under) * 100 if b365_under > 0 else 0
            prob_b365_btts_y = (1 / b365_btts_y) * 100 if b365_btts_y > 0 else 0
            prob_b365_btts_n = (1 / b365_btts_n) * 100 if b365_btts_n > 0 else 0
            prob_b365_cor_over = (1 / b365_cor_over) * 100 if b365_cor_over > 0 else 0
            prob_b365_cor_under = (1 / b365_cor_under) * 100 if b365_cor_under > 0 else 0
            
            # --- 3. CONSULTAR A NUESTRA INTELIGENCIA ARTIFICIAL ---
            datos_api = {
                "elo_local": float(obtener_ultimo_elo(h_team)),
                "elo_visitante": float(obtener_ultimo_elo(a_team)),
                "B365H": b365_h if b365_h > 0 else 2.00,
                "B365D": b365_d if b365_d > 0 else 3.40,
                "B365A": b365_a if b365_a > 0 else 3.20
            }
            
            prob_ia_h, prob_ia_d, prob_ia_a = 0.0, 0.0, 0.0
            prob_ia_over, prob_ia_under = 0.0, 0.0
            prob_ia_btts_y, prob_ia_btts_n = 0.0, 0.0
            prob_ia_cor_over, prob_ia_cor_under = 0.0, 0.0
            
            try:
                res = requests.post("http://127.0.0.1:8000/predecir", json=datos_api, timeout=5)
                if res.status_code == 200:
                    pred = res.json()
                    prob_ia_h = float(pred['mercado_1X2']['Victoria_Local'])
                    prob_ia_d = float(pred['mercado_1X2']['Empate'])
                    prob_ia_a = float(pred['mercado_1X2']['Victoria_Visitante'])
                    prob_ia_under = float(pred['mercado_goles']['Menos_de_2.5'])
                    prob_ia_over = float(pred['mercado_goles']['Mas_de_2.5'])
                    prob_ia_btts_n = float(pred['mercado_btts']['Ambos_Marcan_No'])
                    prob_ia_btts_y = float(pred['mercado_btts']['Ambos_Marcan_Si'])
                    if 'mercado_corners' in pred:
                        prob_ia_cor_under = float(pred['mercado_corners']['Menos_de_9.5'])
                        prob_ia_cor_over = float(pred['mercado_corners']['Mas_de_9.5'])
            except:
                pass 
            
            # --- 4. DETECCIÓN AUTOMÁTICA DE VALUE BETS ---
            recomendaciones = []
            
            if prob_ia_h > 0:
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

                # Mercado Córners (NUEVO)
                if prob_b365_cor_over > 0 and prob_ia_cor_over > (prob_b365_cor_over + 2.0) and prob_ia_cor_over >= umbral_prob:
                    recomendaciones.append(f"🚩 +9.5 Córners (+{prob_ia_cor_over - prob_b365_cor_over:.1f}%)")
                if prob_b365_cor_under > 0 and prob_ia_cor_under > (prob_b365_cor_under + 2.0) and prob_ia_cor_under >= umbral_prob:
                    recomendaciones.append(f"🚩 -9.5 Córners (+{prob_ia_cor_under - prob_b365_cor_under:.1f}%)")
            
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
        cco_def, ccu_def = 1.83, 1.83
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
                    cco_def = float(row.get('B365_Over95_Corners', 1.83)) if pd.notna(row.get('B365_Over95_Corners')) else 1.83
                    ccu_def = float(row.get('B365_Under95_Corners', 1.83)) if pd.notna(row.get('B365_Under95_Corners')) else 1.83
                    partido_encontrado = True
                    break
        
        if partido_encontrado:
            st.success("🎯 **Partido detectado en la jornada actual.** Cuotas de los 4 mercados rellenadas automáticamente.")

        st.markdown("**Introduce o verifica las cuotas de la casa de apuestas:**")
        
        # Fila 1: Cuotas 1X2
        st.caption("🏆 Mercado 1X2")
        col_q1, col_qx, col_q2 = st.columns(3)
        with col_q1: cuota_1 = st.number_input("Local (1)", value=c1_def, step=0.05, format="%.2f")
        with col_qx: cuota_X = st.number_input("Empate (X)", value=cx_def, step=0.05, format="%.2f")
        with col_q2: cuota_2 = st.number_input("Visitante (2)", value=c2_def, step=0.05, format="%.2f")

        # Fila 2: Cuotas Goles, BTTS y Córners
        st.caption("🥅 Mercados de Goles, Ambos Marcan y Córners")
        col_qo, col_qu, col_qby, col_qbn, col_qco, col_qcu = st.columns(6)
        with col_qo: cuota_over = st.number_input("Más +2.5 Goles", value=co_def, step=0.05, format="%.2f")
        with col_qu: cuota_under = st.number_input("Menos -2.5 Goles", value=cu_def, step=0.05, format="%.2f")
        with col_qby: cuota_btts_si = st.number_input("BTTS (SÍ)", value=cby_def, step=0.05, format="%.2f")
        with col_qbn: cuota_btts_no = st.number_input("BTTS (NO)", value=cbn_def, step=0.05, format="%.2f")
        with col_qco: cuota_cor_over = st.number_input("Más +9.5 Córners", value=cco_def, step=0.05, format="%.2f")
        with col_qcu: cuota_cor_under = st.number_input("Menos -9.5 Córners", value=ccu_def, step=0.05, format="%.2f")

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
                    
                    res_col1, res_col2, res_col3, res_col4 = st.columns(4)
                    with res_col1:
                        st.markdown("### 🏆 Probabilidades 1X2")
                        st.write(f"🏠 Local: **{float(pred['mercado_1X2']['Victoria_Local']):.2f}%**")
                        st.write(f"🤝 Empate: **{float(pred['mercado_1X2']['Empate']):.2f}%**")
                        st.write(f"✈️ Visitante: **{float(pred['mercado_1X2']['Victoria_Visitante']):.2f}%**")
                    with res_col2:
                        st.markdown("### 🥅 Goles (+/- 2.5)")
                        st.write(f"🔼 Más de 2.5: **{float(pred['mercado_goles']['Mas_de_2.5']):.2f}%**")
                        st.write(f"🔽 Menos de 2.5: **{float(pred['mercado_goles']['Menos_de_2.5']):.2f}%**")
                    with res_col3:
                        st.markdown("### ⚽ Ambos Marcan (BTTS)")
                        st.write(f"✅ SÍ marcan: **{float(pred['mercado_btts']['Ambos_Marcan_Si']):.2f}%**")
                        st.write(f"❌ NO marcan: **{float(pred['mercado_btts']['Ambos_Marcan_No']):.2f}%**")
                    with res_col4:
                        st.markdown("### 🚩 Córners (+/- 9.5)")
                        p_co_val = float(pred.get('mercado_corners', {}).get('Mas_de_9.5', 50.0))
                        p_cu_val = float(pred.get('mercado_corners', {}).get('Menos_de_9.5', 50.0))
                        st.write(f"🔼 Más de 9.5: **{p_co_val:.2f}%**")
                        st.write(f"🔽 Menos de 9.5: **{p_cu_val:.2f}%**")

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
                    prob_casa_cor_over = (1 / cuota_cor_over) * 100 if cuota_cor_over > 0 else 0
                    prob_casa_cor_under = (1 / cuota_cor_under) * 100 if cuota_cor_under > 0 else 0
                    
                    # 2. Extraer probabilidades de la IA
                    prob_ia_1 = float(pred['mercado_1X2']['Victoria_Local'])
                    prob_ia_X = float(pred['mercado_1X2']['Empate'])
                    prob_ia_2 = float(pred['mercado_1X2']['Victoria_Visitante'])
                    prob_ia_over = float(pred['mercado_goles']['Mas_de_2.5'])
                    prob_ia_under = float(pred['mercado_goles']['Menos_de_2.5'])
                    prob_ia_btts_si = float(pred['mercado_btts']['Ambos_Marcan_Si'])
                    prob_ia_btts_no = float(pred['mercado_btts']['Ambos_Marcan_No'])
                    prob_ia_cor_over = float(pred.get('mercado_corners', {}).get('Mas_de_9.5', 50.0))
                    prob_ia_cor_under = float(pred.get('mercado_corners', {}).get('Menos_de_9.5', 50.0))
                    
                    # 3. Evaluar condiciones de Value Bet
                    val_1 = prob_ia_1 > (prob_casa_1 + 2.0) and prob_ia_1 >= umbral_prob
                    val_X = prob_ia_X > (prob_casa_X + 2.0) and prob_ia_X >= umbral_prob
                    val_2 = prob_ia_2 > (prob_casa_2 + 2.0) and prob_ia_2 >= umbral_prob
                    val_over = prob_ia_over > (prob_casa_over + 2.0) and prob_ia_over >= umbral_prob
                    val_under = prob_ia_under > (prob_casa_under + 2.0) and prob_ia_under >= umbral_prob
                    val_btts_si = prob_ia_btts_si > (prob_casa_btts_si + 2.0) and prob_ia_btts_si >= umbral_prob
                    val_btts_no = prob_ia_btts_no > (prob_casa_btts_no + 2.0) and prob_ia_btts_no >= umbral_prob
                    val_cor_over = prob_ia_cor_over > (prob_casa_cor_over + 2.0) and prob_ia_cor_over >= umbral_prob
                    val_cor_under = prob_ia_cor_under > (prob_casa_cor_under + 2.0) and prob_ia_cor_under >= umbral_prob
                    
                    hay_valor = False
                    
                    # 4. Imprimir informes detallados
                    if val_1:
                        st.info(f"🏠 **Victoria Local (1):** ¡INVERSIÓN RECOMENDADA! Cuota {cuota_1} (Casa: {prob_casa_1:.1f}% vs IA: **{prob_ia_1:.1f}%**). Ventaja: **+{prob_ia_1 - prob_casa_1:.1f}%**.")
                        hay_valor = True
                    if val_X:
                        st.info(f"🤝 **Empate (X):** ¡INVERSIÓN RECOMENDADA! Cuota {cuota_X} (Casa: {prob_casa_X:.1f}% vs IA: **{prob_ia_X:.1f}%**). Ventaja: **+{prob_ia_X - prob_casa_X:.1f}%**.")
                        hay_valor = True
                    if val_2:
                        st.info(f"✈️ **Victoria Visitante (2):** ¡INVERSIÓN RECOMENDADA! Cuota {cuota_2} (Casa: {prob_casa_2:.1f}% vs IA: **{prob_ia_2:.1f}%**). Ventaja: **+{prob_ia_2 - prob_casa_2:.1f}%**.")
                        hay_valor = True
                    if val_over:
                        st.success(f"🔼 **Más de 2.5 Goles:** ¡INVERSIÓN RECOMENDADA! Cuota {cuota_over} (Casa: {prob_casa_over:.1f}% vs IA: **{prob_ia_over:.1f}%**). Ventaja: **+{prob_ia_over - prob_casa_over:.1f}%**.")
                        hay_valor = True
                    if val_under:
                        st.success(f"🔽 **Menos de 2.5 Goles:** ¡INVERSIÓN RECOMENDADA! Cuota {cuota_under} (Casa: {prob_casa_under:.1f}% vs IA: **{prob_ia_under:.1f}%**). Ventaja: **+{prob_ia_under - prob_casa_under:.1f}%**.")
                        hay_valor = True
                    if val_btts_si:
                        st.success(f"⚽ **Ambos Marcan (SÍ):** ¡INVERSIÓN RECOMENDADA! Cuota {cuota_btts_si} (Casa: {prob_casa_btts_si:.1f}% vs IA: **{prob_ia_btts_si:.1f}%**). Ventaja: **+{prob_ia_btts_si - prob_casa_btts_si:.1f}%**.")
                        hay_valor = True
                    if val_btts_no:
                        st.success(f"🚫 **Ambos Marcan (NO):** ¡INVERSIÓN RECOMENDADA! Cuota {cuota_btts_no} (Casa: {prob_casa_btts_no:.1f}% vs IA: **{prob_ia_btts_no:.1f}%**). Ventaja: **+{prob_ia_btts_no - prob_casa_btts_no:.1f}%**.")
                        hay_valor = True
                    if val_cor_over:
                        st.success(f"🚩 **Más de 9.5 Córners:** ¡INVERSIÓN RECOMENDADA! Cuota {cuota_cor_over} (Casa: {prob_casa_cor_over:.1f}% vs IA: **{prob_ia_cor_over:.1f}%**). Ventaja: **+{prob_ia_cor_over - prob_casa_cor_over:.1f}%**.")
                        hay_valor = True
                    if val_cor_under:
                        st.success(f"🚩 **Menos de 9.5 Córners:** ¡INVERSIÓN RECOMENDADA! Cuota {cuota_cor_under} (Casa: {prob_casa_cor_under:.1f}% vs IA: **{prob_ia_cor_under:.1f}%**). Ventaja: **+{prob_ia_cor_under - prob_casa_cor_under:.1f}%**.")
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

                # SECCIÓN CÓRNERS ESTADÍSTICA
                if 'HC' in df_loc.columns and 'AC' in df_loc.columns:
                    df_loc_cor = df_loc.dropna(subset=['HC', 'AC'])
                    df_vis_cor = df_vis.dropna(subset=['HC', 'AC'])
                    
                    if not df_loc_cor.empty and not df_vis_cor.empty:
                        st.markdown("---")
                        st.markdown("### 🚩 Estadísticas de Córners")
                        cor_c1, cor_c2 = st.columns(2)
                        
                        with cor_c1:
                            cor_fav_loc = df_loc_cor['HC'].mean()
                            cor_con_loc = df_loc_cor['AC'].mean()
                            tot_cor_loc = df_loc_cor['HC'] + df_loc_cor['AC']
                            st.markdown(f"**{local} (Local):**")
                            st.write(f"🎯 Córners a favor (Media): **{cor_fav_loc:.2f}**")
                            st.write(f"🛡️ Córners en contra (Media): **{cor_con_loc:.2f}**")
                            st.write(f"🚩 Partido con +8.5 córners: **{((tot_cor_loc > 8.5).mean())*100:.1f}%**")
                            st.write(f"🚩 Partido con +9.5 córners: **{((tot_cor_loc > 9.5).mean())*100:.1f}%**")
                            st.write(f"🚩 Partido con +10.5 córners: **{((tot_cor_loc > 10.5).mean())*100:.1f}%**")

                        with cor_c2:
                            cor_fav_vis = df_vis_cor['AC'].mean()
                            cor_con_vis = df_vis_cor['HC'].mean()
                            tot_cor_vis = df_vis_cor['HC'] + df_vis_cor['AC']
                            st.markdown(f"**{visitante} (Visitante):**")
                            st.write(f"🎯 Córners a favor (Media): **{cor_fav_vis:.2f}**")
                            st.write(f"🛡️ Córners en contra (Media): **{cor_con_vis:.2f}**")
                            st.write(f"🚩 Partido con +8.5 córners: **{((tot_cor_vis > 8.5).mean())*100:.1f}%**")
                            st.write(f"🚩 Partido con +9.5 córners: **{((tot_cor_vis > 9.5).mean())*100:.1f}%**")
                            st.write(f"🚩 Partido con +10.5 córners: **{((tot_cor_vis > 10.5).mean())*100:.1f}%**")
                
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

# ==========================================
# PESTAÑA 4: TRACKER IN-PLAY & LIVE SNIPER
# ==========================================
with tab4:
    st.subheader("⏱️ Tracker In-Play & Simulador de Valor en Directo (Live Sniper)")
    st.markdown("""
    *Cuando una apuesta tiene valor pre-partido, el paso de los minutos (ej. minuto 15 a 30 con 0-0) hace que la cuota en Bet365 **suba exponencialmente**. 
    Esta herramienta calcula el **Valor Esperado Dinámico ($EV\%$)** y te indica el **momento óptimo de entrada (*Sweet Spot*)** antes de que el tiempo restante sea insuficiente.*
    """)

    # 1. SELECCIÓN DE PARTIDO Y MERCADO
    col_p1, col_p2 = st.columns([2, 2])
    
    lista_partidos_jornada = []
    if df_jornada is not None and not df_jornada.empty:
        for _, r in df_jornada.iterrows():
            lista_partidos_jornada.append(f"{normalizar_nombre(r['HomeTeam'])} vs {normalizar_nombre(r['AwayTeam'])}")
            
    with col_p1:
        if lista_partidos_jornada:
            partido_sel = st.selectbox("⚽ Selecciona el Partido en Vivo:", lista_partidos_jornada, index=0)
            p_local, p_visit = partido_sel.split(" vs ")
        else:
            p_local = local
            p_visit = visitante
            st.info(f"Analizando: **{p_local} vs {p_visit}**")

    with col_p2:
        mercado_sel = st.selectbox("🎯 Mercado a Monitorizar:", [
            "Victoria Local (1)",
            "Victoria Visitante (2)",
            "Más de 2.5 Goles",
            "Ambos Marcan (BTTS: SÍ)",
            "Más de 9.5 Córners"
        ])

    # 2. OBTENER PROBABILIDADES BASE PRE-MATCH DE LA IA
    c1_ini, cx_ini, c2_ini = 2.00, 3.40, 3.20
    co_ini, cu_ini = 1.90, 1.90
    cby_ini, cbn_ini = 1.90, 1.90
    cco_ini, ccu_ini = 1.83, 1.83

    if df_jornada is not None and not df_jornada.empty:
        for _, r in df_jornada.iterrows():
            if normalizar_nombre(r['HomeTeam']) == p_local and normalizar_nombre(r['AwayTeam']) == p_visit:
                c1_ini = float(r.get('B365H', 2.00)) if pd.notna(r.get('B365H')) else 2.00
                c2_ini = float(r.get('B365A', 3.20)) if pd.notna(r.get('B365A')) else 3.20
                co_ini = float(r.get('B365_Over25', 1.90)) if pd.notna(r.get('B365_Over25')) else 1.90
                cby_ini = float(r.get('B365_BTTS_Y', 1.90)) if pd.notna(r.get('B365_BTTS_Y')) else 1.90
                cco_ini = float(r.get('B365_Over95_Corners', 1.83)) if pd.notna(r.get('B365_Over95_Corners')) else 1.83
                break

    # Consultar IA Pre-Partido
    datos_base = {
        "elo_local": float(obtener_ultimo_elo(p_local)),
        "elo_visitante": float(obtener_ultimo_elo(p_visit)),
        "B365H": c1_ini, "B365D": cx_ini, "B365A": c2_ini
    }
    
    prob_ia_base = 50.0
    cuota_pre_base = 1.90
    
    try:
        r_api = requests.post("http://127.0.0.1:8000/predecir", json=datos_base, timeout=3)
        if r_api.status_code == 200:
            pred_base = r_api.json()
            if mercado_sel == "Victoria Local (1)":
                prob_ia_base = float(pred_base['mercado_1X2']['Victoria_Local'])
                cuota_pre_base = c1_ini
            elif mercado_sel == "Victoria Visitante (2)":
                prob_ia_base = float(pred_base['mercado_1X2']['Victoria_Visitante'])
                cuota_pre_base = c2_ini
            elif mercado_sel == "Más de 2.5 Goles":
                prob_ia_base = float(pred_base['mercado_goles']['Mas_de_2.5'])
                cuota_pre_base = co_ini
            elif mercado_sel == "Ambos Marcan (BTTS: SÍ)":
                prob_ia_base = float(pred_base['mercado_btts']['Ambos_Marcan_Si'])
                cuota_pre_base = cby_ini
            elif mercado_sel == "Más de 9.5 Córners":
                prob_ia_base = float(pred_base.get('mercado_corners', {}).get('Mas_de_9.5', 52.0))
                cuota_pre_base = cco_ini
    except Exception:
        pass

    st.markdown("---")

    # 3. CONTROLES DE CONDICIONES EN DIRECTO
    st.markdown("### 🎛️ Panel de Control de Condiciones en Directo")
    
    c_live1, c_live2, c_live3, c_live4 = st.columns([3, 2, 2, 2])
    
    with c_live1:
        minuto_live = st.slider("⏱️ Minuto de Juego Actual:", min_value=0, max_value=90, value=25, step=1)
    
    with c_live2:
        goles_loc_live = st.number_input(f"⚽ Goles {p_local}:", min_value=0, max_value=10, value=0, step=1)
    
    with c_live3:
        goles_vis_live = st.number_input(f"⚽ Goles {p_visit}:", min_value=0, max_value=10, value=0, step=1)
        
    with c_live4:
        rojas = st.selectbox("🟥 Tarjetas Rojas:", ["Ninguna", f"Roja a {p_local}", f"Roja a {p_visit}"])

    # 4. ESTIMACIÓN DE CUOTA EN VIVO Y CÁLCULO CONDICIONAL
    goles_totales_live = goles_loc_live + goles_vis_live
    tiempo_restante_pct = max(0.0, (90.0 - minuto_live) / 90.0)
    
    # Estimación de cuota de Bet365 según el minuto y el marcador
    if mercado_sel == "Más de 2.5 Goles":
        if goles_totales_live >= 3:
            cuota_live_sugerida = 1.05
            prob_restante_estimada = 99.0
        elif goles_totales_live == 2:
            cuota_live_sugerida = round(max(1.10, cuota_pre_base * (0.6 + 0.5 * (minuto_live / 90.0))), 2)
            prob_restante_estimada = min(95.0, prob_ia_base * 1.35 * (0.4 + 0.6 * tiempo_restante_pct))
        elif goles_totales_live == 1:
            cuota_live_sugerida = round(max(1.20, cuota_pre_base * (0.8 + 0.8 * (minuto_live / 90.0))), 2)
            prob_restante_estimada = prob_ia_base * (0.3 + 0.7 * (tiempo_restante_pct ** 0.8))
        else: # 0-0
            cuota_live_sugerida = round(cuota_pre_base * (1.0 + 1.6 * ((minuto_live / 90.0) ** 1.2)), 2)
            prob_restante_estimada = prob_ia_base * (tiempo_restante_pct ** 0.7)

    elif mercado_sel == "Ambos Marcan (BTTS: SÍ)":
        if goles_loc_live > 0 and goles_vis_live > 0:
            cuota_live_sugerida = 1.02
            prob_restante_estimada = 99.0
        elif goles_loc_live > 0 or goles_vis_live > 0:
            cuota_live_sugerida = round(max(1.15, cuota_pre_base * (0.85 + 0.9 * (minuto_live / 90.0))), 2)
            prob_restante_estimada = prob_ia_base * 1.2 * (0.2 + 0.8 * tiempo_restante_pct)
        else:
            cuota_live_sugerida = round(cuota_pre_base * (1.0 + 1.5 * ((minuto_live / 90.0) ** 1.2)), 2)
            prob_restante_estimada = prob_ia_base * (tiempo_restante_pct ** 0.75)

    elif mercado_sel == "Victoria Local (1)":
        dif_goles = goles_loc_live - goles_vis_live
        if dif_goles > 0:
            cuota_live_sugerida = round(max(1.04, cuota_pre_base * (0.4 + 0.6 * (1.0 - tiempo_restante_pct))), 2)
            prob_restante_estimada = min(98.0, prob_ia_base * 1.4)
        elif dif_goles == 0:
            cuota_live_sugerida = round(cuota_pre_base * (1.0 + 1.4 * (minuto_live / 90.0)), 2)
            prob_restante_estimada = prob_ia_base * (0.35 + 0.65 * (tiempo_restante_pct ** 0.6))
        else:
            cuota_live_sugerida = round(cuota_pre_base * (2.2 + 2.5 * (minuto_live / 90.0)), 2)
            prob_restante_estimada = prob_ia_base * 0.3 * tiempo_restante_pct

    elif mercado_sel == "Victoria Visitante (2)":
        dif_goles = goles_vis_live - goles_loc_live
        if dif_goles > 0:
            cuota_live_sugerida = round(max(1.04, cuota_pre_base * (0.4 + 0.6 * (1.0 - tiempo_restante_pct))), 2)
            prob_restante_estimada = min(98.0, prob_ia_base * 1.4)
        elif dif_goles == 0:
            cuota_live_sugerida = round(cuota_pre_base * (1.0 + 1.4 * (minuto_live / 90.0)), 2)
            prob_restante_estimada = prob_ia_base * (0.35 + 0.65 * (tiempo_restante_pct ** 0.6))
        else:
            cuota_live_sugerida = round(cuota_pre_base * (2.2 + 2.5 * (minuto_live / 90.0)), 2)
            prob_restante_estimada = prob_ia_base * 0.3 * tiempo_restante_pct

    else: # Córners
        cuota_live_sugerida = round(cuota_pre_base * (1.0 + 1.2 * (minuto_live / 90.0)), 2)
        prob_restante_estimada = prob_ia_base * (tiempo_restante_pct ** 0.5)

    # Ajuste por tarjetas rojas
    if rojas == f"Roja a {p_local}":
        if "Local" in mercado_sel: prob_restante_estimada *= 0.65
        elif "Visitante" in mercado_sel: prob_restante_estimada = min(95.0, prob_restante_estimada * 1.35)
    elif rojas == f"Roja a {p_visit}":
        if "Local" in mercado_sel: prob_restante_estimada = min(95.0, prob_restante_estimada * 1.35)
        elif "Visitante" in mercado_sel: prob_restante_estimada *= 0.65

    # Input de cuota live real o editable
    col_cuota1, col_cuota2 = st.columns([2, 2])
    with col_cuota1:
        cuota_live_usuario = st.number_input(
            "💰 Cuota Actual en Bet365 (Live):",
            min_value=1.01, max_value=50.0,
            value=float(cuota_live_sugerida),
            step=0.05,
            format="%.2f",
            help="Introduce la cuota que ves en Bet365 ahora mismo o usa la sugerida por el modelo matemático."
        )
    with col_cuota2:
        st.write("")
        st.write("")
        st.caption(f"💡 Cuota Pre-Match: **{cuota_pre_base:.2f}** | Cuota Live Estimada: **{cuota_live_sugerida:.2f}**")

    # 5. CÁLCULO DE EXPECTED VALUE (EV%)
    prob_casa_live = (1.0 / cuota_live_usuario) * 100.0 if cuota_live_usuario > 0 else 0
    ev_live_pct = ((prob_restante_estimada / 100.0) * cuota_live_usuario - 1.0) * 100.0

    st.markdown("---")

    # 6. MÉTRICAS Y SEMÁFORO DE ENTRADA
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Probabilidad Inicial IA", f"{prob_ia_base:.1f}%")
    m_col2.metric("Probabilidad Restante Live", f"{prob_restante_estimada:.1f}%", delta=f"{prob_restante_estimada - prob_ia_base:.1f}%")
    m_col3.metric("Cuota Bet365 Live", f"{cuota_live_usuario:.2f}", delta=f"+{cuota_live_usuario - cuota_pre_base:.2f}" if cuota_live_usuario >= cuota_pre_base else f"{cuota_live_usuario - cuota_pre_base:.2f}")
    m_col4.metric("Valor Esperado (EV%)", f"{ev_live_pct:+.1f}%", delta_color="normal" if ev_live_pct > 0 else "inverse")

    st.markdown("### 🚦 Semáforo de Decisión Live (*Sniper Decision*)")
    
    if ev_live_pct >= 8.0 and prob_restante_estimada >= 35.0:
        st.success(f"""
        🟢 **¡MOMENTO ÓPTIMO DE ENTRADA (SNIPER LIVE)!**
        * La cuota en Bet365 ha subido a **{cuota_live_usuario:.2f}** (frente a {cuota_pre_base:.2f} inicial).
        * La probabilidad restante (**{prob_restante_estimada:.1f}%**) supera ampliamente la probabilidad implícita de la casa (**{prob_casa_live:.1f}%**).
        * Ventaja matemática actual: **{ev_live_pct:+.1f}% de Valor Esperado**. Es un punto de entrada con máxima rentabilidad.
        """)
    elif ev_live_pct > 0.0:
        st.warning(f"""
        🟡 **SEGUIMIENTO / ESPERAR (ZONA DE CRECIMIENTO DE VALOR)**
        * Hay ventaja matemática (**{ev_live_pct:+.1f}%**), pero la cuota puede subir aún más en los próximos 5-10 minutos si el marcador no se mueve.
        * Recomendación: Mantén la atención en el partido y busca entrar cuando la cuota ofrezca un $+EV$ superior al +8%.
        """)
    else:
        st.error(f"""
        🔴 **ALTO RIESGO / DESISTIR DE LA APUESTA**
        * Con el minuto **{minuto_live}'** y el marcador actual, la probabilidad restante (**{prob_restante_estimada:.1f}%**) es inferior a la exigida por la cuota {cuota_live_usuario:.2f} (EV: **{ev_live_pct:+.1f}%**).
        * No hay ventaja matemática en este momento. Es mejor no entrar o buscar otro partido.
        """)

    st.markdown("---")

    # 7. GRÁFICA DE LA CURVA DE VALOR ESPERADO (PLOTLY)
    st.markdown("### 📈 Curva de Evolución del Valor en Directo (0' a 90')")
    st.caption("Esta curva muestra cómo varía la ventaja matemática ($EV\%$) si el partido se mantiene en las condiciones actuales a lo largo de los minutos.")

    minutos_eje = list(range(0, 91, 5))
    ev_eje = []
    prob_eje = []
    cuotas_eje = []

    for m in minutos_eje:
        t_pct = max(0.0, (90.0 - m) / 90.0)
        # Estimación de cuota y prob en ese minuto
        if mercado_sel == "Más de 2.5 Goles":
            c_est = round(cuota_pre_base * (1.0 + 1.6 * ((m / 90.0) ** 1.2)), 2) if goles_totales_live == 0 else max(1.10, cuota_pre_base * (0.8 + 0.8 * (m / 90.0)))
            p_est = prob_ia_base * (t_pct ** 0.7) if goles_totales_live == 0 else min(95.0, prob_ia_base * 1.35 * (0.4 + 0.6 * t_pct))
        elif mercado_sel == "Ambos Marcan (BTTS: SÍ)":
            c_est = round(cuota_pre_base * (1.0 + 1.5 * ((m / 90.0) ** 1.2)), 2) if goles_totales_live == 0 else max(1.15, cuota_pre_base * (0.85 + 0.9 * (m / 90.0)))
            p_est = prob_ia_base * (t_pct ** 0.75) if goles_totales_live == 0 else prob_ia_base * 1.2 * (0.2 + 0.8 * t_pct)
        else:
            c_est = round(cuota_pre_base * (1.0 + 1.4 * (m / 90.0)), 2)
            p_est = prob_ia_base * (0.35 + 0.65 * (t_pct ** 0.6))
            
        ev_calc = ((p_est / 100.0) * c_est - 1.0) * 100.0
        ev_eje.append(round(ev_calc, 1))
        prob_eje.append(round(p_est, 1))
        cuotas_eje.append(round(c_est, 2))

    df_curva = pd.DataFrame({
        "Minuto": minutos_eje,
        "Valor_Esperado_EV": ev_eje,
        "Probabilidad_Restante": prob_eje,
        "Cuota_Estimada": cuotas_eje
    })

    fig_curva = px.line(
        df_curva, x="Minuto", y="Valor_Esperado_EV",
        title=f"Evolución del Valor Esperado ({mercado_sel}) - Sweet Spot",
        labels={"Valor_Esperado_EV": "Valor Esperado EV (%)", "Minuto": "Minuto de Juego"},
        markers=True
    )
    
    # Línea de referencia en EV 0%
    fig_curva.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Punto de Equilibrio (0% EV)")
    # Línea vertical del minuto actual
    fig_curva.add_vline(x=minuto_live, line_dash="dot", line_color="orange", annotation_text=f"Minuto Actual ({minuto_live}')")
    
    st.plotly_chart(fig_curva, width='stretch')

    st.markdown("---")

    # 8. CALCULADORA DE FRECUENCIA DE API Y TOKENS GRATUITOS
    st.markdown("### 🛡️ Frecuencia de Peticiones y Control de Tokens Gratuitos")
    
    col_t1, col_t2 = st.columns([2, 2])
    with col_t1:
        st.markdown("""
        **Límites de tus APIs:**
        * **Odds-API.io (Cuotas Live Bet365):** ~500 peticiones gratuitas / mes.
        * **Football-Data.org (Minuto y Marcador):** 10 peticiones / minuto (600/hora).
        """)
        
    with col_t2:
        freq_minutos = st.slider("⏱️ Frecuencia de Consulta Deseada (Minutos):", min_value=1, max_value=15, value=4, step=1)
        peticiones_partido = int(90 / freq_minutos)
        st.info(f"📊 A **1 consulta cada {freq_minutos} minutos**, consumirás **{peticiones_partido} peticiones** por cada partido completo de 90 minutos.")

    st.caption("💡 **Regla de Oro:** Para monitorizar partidos en vivo sin agotar nunca tu cuota gratuita mensual de Odds-API, se recomienda consultar las cuotas cada **3 a 5 minutos** o actualizar manualmente en momentos clave (minuto 15', 30', descanso y 60').")
