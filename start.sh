#!/bin/bash
# Railway startup script with debugging

set -e  # Exit on error

echo "=== Railway Startup Debug ==="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "PORT: ${PORT:-'NOT SET'}"
echo "ENVIRONMENT: ${ENVIRONMENT:-'NOT SET'}"
echo ""

echo "=== Checking Python packages ==="
/opt/venv/bin/python -c "import uvicorn; print(f'uvicorn: {uvicorn.__version__}')" || echo "ERROR: uvicorn not found"
/opt/venv/bin/python -c "import fastapi; print(f'fastapi: {fastapi.__version__}')" || echo "ERROR: fastapi not found"
/opt/venv/bin/python -c "import anthropic; print(f'anthropic installed')" || echo "ERROR: anthropic not found"
echo ""

echo "=== Checking environment variables ==="
/opt/venv/bin/python -c "
import os
required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'ANTHROPIC_API_KEY', 'JWT_SECRET']
for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f'{var}: SET (length={len(value)})')
    else:
        print(f'{var}: MISSING!')
" || echo "ERROR checking env vars"
echo ""

echo "=== Testing app import ==="
/opt/venv/bin/python -c "from app.main import app; print('✓ App imported successfully')" || {
    echo "ERROR: Failed to import app!"
    /opt/venv/bin/python -c "from app.main import app" 2>&1 || true
    exit 1
}
echo ""

echo "=== Starting uvicorn ==="
exec /opt/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
