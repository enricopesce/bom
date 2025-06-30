#!/bin/bash

# Local Development Environment
# Run the VM Assessment BOM Tool locally for development

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

success() { echo -e "${GREEN}✅ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }
info() { echo -e "${BLUE}ℹ️ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }

echo "🚀 VM Assessment BOM Tool - Local Development"
echo "============================================="

# Check if running in project directory
if [ ! -f "web_app/app.py" ]; then
    error "Please run this script from the project root directory"
    exit 1
fi

# Function to check and install dependencies
check_dependencies() {
    info "Checking Python dependencies..."
    
    if ! python3 -c "import fastapi, pandas, openpyxl" 2>/dev/null; then
        warning "Installing missing dependencies..."
        pip install -r requirements.txt || {
            error "Failed to install dependencies"
            exit 1
        }
    fi
    success "Dependencies are ready"
}

# Function to setup development environment
setup_dev_env() {
    info "Setting up development environment..."
    
    # Create uploads directory if it doesn't exist
    mkdir -p web_app/static/uploads
    
    # Set development environment variables
    export APP_ENV="development"
    export WORKERS="1"
    export PORT="8000"
    export LOG_LEVEL="DEBUG"
    
    success "Development environment configured"
}

# Function to start the application
start_app() {
    info "Starting VM Assessment BOM Tool..."
    
    cd web_app
    
    echo ""
    success "🌟 Application starting at: http://localhost:8000"
    success "📁 Upload interface: http://localhost:8000/"
    success "📊 Results will be available after processing"
    echo ""
    info "Press Ctrl+C to stop the application"
    echo ""
    
    # Start with uvicorn for development (hot reload)
    python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload --reload-dir .
}

# Function to run pre-checks
run_prechecks() {
    info "Running pre-deployment checks..."
    
    # Syntax check
    python3 -m py_compile web_app/app.py || {
        error "Python syntax error in app.py"
        exit 1
    }
    
    # Configuration check
    python3 -c "import json; json.load(open('web_app/pricing.json'))" || {
        error "Invalid pricing.json configuration"
        exit 1
    }
    
    success "Pre-checks completed"
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  start       Start the development server (default)"
    echo "  check       Run pre-deployment checks only"
    echo "  install     Install/update dependencies"
    echo "  clean       Clean temporary files"
    echo "  help        Show this help message"
    echo ""
    echo "Development URLs:"
    echo "  Application: http://localhost:8000"
    echo "  API Docs:    http://localhost:8000/docs"
    echo ""
    echo "Development Features:"
    echo "  • Hot reload enabled"
    echo "  • Debug logging"
    echo "  • Development CORS settings"
    echo "  • Detailed error messages"
}

# Function to clean temporary files
clean_temp() {
    info "Cleaning temporary files..."
    
    # Remove uploaded files
    rm -rf web_app/static/uploads/*
    
    # Remove Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    success "Temporary files cleaned"
}

# Function to install dependencies
install_deps() {
    info "Installing/updating dependencies..."
    
    python3 -m pip install --upgrade pip
    pip install -r requirements.txt
    
    success "Dependencies installed"
}

# Main execution
case "${1:-start}" in
    "start")
        run_prechecks
        check_dependencies
        setup_dev_env
        start_app
        ;;
    "check")
        run_prechecks
        success "All checks passed - ready for development"
        ;;
    "install")
        install_deps
        ;;
    "clean")
        clean_temp
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac