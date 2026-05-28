@echo off
title YouTube2MP3 Launcher

cd /d "%~dp0"

echo ===================================================
echo   Buscando actualizaciones de yt-dlp y dependencias
echo ===================================================
py -m pip install -U -r requirements.txt

echo.
echo ===================================================
echo   Iniciando YouTube2MP3 Pro...
echo ===================================================
py main.py

pause