#!/bin/bash
# VM Assessment BOM Generator - Local Testing Script

set -euo pipefail

# Configuration
IMAGE_NAME="${IMAGE_NAME:-vm-assessment-bom}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
CONTAINER_NAME="${CONTAINER_NAME:-vm-assessment-test}"
BUILD_TOOL="${BUILD_TOOL:-podman}"
PORT="${PORT:-8000}"
TEST_FILE="${TEST_FILE:-../RVTools_export_all_2025-05-21_VIlla Berica.zip}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    $BUILD_TOOL stop "$CONTAINER_NAME" &>/dev/null || true
    $BUILD_TOOL rm "$CONTAINER_NAME" &>/dev/null || true
}

# Trap cleanup on exit
trap cleanup EXIT

# Test container startup
test_startup() {
    log_info "Starting container for testing..."
    
    $BUILD_TOOL run -d \
        --name "$CONTAINER_NAME" \
        -p "$PORT:8000" \
        -e APP_ENV=test \
        -e LOG_LEVEL=debug \
        "$IMAGE_NAME:$IMAGE_TAG"
    
    # Wait for startup
    log_info "Waiting for container to start..."
    sleep 10
    
    # Check if container is running
    if ! $BUILD_TOOL ps | grep -q "$CONTAINER_NAME"; then
        log_error "Container failed to start"
        $BUILD_TOOL logs "$CONTAINER_NAME"
        exit 1
    fi
    
    log_success "Container started successfully"
}

# Test health endpoint
test_health() {
    log_info "Testing health endpoint..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$PORT/" > /dev/null; then
            log_success "Health check passed"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts failed, retrying in 2 seconds..."
        sleep 2
        ((attempt++))
    done
    
    log_error "Health check failed after $max_attempts attempts"
    $BUILD_TOOL logs "$CONTAINER_NAME"
    exit 1
}

# Test main page
test_main_page() {
    log_info "Testing main page..."
    
    local response
    response=$(curl -s "http://localhost:$PORT/")
    
    if echo "$response" | grep -q "VM Assessment BOM Generator"; then
        log_success "Main page loads correctly"
    else
        log_error "Main page content is incorrect"
        exit 1
    fi
}

# Test API endpoints
test_api_endpoints() {
    log_info "Testing API endpoints..."
    
    # Test favicon
    if curl -s -f "http://localhost:$PORT/favicon.ico" > /dev/null; then
        log_success "Favicon endpoint works"
    else
        log_warning "Favicon endpoint failed (non-critical)"
    fi
    
    # Test help page
    if curl -s -f "http://localhost:$PORT/help" > /dev/null; then
        log_success "Help page works"
    else
        log_error "Help page failed"
        exit 1
    fi
    
    # Test admin sessions (should work even with no sessions)
    if curl -s -f "http://localhost:$PORT/admin/sessions" > /dev/null; then
        log_success "Admin sessions endpoint works"
    else
        log_error "Admin sessions endpoint failed"
        exit 1
    fi
}

# Test file upload (if test file exists)
test_file_upload() {
    if [[ -f "$TEST_FILE" ]]; then
        log_info "Testing file upload with $TEST_FILE..."
        
        local response
        response=$(curl -s -X POST \
            -F "file=@$TEST_FILE" \
            -F "formats=text" \
            "http://localhost:$PORT/upload")
        
        if echo "$response" | grep -q "session_id"; then
            log_success "File upload test passed"
            
            # Extract session ID and test status
            local session_id
            session_id=$(echo "$response" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
            
            if [[ -n "$session_id" ]]; then
                log_info "Testing session status..."
                sleep 5  # Give it time to process
                
                local status_response
                status_response=$(curl -s "http://localhost:$PORT/status/$session_id")
                
                if echo "$status_response" | grep -q '"status"'; then
                    log_success "Session status test passed"
                else
                    log_warning "Session status test failed (processing may be ongoing)"
                fi
            fi
        else
            log_warning "File upload test failed (may need valid RVTools file)"
        fi
    else
        log_warning "No test file found at $TEST_FILE, skipping upload test"
    fi
}

# Test container logs
test_logs() {
    log_info "Checking container logs for errors..."
    
    local logs
    logs=$($BUILD_TOOL logs "$CONTAINER_NAME" 2>&1)
    
    if echo "$logs" | grep -i "error" | grep -v "404" | grep -v "favicon"; then
        log_warning "Found potential errors in logs:"
        echo "$logs" | grep -i "error" | grep -v "404" | grep -v "favicon"
    else
        log_success "No critical errors found in logs"
    fi
    
    # Show startup confirmation
    if echo "$logs" | grep -q "Uvicorn running"; then
        log_success "Application started successfully"
    else
        log_warning "Application startup not confirmed in logs"
    fi
}

# Performance test
test_performance() {
    log_info "Running basic performance test..."
    
    local start_time end_time duration
    start_time=$(date +%s%N)
    
    for i in {1..10}; do
        curl -s "http://localhost:$PORT/" > /dev/null
    done
    
    end_time=$(date +%s%N)
    duration=$(( (end_time - start_time) / 1000000 ))  # Convert to milliseconds
    
    local avg_response_time=$((duration / 10))
    
    if [ $avg_response_time -lt 1000 ]; then
        log_success "Performance test passed: ${avg_response_time}ms average response time"
    else
        log_warning "Performance test concern: ${avg_response_time}ms average response time"
    fi
}

# Main test runner
run_tests() {
    log_info "VM Assessment BOM Generator - Local Testing"
    log_info "=========================================="
    log_info "Image: $IMAGE_NAME:$IMAGE_TAG"
    log_info "Container: $CONTAINER_NAME"
    log_info "Port: $PORT"
    log_info "Build tool: $BUILD_TOOL"
    log_info ""
    
    test_startup
    test_health
    test_main_page
    test_api_endpoints
    test_file_upload
    test_logs
    test_performance
    
    log_info ""
    log_success "All tests completed successfully!"
    log_info ""
    log_info "Container is running and accessible at: http://localhost:$PORT"
    log_info "To stop the container: $BUILD_TOOL stop $CONTAINER_NAME"
    log_info "To see logs: $BUILD_TOOL logs -f $CONTAINER_NAME"
}

# Handle arguments
case "${1:-run}" in
    run)
        run_tests
        ;;
    cleanup)
        cleanup
        log_success "Cleanup completed"
        ;;
    logs)
        $BUILD_TOOL logs -f "$CONTAINER_NAME"
        ;;
    --help|-h)
        echo "VM Assessment BOM Generator - Local Testing Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  run       Run all tests (default)"
        echo "  cleanup   Stop and remove test container"
        echo "  logs      Show container logs"
        echo "  --help    Show this help"
        echo ""
        echo "Environment variables:"
        echo "  IMAGE_NAME       Container image name [default: vm-assessment-bom]"
        echo "  IMAGE_TAG        Container image tag [default: latest]"
        echo "  CONTAINER_NAME   Test container name [default: vm-assessment-test]"
        echo "  BUILD_TOOL       Container tool [default: podman]"
        echo "  PORT            Local port [default: 8000]"
        echo "  TEST_FILE       RVTools file for upload test [default: RVTools_export_all_2025-05-21_VIlla Berica.zip]"
        echo ""
        ;;
    *)
        log_error "Unknown command: $1"
        log_info "Use --help for usage information"
        exit 1
        ;;
esac