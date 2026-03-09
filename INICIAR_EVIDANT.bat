@echo off
chcp 65001 > nul
title Evidant Suite
cd /d "%~dp0"

REM Obtener IP local
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "127.0.0.1"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP: =%

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║           EVIDANT SUITE                      ║
echo  ╠══════════════════════════════════════════════╣
echo  ║  Local:   http://localhost:8501              ║
echo  ║  Red LAN: http://%IP%:8501
echo  ╚══════════════════════════════════════════════╝
echo.

REM Iniciar Streamlit en segundo plano
echo  [1/2] Iniciando Streamlit...
start "Streamlit" "%~dp0.venv\Scripts\python.exe" -m streamlit run "%~dp0Inicio.py" ^
    --server.address 0.0.0.0 ^
    --server.port 8501 ^
    --server.headless true

REM Esperar que Streamlit levante
timeout /t 4 /nobreak > nul

REM Tunnel Cloudflare (si existe cloudflared.exe en la carpeta)
if exist "%~dp0cloudflared.exe" (
    echo  [2/2] Creando tunel Internet con Cloudflare...
    echo.
    echo  Busca abajo la linea:  https://xxxx.trycloudflare.com
    echo  Ese link funciona desde CUALQUIER red del mundo.
    echo  ────────────────────────────────────────────────
    "%~dp0cloudflared.exe" tunnel --url http://localhost:8501
) else (
    echo  [2/2] Tunel Internet NO disponible.
    echo        Para activarlo descarga cloudflared.exe desde:
    echo        https://github.com/cloudflare/cloudflared/releases/latest
    echo        y colocalo en esta carpeta.
    echo.
    echo  Presiona cualquier tecla para abrir el navegador local...
    pause > nul
    start http://localhost:8501
)

pause
