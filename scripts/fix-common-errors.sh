#!/bin/bash

# Automated GitHub Actions Error Fixer
# Usage: ./scripts/fix-common-errors.sh

set -e

echo "🔧 GitHub Actions Error Auto-Fixer"
echo "=================================="

CHANGES_MADE=false

# Function to update file if pattern exists
update_if_exists() {
    local file="$1"
    local pattern="$2"
    local replacement="$3"
    local description="$4"
    
    if [ -f "$file" ] && grep -q "$pattern" "$file"; then
        echo "🔄 $description"
        sed -i "s|$pattern|$replacement|g" "$file"
        CHANGES_MADE=true
        return 0
    fi
    return 1
}

# Fix deprecated GitHub Actions
echo "1. Fixing deprecated GitHub Actions..."

# Update common deprecated actions
for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
    if [ -f "$workflow" ]; then
        update_if_exists "$workflow" "actions/checkout@v3" "actions/checkout@v4" "  ✅ Updated checkout action in $(basename $workflow)"
        update_if_exists "$workflow" "actions/setup-python@v4" "actions/setup-python@v5" "  ✅ Updated setup-python action in $(basename $workflow)"
        update_if_exists "$workflow" "actions/cache@v3" "actions/cache@v4" "  ✅ Updated cache action in $(basename $workflow)"
        update_if_exists "$workflow" "actions/upload-artifact@v3" "actions/upload-artifact@v4" "  ✅ Updated upload-artifact action in $(basename $workflow)"
        update_if_exists "$workflow" "actions/download-artifact@v3" "actions/download-artifact@v4" "  ✅ Updated download-artifact action in $(basename $workflow)"
        update_if_exists "$workflow" "docker/setup-buildx-action@v2" "docker/setup-buildx-action@v3" "  ✅ Updated docker-buildx action in $(basename $workflow)"
        update_if_exists "$workflow" "docker/build-push-action@v4" "docker/build-push-action@v5" "  ✅ Updated docker-build-push action in $(basename $workflow)"
        update_if_exists "$workflow" "docker/login-action@v2" "docker/login-action@v3" "  ✅ Updated docker-login action in $(basename $workflow)"
    fi
done

# Fix permission issues
echo ""
echo "2. Checking workflow permissions..."
for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
    if [ -f "$workflow" ] && grep -q "packages: write" "$workflow"; then
        if ! grep -q "contents: read" "$workflow"; then
            echo "  ⚠️  Adding missing contents permission to $(basename $workflow)"
            # This is complex to do with sed, better to note it
            echo "  📝 Manual fix needed: Add 'contents: read' permission"
        fi
    fi
done

# Check for common YAML syntax issues
echo ""
echo "3. Validating YAML syntax..."
for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
    if [ -f "$workflow" ]; then
        if ! python3 -c "import yaml; yaml.safe_load(open('$workflow'))" 2>/dev/null; then
            echo "  ❌ YAML syntax error in $(basename $workflow)"
            echo "  💡 Run: python3 -c \"import yaml; yaml.safe_load(open('$workflow'))\""
        else
            echo "  ✅ YAML syntax valid in $(basename $workflow)"
        fi
    fi
done

# Check container build files
echo ""
echo "4. Validating container configuration..."
if [ -f "Containerfile" ] || [ -f "Dockerfile" ]; then
    CONTAINER_FILE="Containerfile"
    [ -f "Dockerfile" ] && CONTAINER_FILE="Dockerfile"
    
    echo "  📦 Found: $CONTAINER_FILE"
    
    # Check for common issues
    if ! grep -q "USER" "$CONTAINER_FILE"; then
        echo "  ⚠️  No USER directive found (security best practice)"
    fi
    
    if ! grep -q "HEALTHCHECK" "$CONTAINER_FILE"; then
        echo "  ℹ️  No HEALTHCHECK found (optional but recommended)"
    fi
else
    echo "  ❌ No Containerfile or Dockerfile found"
fi

# Check Python requirements
echo ""
echo "5. Validating Python dependencies..."
if [ -f "requirements.txt" ]; then
    echo "  📋 Checking requirements.txt..."
    
    # Check for version conflicts
    if grep -q "==" requirements.txt && grep -q ">=" requirements.txt; then
        echo "  ⚠️  Mixed version specifications found"
        echo "  💡 Consider using consistent version pinning"
    fi
    
    echo "  ✅ requirements.txt found"
else
    echo "  ❌ No requirements.txt found"
fi

# Test local build if possible
echo ""
echo "6. Testing local container build..."
if command -v docker &> /dev/null; then
    if [ -f "Containerfile" ]; then
        echo "  🏗️  Testing container build..."
        if docker build -f Containerfile -t test-build . &>/dev/null; then
            echo "  ✅ Container builds successfully"
            docker rmi test-build &>/dev/null || true
        else
            echo "  ❌ Container build failed"
            echo "  💡 Run: docker build -f Containerfile -t test-build ."
        fi
    fi
else
    echo "  ⚠️  Docker not available for local testing"
fi

# Summary and next steps
echo ""
echo "📊 Summary:"
if [ "$CHANGES_MADE" = true ]; then
    echo "✅ Automated fixes applied!"
    echo ""
    echo "🚀 Next steps:"
    echo "1. Review changes: git diff"
    echo "2. Commit fixes: git add . && git commit -m 'Fix: Update deprecated GitHub Actions'"
    echo "3. Push changes: git push"
    echo "4. Monitor build: gh run watch"
else
    echo "ℹ️  No automated fixes needed or applied"
fi

echo ""
echo "🔍 For manual debugging:"
echo "- View logs: gh run view --log"
echo "- Re-run failed: gh run rerun <run-id>"
echo "- Monitor status: ./scripts/monitor-builds.sh"