@echo off
cd /d "C:\Users\gopal\Projects"
title Launching JARVIS...
echo Starting JARVIS AI Assistant with Neural TTS...
"C:\Python314\python.exe" "C:\Users\gopal\Projects\jarvis.py"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Jarvis closed with an error code. Press any key to exit.
    pause > nul
)
