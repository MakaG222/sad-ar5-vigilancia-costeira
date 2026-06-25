@echo off
REM Arranque da plataforma SAD AR5 no Windows (duplo-clique).
cd /d "%~dp0"
title SAD AR5 - Plataforma
echo.
echo  SAD AR5 - Vigilancia Costeira
echo  A iniciar API + interface web...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-win.ps1"
echo.
pause
