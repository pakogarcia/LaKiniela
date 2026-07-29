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

# LaQuiniela Predictor ⚽🤖

Sistema automatizado de predicción de partidos de fútbol (Primera y Segunda División) basado en Machine Learning (XGBoost y Random Forest) y análisis de métricas Elo.

## 📂 Bloque 1: Consolidación y Limpieza de Datos

En este bloque unificamos y depuramos los datos históricos en bruto de ambas categorías para generar un único dataset maestro coherente.

### Script Principal: `union.py`
Este script automatiza todo el proceso de preparación inicial:
1. **Carga**: Lee de forma segura los archivos históricos de Primera (`SP1_total.csv`) y Segunda (`SP2_total.csv`) División[cite: 1].
2. **Fusión**: Combina ambos datasets alineando automáticamente sus registros mediante `pandas`[cite: 1].
3. **Limpieza**: Filtra el conjunto de datos para conservar únicamente las columnas oficiales de rendimiento, estadísticas de juego y cuotas de apuestas necesarias[cite: 2].
4. **Exportación**: Genera el archivo maestro definitivo **`LaLiga_Dataset_Final.csv`** listo para el cálculo de Elo y el entrenamiento de los modelos.

### Cómo ejecutarlo:
```cmd
python union.py