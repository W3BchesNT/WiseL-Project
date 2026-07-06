@echo off
setlocal enabledelayedexpansion
cls
echo ==========================================
echo       COMPILING WISEL PROJECT (FASM)...
echo ==========================================

cd /d "%~dp0"

set "_FASM_DIR=%~dp0Compiler\Fasm\"
set "INCLUDE=%_FASM_DIR%INCLUDE"
set "PATH=%_FASM_DIR%;%PATH%"

if exist main.exe del /f /q main.exe

:: Прямой вызов компилятора без Python-парсера
fasm out.asm main.exe
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed! Check FASM errors above.
    echo ==========================================
    pause
    exit /b
)

echo.
echo [SUCCESS] Compiled successfully!
echo ==========================================

echo Running app: main.exe
echo ------------------------------------------
main.exe

echo.
echo ==========================================
pause
exit
