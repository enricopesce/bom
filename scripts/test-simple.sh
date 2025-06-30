#!/bin/bash

# Simple container testing script using Podman
# Tests the locally running container

set -e

CONTAINER_NAME="vm-assessment-dev"
BASE_URL="http://localhost:8080"

echo "🧪 Testing container-based application..."

# Check if container is running
if ! podman ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container $CONTAINER_NAME is not running"
    echo "💡 Start it with: ./scripts/dev-simple.sh"
    exit 1
fi

echo "✅ Container is running"

# Wait for application to be ready
echo "⏳ Waiting for application to be ready..."
for i in {1..30}; do
    if curl -s -f "$BASE_URL/" > /dev/null 2>&1; then
        echo "✅ Health check passed"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Application failed to start within 30 seconds"
        echo "📋 Container logs:"
        podman logs "$CONTAINER_NAME"
        exit 1
    fi
    sleep 1
done

# Test main page
echo "🌐 Testing main page..."
if curl -s "$BASE_URL/" | grep -q "VM Assessment BOM Generator"; then
    echo "✅ Main page loads correctly"
else
    echo "❌ Main page content incorrect"
    exit 1
fi

# Test additional endpoints
echo "🔌 Testing additional endpoints..."
if curl -s -f "$BASE_URL/admin/sessions" > /dev/null; then
    echo "✅ Admin endpoint working"
else
    echo "❌ Admin endpoint failed"
    exit 1
fi

echo "🎉 All basic tests passed!"
echo "📋 View logs: podman logs $CONTAINER_NAME"
echo "🛑 Stop container: podman stop $CONTAINER_NAME"