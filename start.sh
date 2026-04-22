#!/usr/bin/env bash

echo "Starting RAMA AI OS..."

# Start Ollama if not running
if command -v ollama >/dev/null 2>&1; then
    pgrep -x ollama >/dev/null || (ollama serve &)
fi

# Backend
(cd backend && uvicorn orchestrator.main:app --reload --port 3500 --host 0.0.0.0) &
BACKEND_PID=$!
echo "  Orchestrator started (PID $BACKEND_PID)"

sleep 2

# Frontend
(cd frontend && npm run dev -- --port 8080) &
FRONTEND_PID=$!
echo "  Frontend started (PID $FRONTEND_PID)"

sleep 3
echo ""
echo "  RAMA is live!"
echo "  HUD:      http://localhost:8080"
echo "  API:      http://localhost:3500"
echo "  API docs: http://localhost:3500/docs"
echo ""
echo "  Press Ctrl+C to stop all services"

# Open browser on macOS/Linux
if command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:8080
elif command -v open >/dev/null 2>&1; then
    open http://localhost:8080
fi

# Wait and cleanup
wait
