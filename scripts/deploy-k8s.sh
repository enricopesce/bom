#!/bin/bash
# VM Assessment BOM Generator - Kubernetes Deployment Script

set -euo pipefail

# Configuration
NAMESPACE="${NAMESPACE:-vm-assessment}"
IMAGE_NAME="${IMAGE_NAME:-vm-assessment-bom}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
KUBECTL_CMD="${KUBECTL_CMD:-kubectl}"
DRY_RUN="${DRY_RUN:-false}"
CONTEXT_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v "$KUBECTL_CMD" &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! $KUBECTL_CMD cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        log_info "Please ensure your kubeconfig is properly configured"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create namespace if it doesn't exist
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    
    if $KUBECTL_CMD get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
    else
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would create namespace: $NAMESPACE"
        else
            $KUBECTL_CMD apply -f "$CONTEXT_DIR/k8s/namespace.yaml"
            log_success "Namespace created successfully"
        fi
    fi
}

# Deploy application
deploy_application() {
    log_info "Deploying VM Assessment BOM Generator..."
    
    cd "$CONTEXT_DIR"
    
    # Apply configurations in order
    local resources=(
        "k8s/namespace.yaml"
        "k8s/configmap.yaml"
        "k8s/deployment.yaml"
        "k8s/service.yaml"
        "k8s/hpa.yaml"
        "k8s/pdb.yaml"
    )
    
    for resource in "${resources[@]}"; do
        if [[ -f "$resource" ]]; then
            log_info "Applying $resource..."
            if [[ "$DRY_RUN" == "true" ]]; then
                log_info "[DRY RUN] Would apply: $resource"
                $KUBECTL_CMD apply -f "$resource" --dry-run=client
            else
                $KUBECTL_CMD apply -f "$resource"
            fi
        else
            log_warning "Resource file not found: $resource"
        fi
    done
    
    if [[ "$DRY_RUN" != "true" ]]; then
        log_success "Application deployed successfully"
    else
        log_info "[DRY RUN] Deployment simulation completed"
    fi
}

# Deploy ingress (optional)
deploy_ingress() {
    if [[ "${DEPLOY_INGRESS:-false}" == "true" ]]; then
        log_info "Deploying ingress..."
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would apply: k8s/ingress.yaml"
            $KUBECTL_CMD apply -f "$CONTEXT_DIR/k8s/ingress.yaml" --dry-run=client
        else
            $KUBECTL_CMD apply -f "$CONTEXT_DIR/k8s/ingress.yaml"
            log_success "Ingress deployed successfully"
        fi
    else
        log_info "Skipping ingress deployment (set DEPLOY_INGRESS=true to enable)"
    fi
}

# Wait for deployment to be ready
wait_for_deployment() {
    if [[ "$DRY_RUN" != "true" ]]; then
        log_info "Waiting for deployment to be ready..."
        $KUBECTL_CMD wait --for=condition=available --timeout=300s deployment/vm-assessment-bom -n "$NAMESPACE"
        log_success "Deployment is ready"
    fi
}

# Show deployment status
show_status() {
    log_info "Deployment Status:"
    echo ""
    
    if [[ "$DRY_RUN" != "true" ]]; then
        # Pods
        log_info "Pods:"
        $KUBECTL_CMD get pods -n "$NAMESPACE" -l app.kubernetes.io/name=vm-assessment-bom
        echo ""
        
        # Services
        log_info "Services:"
        $KUBECTL_CMD get services -n "$NAMESPACE"
        echo ""
        
        # Ingress (if exists)
        if $KUBECTL_CMD get ingress -n "$NAMESPACE" &> /dev/null; then
            log_info "Ingress:"
            $KUBECTL_CMD get ingress -n "$NAMESPACE"
            echo ""
        fi
        
        # HPA
        log_info "Horizontal Pod Autoscaler:"
        $KUBECTL_CMD get hpa -n "$NAMESPACE"
        echo ""
        
        # Get service endpoint
        local service_type
        service_type=$($KUBECTL_CMD get service vm-assessment-bom-service -n "$NAMESPACE" -o jsonpath='{.spec.type}')
        
        case "$service_type" in
            LoadBalancer)
                local external_ip
                external_ip=$($KUBECTL_CMD get service vm-assessment-bom-service -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
                if [[ -n "$external_ip" ]]; then
                    log_success "Application accessible at: http://$external_ip"
                else
                    log_info "LoadBalancer IP is pending..."
                fi
                ;;
            ClusterIP)
                log_info "Application accessible via port-forward:"
                log_info "  $KUBECTL_CMD port-forward -n $NAMESPACE service/vm-assessment-bom-service 8000:80"
                ;;
        esac
    else
        log_info "[DRY RUN] Status check skipped"
    fi
}

# Update image in deployment
update_image() {
    local new_image="$1"
    log_info "Updating deployment image to: $new_image"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would update image to: $new_image"
    else
        $KUBECTL_CMD set image deployment/vm-assessment-bom vm-assessment-bom="$new_image" -n "$NAMESPACE"
        $KUBECTL_CMD rollout status deployment/vm-assessment-bom -n "$NAMESPACE"
        log_success "Image updated successfully"
    fi
}

# Rollback deployment
rollback_deployment() {
    log_info "Rolling back deployment..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would rollback deployment"
    else
        $KUBECTL_CMD rollout undo deployment/vm-assessment-bom -n "$NAMESPACE"
        $KUBECTL_CMD rollout status deployment/vm-assessment-bom -n "$NAMESPACE"
        log_success "Rollback completed successfully"
    fi
}

# Delete deployment
delete_deployment() {
    log_warning "This will delete the entire VM Assessment BOM deployment!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deleting deployment..."
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would delete all resources in namespace: $NAMESPACE"
        else
            $KUBECTL_CMD delete namespace "$NAMESPACE"
            log_success "Deployment deleted successfully"
        fi
    else
        log_info "Deletion cancelled"
    fi
}

# Show help
show_help() {
    cat << EOF
VM Assessment BOM Generator - Kubernetes Deployment Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  deploy      Deploy the application (default)
  update      Update the application image
  rollback    Rollback to previous version
  status      Show deployment status
  delete      Delete the deployment
  help        Show this help

Environment Variables:
  NAMESPACE         Kubernetes namespace [default: vm-assessment]
  IMAGE_NAME        Container image name [default: vm-assessment-bom]
  IMAGE_TAG         Container image tag [default: latest]
  KUBECTL_CMD       kubectl command [default: kubectl]
  DRY_RUN          Run in dry-run mode [default: false]
  DEPLOY_INGRESS   Deploy ingress resources [default: false]

Examples:
  $0                                    # Deploy application
  $0 status                            # Show status
  DRY_RUN=true $0                      # Dry run deployment
  IMAGE_TAG=v1.0.0 $0 update           # Update to specific version
  DEPLOY_INGRESS=true $0               # Deploy with ingress
  $0 delete                            # Delete deployment

EOF
}

# Main execution
main() {
    local command="${1:-deploy}"
    
    case "$command" in
        deploy)
            log_info "VM Assessment BOM Generator - Kubernetes Deployment"
            log_info "======================================================"
            log_info "Namespace: $NAMESPACE"
            log_info "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
            log_info "Dry run: $DRY_RUN"
            log_info ""
            
            check_prerequisites
            create_namespace
            deploy_application
            deploy_ingress
            wait_for_deployment
            show_status
            ;;
        update)
            check_prerequisites
            local new_image="${IMAGE_NAME}:${IMAGE_TAG}"
            update_image "$new_image"
            show_status
            ;;
        rollback)
            check_prerequisites
            rollback_deployment
            show_status
            ;;
        status)
            check_prerequisites
            show_status
            ;;
        delete)
            check_prerequisites
            delete_deployment
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"