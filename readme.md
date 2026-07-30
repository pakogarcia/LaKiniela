# 

⚽ LaKiniela: Sistema de Trading Deportivo con IA

**LaKiniela** es una herramienta integral de MLOps y Data Science diseñada para predecir resultados de fútbol (Primera y Segunda División de España) y detectar oportunidades de inversión (**Value Bets**) cruzando predicciones de Inteligencia Artificial con cuotas reales de casas de apuestas en tiempo real.

## **🚀 Características Principales**

> * **Radar Automático de Value Bets:** Escanea la jornada actual cruzando las cuotas de The Odds API con las predicciones del modelo para encontrar ineficiencias en el mercado (1X2).  
> * **Predictor Inteligente:** Panel manual con autocompletado de cuotas para simular escenarios dinámicos y consultar probabilidades exactas (Mercados 1X2 y Goles).  
> * **Gestión de Varianza (Control de Riesgo):** Barra lateral interactiva para filtrar apuestas improbables, exigiendo un porcentaje mínimo de probabilidad de éxito a la IA.  
> * **Mapeo Universal de Equipos:** Sistema integrado (mapeo\_equipos.json) que estandariza las nomenclaturas de distintas fuentes de datos y APIs en tiempo real.  
> * **API Local Continua:** Motor de Machine Learning independiente vía FastAPI, sirviendo predicciones matemáticas al instante.

## **🛠️ Stack Tecnológico**

> * **Lenguaje:** Python 3.x  
> * **Análisis y Procesamiento:** Pandas, Numpy  
> * **Machine Learning:** Scikit-Learn, XGBoost, Random Forest  
> * **Backend y API:** FastAPI, Uvicorn, Requests  
> * **Frontend y Dashboard:** Streamlit  
> * **Fuentes de Datos:** The-Odds-API (Cuotas live), Open-Meteo (Clima histórico), ClubElo (Ratings)

## **🏗️ Arquitectura y Pipeline de Datos (ETL)**

El proyecto está dividido en un flujo de trabajo modular y escalable.

### **Fase 1: Consolidación y Limpieza de Datos (union.py)**

Unificamos y depuramos los datos históricos en bruto de Primera y Segunda División. El script fusiona los datasets alineando registros, filtra las columnas oficiales de rendimiento (estadísticas y cuotas) y genera el dataset base LaLiga\_Dataset\_Final.csv.

### **Fase 2: Sistema de Ratings Elo (actualizar\_elo.py / descargar\_elo\_completo.py)**

Integramos el sistema Elo para medir la fuerza relativa y actualizada de cada club. Se consulta a la API de ClubElo de forma automatizada o mediante scraping.

### **⚠️ Nota: Si la web de ClubElo sufre restricciones de tráfico, el sistema tiene un "fallback" seguro que prioriza el uso de archivos históricos locales (EloSP1.csv, EloSP1\_Historico.csv).**

Fase 3: Enriquecimiento Climático (enriquecer\_clima.py / fusionar\_elo\_clima.py)

Para dar mayor precisión al modelo, incorporamos variables meteorológicas basadas en las coordenadas geográficas de cada estadio. Realizamos peticiones a la API de *Open-Meteo* en la fecha exacta del partido y fusionamos el resultado con los datos de Elo.

### **Fase 4: Entrenamiento de Modelos (entrenar\_modelos.py)**

Cruzamos todo el dataset maestro y preparamos las variables predictivas (Elo, diferencias, cuotas históricas, clima). Entrenamos dos modelos principales:

> * **XGBoost Classifier:** Optimizado y balanceado para el mercado **1X2**.  
> * **Random Forest Classifier:** Diseñado para predecir el mercado de **Goles (Más/Menos 2.5)**.

### **Fase 5: API REST y Despliegue (api\_predicciones.py)**

Los modelos se serializan (.pkl) y se montan sobre una API ligera con **FastAPI**. Esto expone un endpoint POST (/predecir) para calcular en milisegundos las probabilidades matemáticas de cualquier enfrentamiento.

## **⚙️ Instalación y Guía de Uso**

Sigue estos pasos para replicar el entorno y poner a funcionar el escáner de Value Bets:  
**1\. Clona el repositorio e instala las dependencias:**

git clone https://github.com/TU\_USUARIO/LaKiniela.git  
cd LaKiniela  
pip install \-r requirements.txt

**2\. Levanta el motor de Inteligencia Artificial:**  
Abre una terminal y ejecuta la API. Este proceso debe quedarse corriendo en segundo plano.

uvicorn api\_predicciones:app \--reload

**3\. Actualiza las cuotas de la jornada (Opcional):**  
Si quieres escanear partidos reales, descarga las cuotas más recientes (requiere clave de The Odds API).

python descargar\_cuotas\_live.py

**4\. Inicia la Interfaz Visual (Dashboard):**  
Abre una nueva terminal y lanza la aplicación web. Se abrirá automáticamente en tu navegador.

streamlit run app\_web.py

*(Nota: Si prefieres una herramienta orientada puramente a texto sin interfaz gráfica, puedes usar el simulador por consola ejecutando python interfaz\_usuario.py).*