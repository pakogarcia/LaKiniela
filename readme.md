# 📈 ML Sports Value Betting (LaKiniela)

Proyecto integral de Machine Learning y Analítica de Datos diseñado para predecir resultados de fútbol (Primera y Segunda División de España) y detectar "Value Bets" cruzando predicciones de IA con cuotas reales de casas de apuestas en tiempo real.

## 🎯 Objetivos del Proyecto
* Consolidar un pipeline de datos (ETL) extrayendo información histórica y en tiempo real.
* Entrenar modelos de Machine Learning para predecir probabilidades reales de victoria, empate o derrota.
* Integrar APIs externas (Meteorología y The Odds API) para enriquecer el contexto del evento.
* Desplegar un dashboard interactivo para la visualización de ineficiencias del mercado de apuestas.

## 🏗️ Arquitectura y Módulos
1. **Data Ingestion:** (Aquí explicaremos cómo obtenemos los CSV y las APIs).
2. **Feature Engineering:** (Aquí hablaremos del Clima y el cálculo del Elo).
3. **Machine Learning:** (Modelos usados, métricas de éxito).
4. **Dashboard:** (Streamlit).

## 💻 Tecnologías Utilizadas
* **Lenguaje:** Python 3.x
* **Librerías Core:** Pandas, Scikit-Learn, Streamlit, Requests
* **APIs:** The Odds API, [Nombre de tu API del clima]

## 🚀 Instalación y Uso

# LaKiniela Predictor

Sistema automatizado de predicción de partidos de fútbol (Primera y Segunda División) basado en Machine Learning (XGBoost y Random Forest) y análisis de métricas Elo.

## 📂 Bloque 1: Consolidación y Limpieza de Datos

En este bloque unificamos y depuramos los datos históricos en bruto de ambas categorías Primera y Segunda División de Fútbol de España para generar un único dataset maestro coherente.

### Script Principal: `union.py`
Este script automatiza todo el proceso de preparación inicial:
1. **Carga**: Lee de forma segura los archivos históricos de Primera (`SP1_total.csv`) y Segunda (`SP2_total.csv`) División[cite: 1].
2. **Fusión**: Combina ambos datasets alineando automáticamente sus registros mediante `pandas`[cite: 1].
3. **Limpieza**: Filtra el conjunto de datos para conservar únicamente las columnas oficiales de rendimiento, estadísticas de juego y cuotas de apuestas necesarias[cite: 2].
4. **Exportación**: Genera el archivo maestro definitivo **`LaLiga_Dataset_Final.csv`** listo para el cálculo de Elo y el entrenamiento de los modelos.

### Cómo ejecutarlo:
```cmd
python union.py
```

## ♟️ Bloque 2: Sistema de Ratings Elo

El Elo mide la fuerza relativa y actualizada de cada equipo de Primera y Segunda División. Se integra en nuestro pipeline para alimentar las variables predictivas de los modelos de Machine Learning.

### Archivos Clave:
* **`actualizar_elo.py`**: Diseñado para consultar la API de ClubElo de forma automatizada por fecha y club[cite: 3].
* **`descargar_elo_completo.py`**: Extrae la tabla histórica de ratings directamente desde el sitio web mediante scraping robusto (`BeautifulSoup` + `pandas`)[cite: 4].

> ⚠️ **Nota Importante sobre la Capacidad de la Página:** 
> La actualización en tiempo real de los ratings desde la web de ClubElo puede verse **imposibilitada u obstaculizada temporalmente** debido a restricciones de tráfico, límites de peticiones de la API o bloqueos de la plataforma externa. Por ello, el sistema prioriza el uso de archivos históricos locales (`EloSP1.csv`, `EloSP1_Historico.csv`) cuando la conexión directa no está disponible.


## ⛅ Bloque 3: Enriquecimiento Climático y Fusión Definitiva

Para dar mayor realismo y precisión a las predicciones de los partidos, el sistema incorpora variables meteorológicas históricas basadas en la ubicación geográfica de cada estadio.

### Scripts y Componentes Principales:
* **`auditor_coordenadas.py`**: Verifica que todos los equipos presentes en el histórico de partidos dispongan de sus respectivas coordenadas geográficas en `coordenadas_equipos.csv`[cite: 6].
* **`enriquecer_clima.py`**: Realiza peticiones masivas a la API de *Open-Meteo* utilizando la latitud y longitud del equipo local en la fecha exacta del partido. Incluye:
  * Control de reanudación automática si se interrumpe el proceso.
  * Auto-guardado de seguridad cada 100 registros (`SP1_con_clima.csv`)[cite: 7].
  * Detección de límites de peticiones (`LIMIT`) por restricciones de IP[cite: 7].
* **`fusionar_elo_clima.py`**: Consolida el pipeline uniendo los datos meteorológicos y los ratings Elo históricos mediante diccionarios optimizados de alto rendimiento, generando el archivo maestro definitivo **`LaLiga_Dataset_Final.csv`**[cite: 5].

## 🤖 Bloque 4: Entrenamiento de Modelos y API Predictiva

Una vez consolidado el dataset maestro con la información histórica, los ratings Elo y el clima, procedemos al entrenamiento de los algoritmos de Machine Learning y a la puesta en marcha de una API de inferencia.

### Archivos Clave:
* **`entrenar_modelos.py`**: Script encargado de:
  * Cruzar y alinear los datos de clima y Elo.
  * Preparar las variables predictivas (`elo_local`, `elo_visitante`, `dif_elo`, cuotas de apuestas `B365`).
  * Entrenar un **XGBoost Classifier** optimizado para el mercado **1X2** con ponderación de clases balanceadas[cite: 10].
  * Entrenar un **Random Forest Classifier** para el mercado de **Goles (Más/Menos de 2.5)**[cite: 10].
  * Serializar y guardar los modelos (`modelo_1x2_xgboost.pkl`, `modelo_goles_rf.pkl`, `label_encoder.pkl`)[cite: 10].
* **`api_predicciones.py`**: API ligera construida con **FastAPI** que carga los modelos serializados y expone un endpoint POST (`/predecir`) para calcular en tiempo real las probabilidades de cualquier enfrentamiento[cite: 9, 10].



## 🌐 Bloque 5: Interfaz de Usuario y Simulación

El proyecto incluye dos modalidades diferentes para interactuar con el motor predictivo y consultar las probabilidades de los partidos:

⚠️ Requisito previo para ambas interfaces:
Para que cualquiera de las interfaces pueda calcular las predicciones, el servidor de la API REST debe estar encendido y en funcionamiento en segundo plano ejecutando (en otra terminal):
  ```cmd
  uvicorn api_predicciones:app --reload

### 1. Interfaz Web Gráfica (Streamlit)
Permite seleccionar los equipos mediante desplegables visuales, configurar las cuotas de apuestas de forma interactiva y visualizar las probabilidades de los mercados 1X2 y de Goles de manera gráfica.
* **Archivo:** `app_web.py`
* **Ejecución:**
  ```cmd
  streamlit run app_web.py

### 2. Simulador Interactivo por Consola
Herramienta de texto orientada a la terminal para introducir los datos de los equipos y cuotas de forma rápida mediante entrada de teclado (input()).

* **Archivo:** `interfaz_usuario.py`
* **Ejecución:**
  ```cmd
  python interfaz_usuario.py


