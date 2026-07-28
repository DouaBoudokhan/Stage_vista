#!/bin/bash

echo "Starting StockIT Backend Server..."
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start server
uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
