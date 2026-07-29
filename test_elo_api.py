import requests
import time

def obtener_elo_robusto(club, fecha):
    url = f"http://clubelo.com/api/Elo?club={club}&date={fecha}"
    
    # Intentamos 3 veces si nos da error
    for intento in range(3):
        try:
            response = requests.get(url, timeout=10)
            # Verificamos si la respuesta es realmente JSON y no HTML
            if response.status_code == 200 and response.headers.get('Content-Type') == 'application/json':
                return response.json()
            else:
                print(f"Intento {intento+1}: API sobrecargada, esperando 5 segundos...")
                time.sleep(5)
        except:
            time.sleep(5)
    return None

if __name__ == "__main__":
    print("Consultando ClubElo...")
    resultado = obtener_elo_robusto("RealMadrid", "2024-05-01")
    print("Resultado obtenido:", resultado)