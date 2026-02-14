#!/bin/bash
# Start the Prophecy FastAPI server

cd "$(dirname "$0")"

echo "Starting Prophecy Backend..."
echo ""
echo "Dev Mode Enabled:"
echo "  - Login: demo@prophecy.com (any password)"
echo "  - Token: dev-token"
echo ""
echo "API Docs: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/health"
echo ""

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
