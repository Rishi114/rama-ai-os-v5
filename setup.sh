#!/usr/bin/env bash
set -e

# ── Colours ───────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${CYAN}"
echo "  ██████╗  █████╗ ███╗   ███╗ █████╗ "
echo "  ██╔══██╗██╔══██╗████╗ ████║██╔══██╗"
echo "  ██████╔╝███████║██╔████╔██║███████║"
echo "  ██╔══██╗██╔══██║██║╚██╔╝██║██╔══██║"
echo "  ██║  ██║██║  ██║██║ ╚═╝ ██║██║  ██║"
echo "  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝"
echo -e "${NC}"
echo "  AI OS v5.0 — Setup Script"
echo "  =========================="
echo ""

# ── Check tools ───────────────────────────────────────────────────────────
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}[ERROR] python3 not found${NC}"; exit 1; }
command -v node    >/dev/null 2>&1 || { echo -e "${RED}[ERROR] node not found${NC}"; exit 1; }
command -v npm     >/dev/null 2>&1 || { echo -e "${RED}[ERROR] npm not found${NC}"; exit 1; }

# ── .env ──────────────────────────────────────────────────────────────────
echo -e "${GREEN}[1/5] Setting up environment...${NC}"
[ ! -f .env ] && cp .env.example .env && echo "      Created .env — add your API keys"

# ── Python deps ───────────────────────────────────────────────────────────
echo -e "${GREEN}[2/5] Installing Python dependencies...${NC}"
cd backend
pip3 install -r requirements.txt -q
cd ..

# ── Node deps ─────────────────────────────────────────────────────────────
echo -e "${GREEN}[3/5] Installing frontend dependencies...${NC}"
cd frontend && npm install --silent && cd ..

# ── Ollama ────────────────────────────────────────────────────────────────
echo -e "${GREEN}[4/5] Checking Ollama...${NC}"
if command -v ollama >/dev/null 2>&1; then
    echo "      Pulling models (first time may take 10-20 min)..."
    ollama pull llama3     &
    ollama pull phi3       &
    ollama pull qwen2.5-coder &
    wait
    echo "      Models ready"
else
    echo -e "${YELLOW}      Ollama not found. Get it: https://ollama.com${NC}"
    echo "      RAMA will use Gemini cloud fallback"
fi

# ── Data dirs ─────────────────────────────────────────────────────────────
echo -e "${GREEN}[5/5] Initialising data...${NC}"
mkdir -p backend/data
[ ! -f backend/data/memory.json ]         && echo "[]" > backend/data/memory.json
[ ! -f backend/data/learned_skills.json ] && echo "[]" > backend/data/learned_skills.json

echo ""
echo -e "${CYAN}  ✅ Setup complete!${NC}"
echo ""
echo "  To start RAMA:"
echo "    ./start.sh"
echo ""
echo "  Or with Docker:"
echo "    docker compose up --build"
echo ""
