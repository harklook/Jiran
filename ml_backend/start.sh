#!/bin/bash
cd "$(dirname "$0")"

echo "Starting ML server..."
uvicorn app:app --port 8001 &
SERVER_PID=$!

sleep 5

echo "Starting view watcher..."
python3 view_watcher.py &
WATCHER_PID=$!

echo ""
echo "Both running. Press Ctrl+C to stop."
echo "  ML Server  PID: $SERVER_PID"
echo "  Watcher    PID: $WATCHER_PID"
echo ""

trap "echo 'Stopping...'; kill $SERVER_PID $WATCHER_PID 2>/dev/null; exit" SIGINT SIGTERM

wait $WATCHER_PID
