import pandas as pd
import requests

print("⏳ Cargando base de datos de equipos...")
try:
    df = pd.read_csv('LaLiga_Dataset_Final.csv')
    lista_equipos = sorted(df['HomeTeam'].dropna().unique().tolist())
except FileNotFoundError:
    print("❌ ERROR: No se encuentra 'LaLiga_Dataset_Final.csv'. Ejecuta primero entrenar_modelos.py")
    exit()

def obtener_ultimo_elo(equipo):
    df_equipo = df[(df['HomeTeam'] == equipo) | (df['AwayTeam'] == equipo)].copy()
    if not df_equipo.empty:
        ultima_fila = df_equipo.iloc[-1]
        if ultima_fila['HomeTeam'] == equipo:
            return ultima_fila['elo_local']
        else:
            return ultima_fila['elo_visitante']
    return 1.50 

print("\n⚽ SIMULADOR DE PREDICCIONES ⚽")
print("Ejemplo de equipos:", ", ".join(lista_equipos[:5]) + "...\n")

local = input("🏠 Introduce el nombre del Equipo Local: ")
visitante = input("✈️ Introduce el nombre del Equipo Visitante: ")

elo_loc = obtener_ultimo_elo(local)
elo_vis = obtener_ultimo_elo(visitante)

print(f"\n✅ ELO recuperado histórico para {local}: {elo_loc:.2f}")
print(f"✅ ELO recuperado histórico para {visitante}: {elo_vis:.2f}\n")

cuota_1 = float(input("💰 Cuota victoria Local (1): "))
cuota_X = float(input("💰 Cuota Empate (X): "))
cuota_2 = float(input("💰 Cuota victoria Visitante (2): "))

datos = {
    "elo_local": float(elo_loc),
    "elo_visitante": float(elo_vis),
    "B365H": cuota_1,
    "B365D": cuota_X,
    "B365A": cuota_2
}

# La API local por defecto de Uvicorn corre en el puerto 8000
url_api = "http://127.0.0.1:8000/predecir"

try:
    respuesta = requests.post(url_api, json=datos)
    if respuesta.status_code == 200:
        pred = respuesta.json()
        print("\n" + "⚽"*25)
        print(f"🎯 PREDICCIÓN FINAL: {local.upper()} vs {visitante.upper()}")
        print("⚽"*25)
        print("\n🏆 MERCADO 1X2:")
        print(f"   🟢 Victoria Local: {pred['mercado_1X2']['Victoria_Local']:.2f}%")
        print(f"   ⚪ Empate:         {pred['mercado_1X2']['Empate']:.2f}%")
        print(f"   🔴 Victoria Visit: {pred['mercado_1X2']['Victoria_Visitante']:.2f}%")
        print("\n🥅 MERCADO DE GOLES:")
        print(f"   🔥 Más de 2.5:   {pred['mercado_goles']['Mas_de_2.5']:.2f}%")
        print(f"   🧊 Menos de 2.5: {pred['mercado_goles']['Menos_de_2.5']:.2f}%")
        print("="*50)
    else:
        print(f"❌ Error en la API: Código {respuesta.status_code}")
except Exception as e:
    print(f"❌ Error de conexión. ¿Has encendido el servidor Uvicorn? Detalle: {e}")