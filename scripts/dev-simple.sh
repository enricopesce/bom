#!/bin/bash

# Simple container-based local development script using Podman
# No Kubernetes complexity - just build and run locally

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
IMAGE_NAME="vm-assessment-bom"
CONTAINER_NAME="vm-assessment-dev"
PORT="8080"

cd "$ROOT_DIR"

echo "🛠️  Building container image with Podman..."
podman build -t "$IMAGE_NAME:latest" .

echo "🧹 Stopping and removing existing container if running..."
podman stop "$CONTAINER_NAME" 2>/dev/null || true
podman rm "$CONTAINER_NAME" 2>/dev/null || true

echo "🚀 Starting container on port $PORT..."
podman run -d \
    --name "$CONTAINER_NAME" \
    -p "$PORT:8080" \
    -v "$ROOT_DIR/uploads:/app/uploads" \
    -v "$ROOT_DIR/reports:/app/reports" \
    "$IMAGE_NAME:latest"

echo "✅ Container started successfully!"
echo "📱 Access the application at: http://localhost:$PORT"
echo "📋 View logs with: podman logs $CONTAINER_NAME"
echo "🛑 Stop with: podman stop $CONTAINER_NAME"