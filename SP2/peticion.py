import requests
import json

# Tu token de football-data.org
TOKEN = "7be18ac491154c619bc86896f6e3ab78"
HEADERS = {"X-Auth-Token": TOKEN}

# Códigos de competición en la API:
# 'PD' = Primera División (La Liga EA Sports)
# 'SD' = Segunda División (La Liga Hypermotion)
competicion = "PD" 

url = f"https://api.football-data.org/v4/competitions/{competicion}/matches"

print(f"Consultando la API de Football-Data para la competición {competicion}...")

try:
    response = requests.get(url, headers=HEADERS, timeout=10)
    
    print(f"Código de estado HTTP: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Competición: {data.get('competition', {}).get('name')}")
        matches = data.get("matches", [])
        print(f"Total de partidos devueltos: {len(matches)}")
        
        if matches:
            # Mostramos el último partido registrado como ejemplo de estructura
            print("\n--- Ejemplo del último partido devuelto ---")
            print(json.dumps(matches[-1], indent=2, ensure_ascii=False))
    else:
        print("❌ Error en la petición:", response.text)

except Exception as e:
    print(f"Error de conexión: {e}")