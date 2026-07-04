@echo off
setlocal enabledelayedexpansion
cls
echo ==========================================
echo       COMPILING WISEL PROJECT...
echo ==========================================

cd /d "%~dp0"
set "INCLUDE="
for %%n in (fasm.exe fasmw.exe) do (
    where %%n >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=* usebackq" %%i in (`where %%n`) do set "_FASM_DIR=%%~dpi"& goto :set_include
    )
)
for /d %%d in ("C:\Program Files\fasm*") do (
    if exist "%%d\fasm.exe" ( set "_FASM_DIR=%%d\"& goto :set_include )
    if exist "%%d\FASM.EXE" ( set "_FASM_DIR=%%d\"& goto :set_include )
)
if exist "%USERPROFILE%\Desktop\FASM\fasm.exe" (
    set "_FASM_DIR=%USERPROFILE%\Desktop\FASM\"
    goto :set_include
)
set "_FASM_DIR=C:\fasm\"
:set_include
set "INCLUDE=%_FASM_DIR%INCLUDE"
if exist main.exe del /f /q main.exe

python Compiler\oniLink.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed! Check Python or FASM errors above.
    echo ==========================================
    pause
    exit /b
)
ie4uinit.exe -show
echo.
echo [SUCCESS] Parsed and compiled successfully!
echo ==========================================
mklink /H main.exe Compiler\main.exe >nul

echo Running app: main.exe
echo ------------------------------------------
main.exe

echo.
echo ==========================================
pause
exit