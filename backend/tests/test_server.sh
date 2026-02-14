#!/bin/bash
source venv/bin/activate
python -m app.main &
SERVER_PID=$!
sleep 3
curl -s http://localhost:8000/health
kill $SERVER_PID
echo ""
echo "✅ Server test complete"
