#!/bin/bash
# VM Assessment BOM Generator - Container Image Build Script
# Supports Docker, Podman, and Buildah

set -euo pipefail

# Configuration
IMAGE_NAME="vm-assessment-bom"
IMAGE_TAG="${IMAGE_TAG:-latest}"
BUILD_TOOL="${BUILD_TOOL:-podman}"  # podman, docker, or buildah
PUSH_REGISTRY="${PUSH_REGISTRY:-}"
CONTEXT_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check if build tool is available
check_build_tool() {
    if ! command -v "$BUILD_TOOL" &> /dev/null; then
        log_error "$BUILD_TOOL is not installed or not in PATH"
        log_info "Install options:"
        log_info "  - Podman: https://podman.io/getting-started/installation"
        log_info "  - Buildah: https://buildah.io/getting-started/"
        log_info "  - Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    log_success "$BUILD_TOOL is available"
}

# Build with Podman
build_with_podman() {
    log_info "Building with Podman..."
    cd "$CONTEXT_DIR"
    
    podman build \
        --file Containerfile \
        --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
        --tag "${IMAGE_NAME}:latest" \
        --label "build.date=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --label "build.tool=podman" \
        --label "build.version=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        .
    
    log_success "Image built successfully with Podman"
}

# Build with Docker
build_with_docker() {
    log_info "Building with Docker..."
    cd "$CONTEXT_DIR"
    
    docker build \
        --file Containerfile \
        --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
        --tag "${IMAGE_NAME}:latest" \
        --label "build.date=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --label "build.tool=docker" \
        --label "build.version=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        .
    
    log_success "Image built successfully with Docker"
}

# Build with Buildah
build_with_buildah() {
    log_info "Building with Buildah..."
    cd "$CONTEXT_DIR"
    
    # Create a new container
    container=$(buildah from python:3.11-slim-bullseye)
    
    # Set metadata
    buildah config \
        --label "org.opencontainers.image.title=VM Assessment BOM Generator" \
        --label "org.opencontainers.image.description=Web-based tool for generating Bill of Materials from VM assessment files" \
        --label "org.opencontainers.image.version=1.0.0" \
        --label "build.date=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --label "build.tool=buildah" \
        --label "build.version=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        "$container"
    
    # Set environment variables
    buildah config --env PYTHONUNBUFFERED=1 "$container"
    buildah config --env PYTHONDONTWRITEBYTECODE=1 "$container"
    buildah config --env APP_ENV=production "$container"
    buildah config --env WORKERS=4 "$container"
    buildah config --env PORT=8000 "$container"
    
    # Create user
    buildah run "$container" -- groupadd -r appuser
    buildah run "$container" -- useradd -r -g appuser appuser
    
    # Install system dependencies
    buildah run "$container" -- apt-get update
    buildah run "$container" -- apt-get install -y gcc g++ libffi-dev
    buildah run "$container" -- rm -rf /var/lib/apt/lists/*
    buildah run "$container" -- apt-get clean
    
    # Set working directory
    buildah config --workingdir /app "$container"
    
    # Copy and install Python dependencies
    buildah copy "$container" web_app/requirements.txt ./
    buildah copy "$container" requirements-prod.txt ./
    buildah run "$container" -- pip install --no-cache-dir --upgrade pip
    buildah run "$container" -- pip install --no-cache-dir -r requirements.txt
    buildah run "$container" -- pip install --no-cache-dir -r requirements-prod.txt
    
    # Copy application
    buildah copy "$container" . .
    
    # Create directories and set permissions
    buildah run "$container" -- mkdir -p /app/web_app/static/uploads /app/logs
    buildah run "$container" -- chown -R appuser:appuser /app
    buildah run "$container" -- chmod -R 755 /app
    
    # Set user
    buildah config --user appuser "$container"
    
    # Set port
    buildah config --port 8000 "$container"
    
    # Set entrypoint
    buildah config --cmd '["python", "-m", "uvicorn", "web_app.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]' "$container"
    
    # Commit the container to an image
    buildah commit "$container" "${IMAGE_NAME}:${IMAGE_TAG}"
    buildah commit "$container" "${IMAGE_NAME}:latest"
    
    # Clean up
    buildah rm "$container"
    
    log_success "Image built successfully with Buildah"
}

# Push image to registry
push_image() {
    if [[ -n "$PUSH_REGISTRY" ]]; then
        log_info "Pushing image to registry: $PUSH_REGISTRY"
        
        # Tag for registry
        case "$BUILD_TOOL" in
            podman)
                podman tag "${IMAGE_NAME}:${IMAGE_TAG}" "${PUSH_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                podman push "${PUSH_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                ;;
            docker)
                docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${PUSH_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                docker push "${PUSH_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                ;;
            buildah)
                buildah tag "${IMAGE_NAME}:${IMAGE_TAG}" "${PUSH_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                buildah push "${PUSH_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                ;;
        esac
        
        log_success "Image pushed successfully"
    fi
}

# Show image info
show_image_info() {
    log_info "Image build completed!"
    log_info "Image name: ${IMAGE_NAME}:${IMAGE_TAG}"
    log_info "Build tool: $BUILD_TOOL"
    log_info "Context: $CONTEXT_DIR"
    
    # Show image size
    case "$BUILD_TOOL" in
        podman)
            size=$(podman images "${IMAGE_NAME}:${IMAGE_TAG}" --format "{{.Size}}" | head -1)
            ;;
        docker)
            size=$(docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "{{.Size}}" | head -1)
            ;;
        buildah)
            size=$(buildah images "${IMAGE_NAME}:${IMAGE_TAG}" --format "{{.Size}}" | head -1)
            ;;
    esac
    
    log_info "Image size: $size"
    
    log_info ""
    log_info "To run the container:"
    log_info "  $BUILD_TOOL run -p 8000:8000 ${IMAGE_NAME}:${IMAGE_TAG}"
    log_info ""
    log_info "To deploy to Kubernetes:"
    log_info "  kubectl apply -f k8s/"
}

# Main execution
main() {
    log_info "VM Assessment BOM Generator - Container Build Script"
    log_info "=================================================="
    log_info "Build tool: $BUILD_TOOL"
    log_info "Image name: ${IMAGE_NAME}:${IMAGE_TAG}"
    log_info "Context: $CONTEXT_DIR"
    log_info ""
    
    check_build_tool
    
    case "$BUILD_TOOL" in
        podman)
            build_with_podman
            ;;
        docker)
            build_with_docker
            ;;
        buildah)
            build_with_buildah
            ;;
        *)
            log_error "Unsupported build tool: $BUILD_TOOL"
            log_info "Supported tools: podman, docker, buildah"
            exit 1
            ;;
    esac
    
    push_image
    show_image_info
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "VM Assessment BOM Generator - Container Build Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Environment variables:"
        echo "  BUILD_TOOL        Build tool to use (podman, docker, buildah) [default: podman]"
        echo "  IMAGE_TAG         Image tag [default: latest]"
        echo "  PUSH_REGISTRY     Registry to push to (optional)"
        echo ""
        echo "Examples:"
        echo "  $0                                    # Build with podman"
        echo "  BUILD_TOOL=docker $0                  # Build with docker"
        echo "  BUILD_TOOL=buildah $0                 # Build with buildah"
        echo "  IMAGE_TAG=v1.0.0 $0                   # Build with custom tag"
        echo "  PUSH_REGISTRY=registry.example.com $0 # Build and push"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac