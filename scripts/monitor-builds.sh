#!/bin/bash

# GitHub Build Monitor and Error Solver
# Usage: ./scripts/monitor-builds.sh

set -e

echo "🔍 Checking GitHub Actions status..."

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI not found. Install with: sudo apt install gh"
    exit 1
fi

# Get latest workflow runs
echo "📊 Latest workflow runs:"
gh run list --limit 5 --json status,conclusion,name,createdAt,url

# Check for failed runs
FAILED_RUNS=$(gh run list --limit 10 --json status,conclusion,workflowName | jq -r '.[] | select(.conclusion == "failure") | .workflowName' | head -3)

if [ -n "$FAILED_RUNS" ]; then
    echo "❌ Found failed runs:"
    echo "$FAILED_RUNS"
    
    # Get latest failed run details
    LATEST_FAILED=$(gh run list --limit 1 --json status,conclusion,databaseId | jq -r '.[] | select(.conclusion == "failure") | .databaseId')
    
    if [ -n "$LATEST_FAILED" ]; then
        echo "🔍 Analyzing latest failed run..."
        
        # Download and analyze logs
        gh run download "$LATEST_FAILED" --dir /tmp/build-logs 2>/dev/null || true
        
        # Common error patterns
        echo "🔧 Checking for common issues..."
        
        # Check for deprecated actions
        if gh run view "$LATEST_FAILED" --log | grep -q "deprecated"; then
            echo "⚠️  FOUND: Deprecated GitHub Actions"
            echo "💡 Solution: Update action versions in .github/workflows/"
        fi
        
        # Check for permission issues
        if gh run view "$LATEST_FAILED" --log | grep -q "permission denied\|403"; then
            echo "⚠️  FOUND: Permission issues"
            echo "💡 Solution: Check workflow permissions in .github/workflows/"
        fi
        
        # Check for container build issues
        if gh run view "$LATEST_FAILED" --log | grep -q "failed to build\|Dockerfile"; then
            echo "⚠️  FOUND: Container build issues"
            echo "💡 Solution: Test locally with: docker build -f Containerfile -t test ."
        fi
        
        # Check for dependency issues
        if gh run view "$LATEST_FAILED" --log | grep -q "ModuleNotFoundError\|ImportError"; then
            echo "⚠️  FOUND: Python dependency issues"
            echo "💡 Solution: Check requirements.txt and Python version compatibility"
        fi
        
        # Check for timeout issues
        if gh run view "$LATEST_FAILED" --log | grep -q "timeout\|cancelled"; then
            echo "⚠️  FOUND: Timeout issues"
            echo "💡 Solution: Increase timeout or optimize build process"
        fi
        
        echo ""
        echo "📋 Quick fixes to try:"
        echo "1. Update GitHub Actions versions"
        echo "2. Check repository permissions"
        echo "3. Test container build locally"
        echo "4. Verify all dependencies are listed"
        echo "5. Check for syntax errors in YAML files"
        
        echo ""
        echo "🔗 View full logs: gh run view $LATEST_FAILED --log"
        echo "🔗 Re-run failed jobs: gh run rerun $LATEST_FAILED"
    fi
else
    echo "✅ No recent failed runs found!"
fi

# Check repository status
echo ""
echo "📈 Repository status:"
gh repo view --json name,description,pushedAt,defaultBranch

echo ""
echo "🎯 To fix common issues automatically, run:"
echo "   ./scripts/fix-common-errors.sh"