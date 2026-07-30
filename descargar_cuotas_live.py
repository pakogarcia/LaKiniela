import os
import pandas as pd
from dotenv import load_dotenv
from odds_api import OddsAPIClient

load_dotenv()
API_KEY = os.getenv("THE_ODDS_API_KEY")

def descargar_la_liga_live():
    if not API_KEY:
        print("❌ ERROR: No se encuentra la variable 'THE_ODDS_API_KEY' en el archivo .env")
        return None

    print("🌐 Conectando con Odds-API.io para filtrar exclusivamente La Liga española...")
    client = OddsAPIClient(api_key=API_KEY)
    
    try:
        # Obtenemos los eventos de fútbol
        events = client.get_events(sport="football")
        
        if not events:
            print("⚠️ No se han encontrado eventos.")
            return None
            
        lista_partidos = []
        for evento in events:
            # Comprobación estricta de que la liga pertenezca exactamente a España / Primera División
            league_name = str(evento.get('league', '')).lower()
            country_name = str(evento.get('country', '')).lower()
            
            # Filtro riguroso para evitar confusiones con otras ligas
            if ('spain' in country_name or 'españa' in country_name) and ('laliga' in league_name or 'primera' in league_name or 'la liga' in league_name):
                event_id = evento.get('id')
                home_team = evento.get('participant1Name') or evento.get('home')
                away_team = evento.get('participant2Name') or evento.get('away')
                fecha = evento.get('startTime') or evento.get('date')
                
                b365_h, b365_d, b365_a = None, None, None
                try:
                    odds = client.get_event_odds(event_id=event_id)
                except Exception:
                    pass

                lista_partidos.append({
                    "Fecha": fecha,
                    "HomeTeam": home_team,
                    "AwayTeam": away_team,
                    "B365H": b365_h,
                    "B365D": b365_d,
                    "B365A": b365_a
                })
                
        df = pd.DataFrame(lista_partidos)
        return df

    except Exception as e:
        print(f"❌ Error al consultar la API: {e}")
        return None

if __name__ == "__main__":
    df = descargar_la_liga_live()
    if df is not None and not df.empty:
        archivo_salida = "proxima_jornada.csv"
        df.to_csv(archivo_salida, index=False, encoding="utf-8")
        print(f"💾 Guardado con éxito en '{archivo_salida}'.")
        print(df.head(10))
    else:
        print("⚠️ No hay partidos oficiales de La Liga disponibles en este momento.")