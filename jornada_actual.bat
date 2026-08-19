@echo off
echo ==========================================
echo   LANZANDO PANEL DE TRADING Y PREDICCION
echo ==========================================

:: 1. Activar el entorno virtual
call env_futbol\Scripts\activate

echo [1/2] Arrancando el motor de la IA (FastAPI)...
start /min cmd /k "uvicorn api_predicciones:app --reload"

:: Pequeña pausa de cortesía para que la API despierte
timeout /t 3 >nul

echo [2/2] Abriendo el panel web en Streamlit...
streamlit run app_web.py

pause