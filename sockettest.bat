@echo off
set PYTHON=C:\Users\dexte\AppData\Local\Python\bin\python.exe
set GAME_DIR=C:\games\demoscene
cd /d %GAME_DIR%
"%PYTHON%" sockettest.py %1 %2 2>>"%GAME_DIR%\sockettest.log"
exit
