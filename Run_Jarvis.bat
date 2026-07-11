@echo off
cd /d "C:\Users\gopal\Projects"
title Launching JARVIS v3.1...
echo Starting JARVIS AI Assistant with Modular Clean Architecture...
"C:\Python314\python.exe" "C:\Users\gopal\Projects\main.py"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Jarvis closed with an error code. Press any key to exit.
    pause > nul
)
