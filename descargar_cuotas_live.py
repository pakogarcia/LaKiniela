import os
import sys
import json
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Asegurar codificación UTF-8 en salida estándar para consolas de Windows
try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

load_dotenv()
API_KEY = os.getenv("THE_ODDS_API_KEY")

def cargar_mapeo():
    archivo_json = 'mapeo_equipos.json'
    if os.path.exists(archivo_json):
        with open(archivo_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

MAPEO_EQUIPOS = cargar_mapeo()

def normalizar_nombre(nombre_raw):
    if not nombre_raw:
        return ""
    nombre = str(nombre_raw).strip()
    if nombre in MAPEO_EQUIPOS:
        return MAPEO_EQUIPOS[nombre]
    
    # Fallback: limpieza de prefijos y sufijos comunes
    nombre_limpio = nombre
    for prefijo in ["FC ", "CD ", "UD ", "SD ", "RC ", "RCD ", "CF ", "AD ", "CE ", "CA "]:
        if nombre_limpio.startswith(prefijo):
            nombre_limpio = nombre_limpio[len(prefijo):].strip()
    for sufijo in [" CF", " FC", " CD", " UD", " SD", " SAD", " Seville", " San Sebastian", " San Sebastián", " Barcelona", " Madrid"]:
        if nombre_limpio.endswith(sufijo):
            nombre_limpio = nombre_limpio[:-len(sufijo)].strip()
            
    if nombre_limpio in MAPEO_EQUIPOS:
        return MAPEO_EQUIPOS[nombre_limpio]
        
    return nombre

def descargar_jornada_odds_io():
    if not API_KEY:
        print("❌ Error: No se encuentra la variable THE_ODDS_API_KEY en el archivo .env")
        return

    print("🌐 Consultando partidos en Odds-API.io para LaLiga y LaLiga 2...")
    
    url_events = f"https://api.odds-api.io/v3/events?sport=football&apiKey={API_KEY}"
    
    try:
        res_events = requests.get(url_events, timeout=15)
        if res_events.status_code != 200:
            print(f"❌ Error al obtener eventos (Código {res_events.status_code}): {res_events.text[:200]}")
            return
            
        data_events = res_events.json()
        eventos = data_events.get('data', []) if isinstance(data_events, dict) else data_events
        
        ahora = datetime.now(timezone.utc)
        limite_dias = ahora + timedelta(days=7) # Ventana de 7 días para cubrir la jornada completa
        
        eventos_laliga = []
        
        for ev in eventos:
            if not isinstance(ev, dict):
                continue
            
            league_info = ev.get('league', {})
            league_name = (league_info.get('name', '') if isinstance(league_info, dict) else str(league_info)).lower()
            league_slug = (league_info.get('slug', '') if isinstance(league_info, dict) else '').lower()
            
            # Filtro por ligas españolas de primera y segunda división
            es_laliga = (
                'spain - laliga' in league_name or 
                'spain - laliga 2' in league_name or 
                'spain - segunda' in league_name or 
                'spain-laliga' in league_slug or
                'spain-segunda' in league_slug
            )
            
            if not es_laliga:
                continue
                
            # Validar fecha
            fecha_str = ev.get('date', ev.get('commence_time', ''))
            if not fecha_str:
                continue
                
            try:
                # Soporta ISO string como 2026-08-20T19:00:00Z
                fecha_partido = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
            except Exception:
                continue
                
            # Descartar partidos ya finalizados o muy lejanos
            if fecha_partido < ahora - timedelta(hours=3) or fecha_partido > limite_dias:
                continue
                
            eventos_laliga.append(ev)

        # Ordenar cronológicamente
        eventos_laliga = sorted(eventos_laliga, key=lambda x: x.get('date', x.get('commence_time', '')))
        
        print(f"✅ Se encontraron {len(eventos_laliga)} partidos de LaLiga / LaLiga 2 en la próxima jornada.")
        
        partidos = []
        
        for ev in eventos_laliga:
            event_id = ev.get('id')
            fecha_iso = ev.get('date', ev.get('commence_time', ''))
            local_raw = ev.get('home', ev.get('home_team', ''))
            visitante_raw = ev.get('away', ev.get('away_team', ''))
            
            if not event_id or not local_raw or not visitante_raw:
                continue
                
            local_norm = normalizar_nombre(local_raw)
            visitante_norm = normalizar_nombre(visitante_raw)
            
            # Formatear fecha legible DD/MM/YYYY HH:MM
            try:
                dt_obj = datetime.fromisoformat(fecha_iso.replace('Z', '+00:00'))
                fecha_legible = dt_obj.strftime("%d/%m/%Y %H:%M")
            except Exception:
                fecha_legible = fecha_iso
                
            url_odds = f"https://api.odds-api.io/v3/odds?apiKey={API_KEY}&eventId={event_id}&bookmakers=Bet365"
            b365_h, b365_d, b365_a = 0.0, 0.0, 0.0
            over25, under25 = 1.90, 1.90
            btts_y, btts_n = 1.90, 1.90
            corners_over95, corners_under95 = 1.83, 1.83
            
            try:
                res_odds = requests.get(url_odds, timeout=10)
                if res_odds.status_code == 200:
                    data_odds = res_odds.json()
                    bookmakers_b365 = data_odds.get('bookmakers', {}).get('Bet365', [])
                    
                    if isinstance(bookmakers_b365, list):
                        for m in bookmakers_b365:
                            if not isinstance(m, dict):
                                continue
                            m_name = m.get('name', '')
                            odds_list = m.get('odds', [])
                            if not isinstance(odds_list, list) or len(odds_list) == 0:
                                continue
                                
                            # 1. Mercado 1X2 (ML)
                            if m_name == 'ML':
                                first = odds_list[0]
                                try:
                                    b365_h = float(first.get('home', 0.0))
                                    b365_d = float(first.get('draw', 0.0))
                                    b365_a = float(first.get('away', 0.0))
                                except (ValueError, TypeError):
                                    pass
                                    
                            # 2. Mercado Goles Over/Under 2.5
                            if m_name in ['Goals Over/Under', 'Totals', 'Alternative Total Goals', 'Total Goals']:
                                for item in odds_list:
                                    if not isinstance(item, dict):
                                        continue
                                    if str(item.get('hdp', '')) == '2.5' or item.get('hdp') == 2.5:
                                        try:
                                            over25 = float(item.get('over', 1.90))
                                            under25 = float(item.get('under', 1.90))
                                            break
                                        except (ValueError, TypeError):
                                            pass
                                            
                            # 3. Mercado BTTS (Ambos Equipos Marcan - Tiempo Completo)
                            if m_name == 'Both Teams To Score':
                                first = odds_list[0]
                                try:
                                    btts_y = float(first.get('yes', 1.90))
                                    btts_n = float(first.get('no', 1.90))
                                except (ValueError, TypeError):
                                    pass

                            # 4. Mercado Córners Over/Under 9.5
                            if m_name in ['Corners Totals', 'Corners 2-Way', 'Corners', 'Alternative Corners']:
                                for item in odds_list:
                                    if not isinstance(item, dict):
                                        continue
                                    hdp_val = str(item.get('hdp', ''))
                                    if hdp_val in ['9.5', '10', '9']:
                                        try:
                                            if 'over' in item and 'under' in item:
                                                corners_over95 = float(item.get('over', 1.83))
                                                corners_under95 = float(item.get('under', 1.83))
                                                break
                                        except (ValueError, TypeError):
                                            pass
            except Exception as e_odds:
                print(f"⚠️ Error al obtener cuotas para {local_norm} vs {visitante_norm}: {e_odds}")

            partidos.append({
                "Date": fecha_legible,
                "HomeTeam": local_norm,
                "AwayTeam": visitante_norm,
                "B365H": round(b365_h, 2) if b365_h > 0 else 2.00,
                "B365D": round(b365_d, 2) if b365_d > 0 else 3.40,
                "B365A": round(b365_a, 2) if b365_a > 0 else 3.20,
                "B365_Over25": round(over25, 2),
                "B365_Under25": round(under25, 2),
                "B365_BTTS_Y": round(btts_y, 2),
                "B365_BTTS_N": round(btts_n, 2),
                "B365_Over95_Corners": round(corners_over95, 2),
                "B365_Under95_Corners": round(corners_under95, 2)
            })
            print(f" -> Partido: {local_norm} vs {visitante_norm} | 1X2: [{b365_h}, {b365_d}, {b365_a}] | +/-2.5: [{over25}, {under25}] | BTTS: [{btts_y}, {btts_n}] | Corners +/-9.5: [{corners_over95}, {corners_under95}]")
            
        df_proxima = pd.DataFrame(partidos)
        if not df_proxima.empty:
            df_proxima.to_csv("proxima_jornada.csv", index=False, encoding="utf-8")
            print(f"\n🎉 ¡Éxito! Se han guardado {len(df_proxima)} partidos con nombres estandarizados y cuotas en 'proxima_jornada.csv'.")
        else:
            print("⚠️ No se han encontrado partidos programados de LaLiga en el intervalo de fechas.")
            
    except Exception as e:
        print(f"❌ Excepción durante la descarga: {e}")

if __name__ == "__main__":
    descargar_jornada_odds_io()