@echo off
echo Activando entorno virtual...
call env_futbol\Scripts\activate

echo Actualizando Pipeline de Datos...
python limpiar.py
python auditor_equipos.py
python enriquecer_clima.py
python fusionar_elo_clima.py
python entrenar_modelos.py

echo Proceso completado. La IA ya ha aprendido de la última jornada.
pause