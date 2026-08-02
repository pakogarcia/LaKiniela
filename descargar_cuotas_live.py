import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("THE_ODDS_API_KEY")

def descargar_la_liga_live():
    if not API_KEY:
        print("❌ ERROR: No se encuentra la variable 'THE_ODDS_API_KEY' en el archivo .env")
        return None

    print("🌐 Conectando con The Odds API para La Liga (Mercados: 1X2, Goles, BTTS)...")
    
    # URL directa a La Liga española, ahorrando peticiones
    url = "https://api.the-odds-api.com/v4/sports/soccer_spain_la_liga/odds/"
    
    # Pedimos los 3 mercados específicos y solo para Bet365
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h,totals,btts",
        "bookmakers": "bet365", 
        "oddsFormat": "decimal"
    }
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            print(f"❌ Error de la API: {response.status_code} - {response.text}")
            return None
            
        data = response.json()
        
        if not data:
            print("⚠️ No hay partidos de La Liga publicados en Bet365 en este momento.")
            return None
            
        lista_partidos = []
        
        for partido in data:
            fecha = partido.get("commence_time")
            home_team = partido.get("home_team")
            away_team = partido.get("away_team")
            
            # Inicializamos variables por defecto por si Bet365 aún no ha sacado algún mercado
            b365_h, b365_d, b365_a = 0.0, 0.0, 0.0
            cuota_mas_25, cuota_menos_25 = 0.0, 0.0
            cuota_btts_si, cuota_btts_no = 0.0, 0.0
            
            bookmakers = partido.get("bookmakers", [])
            if bookmakers:
                mercados = bookmakers[0].get("markets", [])
                for mercado in mercados:
                    key = mercado.get("key")
                    outcomes = mercado.get("outcomes", [])
                    
                    if key == "h2h":
                        for out in outcomes:
                            if out["name"] == home_team: b365_h = out["price"]
                            elif out["name"] == away_team: b365_a = out["price"]
                            elif out["name"] == "Draw": b365_d = out["price"]
                    
                    elif key == "totals":
                        for out in outcomes:
                            # Filtramos específicamente la línea de Más/Menos 2.5 goles
                            if out.get("point") == 2.5:
                                if out["name"] == "Over": cuota_mas_25 = out["price"]
                                elif out["name"] == "Under": cuota_menos_25 = out["price"]
                    
                    elif key == "btts":
                        for out in outcomes:
                            if out["name"] == "Yes": cuota_btts_si = out["price"]
                            elif out["name"] == "No": cuota_btts_no = out["price"]

            lista_partidos.append({
                "Date": fecha,
                "HomeTeam": home_team,
                "AwayTeam": away_team,
                "B365H": b365_h,
                "B365D": b365_d,
                "B365A": b365_a,
                "B365_Over25": cuota_mas_25,
                "B365_Under25": cuota_menos_25,
                "B365_BTTS_Y": cuota_btts_si,
                "B365_BTTS_N": cuota_btts_no
            })
            
        df = pd.DataFrame(lista_partidos)
        return df

    except Exception as e:
        print(f"❌ Error interno al consultar la API: {e}")
        return None

if __name__ == "__main__":
    df = descargar_la_liga_live()
    if df is not None and not df.empty:
        archivo_salida = "proxima_jornada.csv"
        df.to_csv(archivo_salida, index=False, encoding="utf-8")
        print(f"💾 Guardado con éxito en '{archivo_salida}'.")
        print(df.head())
    else:
        print("⚠️ No hay datos válidos para procesar.")