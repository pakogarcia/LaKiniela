@echo off
echo ============================================================
echo   ACTUALIZACION MAESTRA AUTOMATICA - LA KINIELA
echo ============================================================

:: 1. Activar el entorno virtual
call env_futbol\Scripts\activate

:: 2. Configurar codificacion UTF-8 para consola de Windows
set PYTHONIOENCODING=utf-8

:: 3. Ejecutar pipeline completo de ETL, Clima, ELO, Modelos y Cuotas
python actualizar_sistema_completo.py

echo.
echo ============================================================
echo   PROCESO COMPLETADO. TODOS LOS CSV Y MODELOS ESTAN LISTOS.
echo ============================================================
pause