import pandas as pd
import os

def unificar_y_limpiar_datos():
    print("1. Cargando archivos de Primera y Segunda División...")
    
    # Comprobar que los archivos existen antes de cargarlos
    if not os.path.exists("SP1_total.csv") or not os.path.exists("SP2_total.csv"):
        print("❌ Error: No se encuentra 'SP1_total.csv' o 'SP2_total.csv' en la carpeta.")
        return

    # Cargar archivos de ambas divisiones
    df_primera = pd.read_csv("SP1_total.csv", sep=";")
    df_segunda = pd.read_csv("SP2_total.csv", sep=";")

    print(f"   - Filas Primera División (SP1): {len(df_primera)}")
    print(f"   - Filas Segunda División (SP2): {len(df_segunda)}")

    # 2. Unir ambos datasets alineando automáticamente las columnas
    print("2. Uniendo datasets...")
    df_total = pd.concat([df_primera, df_segunda], ignore_index=True)

    # 3. Definir la lista oficial de columnas limpias deseadas
    columnas_limpias = [
        'Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 
        'HTHG', 'HTAG', 'HTR', 'HS', 'AS', 'HST', 'AST', 'HF', 'AF', 
        'HC', 'AC', 'HY', 'AY', 'HR', 'AR', 'B365H', 'B365D', 'B365A', 
        'BbAvH', 'BbAvD', 'BbAvA', 'BbAv>2.5', 'BbAv<2.5', 'BbAvAHH', 'BbAvAHA'
    ]

    # 4. Filtrar para quedarnos únicamente con las columnas oficiales existentes
    print("3. Limpiando columnas innecesarias...")
    columnas_existentes = [col for col in columnas_limpias if col in df_total.columns]
    df_limpio = df_total[columnas_existentes]

    # 5. Guardar el dataset maestro unificado y limpio definitivo
    archivo_salida = "LaLiga_Dataset_Final.csv"
    df_limpio.to_csv(archivo_salida, index=False, sep=";")

    print(f"✨ ¡Proceso completado con éxito!")
    print(f"   - Dataset final guardado en: '{archivo_salida}'")
    print(f"   - Total de registros unificados y limpios: {len(df_limpio)}")

if __name__ == "__main__":
    unificar_y_limpiar_datos()