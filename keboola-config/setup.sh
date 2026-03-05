#!/bin/bash
set -Eeuo pipefail

echo "=== Installing Python dependencies ==="
cd /app
uv sync

echo "=== Installing frontend dependencies ==="
cd /app/frontend
/usr/local/bin/npm install

echo "=== Building frontend ==="
/usr/local/bin/npm run build

echo "=== Setup complete ==="
