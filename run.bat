@echo off
set GAME_DIR=C:\demoscene
set PYTHON=C:\Users\dexte\AppData\Local\Python\bin\python.exe
set NODE=%1
set HANDLE=%2

cd /d %GAME_DIR%

echo run.bat called with: %1 %2 > "%TEMP%\demoscene_run.log"

REM Copy drop file
if exist "C:\mystic\temp%NODE%\DOOR.SYS" (
    copy /y "C:\mystic\temp%NODE%\DOOR.SYS" "%GAME_DIR%\DOOR.SYS" >nul
    echo DOOR.SYS copied >> "%TEMP%\demoscene_run.log"
)

REM Launch game
"%PYTHON%" game.py %NODE% %HANDLE% >> "%TEMP%\demoscene_run.log" 2>&1

echo Game exited with code: %ERRORLEVEL% >> "%TEMP%\demoscene_run.log"

REM Clean up drop file
if exist "%GAME_DIR%\DOOR.SYS" del "%GAME_DIR%\DOOR.SYS" >nul