#!/bin/bash
set -Eeuo pipefail

echo "==> Installing frontend dependencies and building..."
cd /app/frontend
npm install
npm run build

echo "==> Installing Python dependencies..."
cd /app
uv sync

echo "==> Setup complete."
