@echo off
title RAMA AI OS — Setup
color 0A

echo.
echo  ██████╗  █████╗ ███╗   ███╗ █████╗
echo  ██╔══██╗██╔══██╗████╗ ████║██╔══██╗
echo  ██████╔╝███████║██╔████╔██║███████║
echo  ██╔══██╗██╔══██║██║╚██╔╝██║██╔══██║
echo  ██║  ██║██║  ██║██║ ╚═╝ ██║██║  ██║
echo  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝
echo.
echo  AI OS v5.0 — One-Command Setup (Windows)
echo  ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install from https://python.org
    pause & exit /b 1
)

:: Check Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install from https://nodejs.org
    pause & exit /b 1
)

:: Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Docker not found. Install from https://docker.com for full setup.
    echo           You can still run RAMA without Docker (manual mode).
)

echo [1/5] Copying environment file...
if not exist .env (
    copy .env.example .env
    echo       Created .env — edit it to add your API keys
) else (
    echo       .env already exists, skipping
)

echo [2/5] Installing Python dependencies...
cd backend
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed
    pause & exit /b 1
)
cd ..

echo [3/5] Installing frontend dependencies...
cd frontend
npm install --silent
if %errorlevel% neq 0 (
    echo [ERROR] npm install failed
    pause & exit /b 1
)
cd ..

echo [4/5] Checking Ollama...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Ollama not found. Download from https://ollama.com
    echo           RAMA will use Gemini cloud as fallback.
) else (
    echo [4/5] Pulling Ollama models (this may take a while)...
    ollama pull llama3
    ollama pull phi3
    ollama pull qwen2.5-coder
    echo       Models ready!
)

echo [5/5] Creating data directories...
if not exist backend\data mkdir backend\data
if not exist backend\data\memory.json echo [] > backend\data\memory.json
if not exist backend\data\learned_skills.json echo [] > backend\data\learned_skills.json

echo.
echo  ✅ SETUP COMPLETE!
echo.
echo  To start RAMA, run:  start.bat
echo  Or manually:
echo    Terminal 1:  cd backend ^&^& uvicorn orchestrator.main:app --reload --port 3500
echo    Terminal 2:  cd frontend ^&^& npm run dev
echo.
pause
