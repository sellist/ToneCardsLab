#!/bin/bash

if [ ! -d "tcl-api" ] || [ ! -d "tcl-web" ]; then
    echo "please run this script from the ToneCardsLab root directory"
    exit 1
fi

cleanup() {
    echo "Shutting down"
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

echo "Starting API server"
cd tcl-api
uv run uvicorn tcl_api.main:app --reload --port 8000 &
API_PID=$!
cd ..

sleep 2

echo "Starting web server"
cd tcl-web
npm run dev &
WEB_PID=$!
cd ..


echo "Access points:"
echo "   API:  http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   Web:  http://localhost:5173"
echo "Press Ctrl+C to stop all servers"
echo ""

wait

