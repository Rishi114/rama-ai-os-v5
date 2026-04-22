@echo off
title RAMA AI OS — Starting...
color 0A

echo  Starting RAMA AI OS v5.0...
echo.

:: Start backend
echo [1/2] Starting orchestrator (port 3500)...
start "RAMA Backend" cmd /k "cd backend && uvicorn orchestrator.main:app --reload --port 3500 --host 0.0.0.0"

:: Wait a moment
timeout /t 3 /nobreak >nul

:: Start frontend
echo [2/2] Starting frontend HUD (port 8080)...
start "RAMA Frontend" cmd /k "cd frontend && npm run dev -- --port 8080"

:: Wait then open browser
timeout /t 4 /nobreak >nul
start http://localhost:8080

echo.
echo  RAMA is running!
echo  Frontend:     http://localhost:8080
echo  API:          http://localhost:3500
echo  API Docs:     http://localhost:3500/docs
echo.
