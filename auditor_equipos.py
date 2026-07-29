import pandas as pd

def auditar_coordenadas():
    print("🔍 Iniciando auditoría de equipos...")
    
    # 1. Cargar los equipos que ya tenemos en nuestro diccionario
    try:
        df_coords = pd.read_csv("coordenadas_equipos.csv", sep=",")
        # Convertimos la columna a un 'set' (conjunto) para hacer comparaciones ultra rápidas
        equipos_conocidos = set(df_coords['Equipo'].dropna().unique())
        print(f"✅ Encontrados {len(equipos_conocidos)} equipos en coordenadas_equipos.csv")
    except FileNotFoundError:
        print("❌ Error: No se encuentra el archivo 'coordenadas_equipos.csv'")
        return

    # 2. Cargar todos los equipos que existen en la base de datos histórica
    try:
        # Recuerda que el SP1 original usa punto y coma (;)
        df_partidos = pd.read_csv("SP1_total.csv", sep=";")
        equipos_historicos = set(df_partidos['HomeTeam'].dropna().unique())
        print(f"⚽ Encontrados {len(equipos_historicos)} equipos históricos en LaLiga (SP1_total.csv)")
    except FileNotFoundError:
        print("❌ Error: No se encuentra el archivo 'SP1_total.csv'")
        return

    # 3. Calcular la diferencia matemática (Los que están en la historia pero NO en el diccionario)
    equipos_faltantes = equipos_historicos - equipos_conocidos

    # 4. Mostrar el reporte final
    print("\n" + "="*40 + "\n📊 REPORTE DE AUDITORÍA\n" + "="*40)
    
    if len(equipos_faltantes) == 0:
        print("🎉 ¡Excelente! Tienes las coordenadas de TODOS los equipos históricos.")
        print("Puedes lanzar el script de clima masivo sin miedo.")
    else:
        print(f"⚠️ ATENCIÓN: Te faltan las coordenadas de {len(equipos_faltantes)} equipos.\n")
        print("Añade las siguientes líneas a tu 'coordenadas_equipos.csv' (busca su lat/lon en Google):")
        
        # Imprimimos la lista ordenada alfabéticamente y con formato CSV lista para copiar y pegar
        for equipo in sorted(equipos_faltantes):
            print(f"{equipo},LATITUD,LONGITUD")
            
        print("\n💡 Consejo: Una vez los rellenes, vuelve a ejecutar este script para comprobar que la lista se queda a cero.")

if __name__ == "__main__":
    auditar_coordenadas()