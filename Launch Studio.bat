@echo off
title Stonelytics Studio — Launch
cd /d "%~dp0"

echo ============================================
echo    Stonelytics Studio — Cognitive Engineering
echo ============================================
echo.

:: ─── 1. Check Python ───
echo [1/6] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Python no encontrado.
    echo.
    echo Instala Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [OK] Python %PYVER%

:: ─── 2. Check / Install srie-runtime ───
echo [2/6] Verificando SRIE Runtime...
python -c "import srie" >nul 2>&1
if %errorlevel% neq 0 (
    echo [..] Instalando srie-runtime...
    if exist ".\srie-runtime" (
        cd srie-runtime
        python -m pip install -e . >nul 2>&1
        cd ..
    ) else (
        echo [FAIL] No se encuentra srie-runtime/
        echo        Clonalo en esta carpeta: git clone https://github.com/Daviddb007/srie-runtime.git
        pause
        exit /b 1
    )
)
echo [OK] SRIE Runtime

:: ─── 3. Check / Install stonelytics-studio ───
echo [3/6] Verificando Stonelytics Studio...
python -c "import stonelytics" >nul 2>&1
if %errorlevel% neq 0 (
    echo [..] Instalando stonelytics-studio...
    if exist ".\stonelytics-studio" (
        cd stonelytics-studio
        python -m pip install -e . >nul 2>&1
        cd ..
    ) else (
        echo [FAIL] No se encuentra stonelytics-studio/
        echo        Clonalo en esta carpeta: git clone https://github.com/Daviddb007/stonelytics-studio.git
        pause
        exit /b 1
    )
)
echo [OK] Stonelytics Studio

:: ─── 4. Initialize project if needed ───
echo [4/6] Verificando proyecto...
if not exist ".\SDOS\IDENTITY.yaml" (
    echo [..] Inicializando proyecto...
    srie init . >nul 2>&1
    echo [OK] Proyecto inicializado
) else (
    echo [OK] Proyecto listo
)

:: ─── 5. Initialize Universe if needed ───
echo [5/6] Verificando Universo...
srie universe status . >nul 2>&1
if %errorlevel% neq 0 (
    echo [..] Inicializando Universo...
    srie universe init . --name "Mi Universo" >nul 2>&1
    srie universe org . "Mi Organizacion" >nul 2>&1
    echo [OK] Universo creado
) else (
    echo [OK] Universo listo
)

:: ─── 6. Launch Studio ───
echo [6/6] Arrancando Studio...
echo.
echo ============================================
echo    Abriendo http://localhost:3000
echo    Presiona Ctrl+C para detener
echo ============================================
echo.

set STUDIO_PROJECT=%CD%
start http://localhost:3000
python -m stonelytics.shell

pause
