import pandas as pd
import requests
from io import StringIO

def descargar_elo_robusto():
    url = "http://clubelo.com/ESP"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    print("🌍 Extrayendo ranking desde el sitio web de ClubElo...")
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Error al conectar: {response.status_code}")
            return

        # FORZAMOS LA LECTURA: Usamos BeautifulSoup para obtener el HTML 
        # y se lo pasamos a pandas como un string, no como una URL
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscamos todas las tablas en el HTML
        tablas_html = soup.find_all('table')
        
        tabla_encontrada = None
        for i, tabla in enumerate(tablas_html):
            # Convertimos la tabla HTML a un DataFrame de pandas
            df = pd.read_html(StringIO(str(tabla)))[0]
            
            # Buscamos si el encabezado o la primera fila contiene 'Club'
            columnas = [str(col).lower() for col in df.columns]
            if 'club' in columnas:
                tabla_encontrada = df
                print(f"✅ ¡Tabla encontrada en el índice {i}!")
                break
        
        if tabla_encontrada is not None:
            tabla_encontrada.to_csv('EloSP1_Historico.csv', index=False, sep=';')
            print(f"💾 Guardado con éxito. Filas: {len(tabla_encontrada)}")
        else:
            print("❌ No se encontró la tabla de clubes.")
            
    except Exception as e:
        print(f"❌ Error al extraer: {e}")