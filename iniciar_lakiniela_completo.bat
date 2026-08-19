@echo off
echo ============================================================
echo   LAKINIELA: TODO-EN-UNO (ACTUALIZAR Y LANZAR PANEL)
echo ============================================================

:: 1. Activar entorno virtual
call env_futbol\Scripts\activate
set PYTHONIOENCODING=utf-8

:: 2. Actualizacion maestra de todos los CSVs, ELOs, Modelos y Cuotas
echo [1/3] Sincronizando datos, modelos y cuotas en vivo de Bet365...
python actualizar_sistema_completo.py

:: 3. Arrancar API FastAPI en segundo plano
echo [2/3] Levantando el motor predictivo FastAPI...
start /min cmd /k "uvicorn api_predicciones:app --reload"
timeout /t 3 >nul

:: 4. Abrir la interfaz web de Streamlit
echo [3/3] Abriendo el panel de control en tu navegador...
streamlit run app_web.py

pause
