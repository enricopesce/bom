# VM Assessment BOM Generator - Deployment Guide

## 🐳 **Container & Kubernetes Deployment**

Questa guida ti aiuterà a buildare e deployare il VM Assessment BOM Generator su Kubernetes usando tool open source compatibili con Docker.

## 🛠️ **Tool Supportati**

### **Container Build Tools**
- **Podman** ⭐ (Raccomandato - Open Source, rootless, Docker-compatible)
- **Buildah** (Build-only tool, molto potente e flessibile)  
- **Docker** (Compatibile ma proprietario)

### **Kubernetes Tools**
- **kubectl** - Client Kubernetes standard
- **k3s/k8s** - Kubernetes distributions
- **OpenShift** - Supportato tramite kubectl

## 🚀 **Quick Start**

### **1. Build dell'Immagine**

```bash
# Con Podman (raccomandato)
make build

# Con Docker
make build-docker

# Con Buildah
make build-buildah

# Build con tag personalizzato
IMAGE_TAG=v1.0.0 make build
```

### **2. Test Locale**

```bash
# Run in foreground
make run

# Run in background
make run-detached

# Check logs
podman logs vm-assessment-bom

# Stop container
make stop
```

### **3. Deploy su Kubernetes**

```bash
# Deploy completo
make deploy

# Deploy con Ingress
make deploy-with-ingress

# Dry run per verificare
make deploy-dry-run

# Check status
make status
```

## 📋 **Requisiti**

### **Sistema**
- Linux, macOS, o Windows con WSL2
- Python 3.11+ (per development)
- 4GB RAM liberi
- 10GB spazio disco

### **Tool Richiesti**

#### **Podman Installation (Raccomandato)**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install podman

# RHEL/CentOS/Fedora
sudo dnf install podman

# macOS
brew install podman
podman machine init
podman machine start

# Verify
podman --version
```

#### **Buildah Installation (Opzionale)**
```bash
# Ubuntu/Debian
sudo apt-get install buildah

# RHEL/CentOS/Fedora
sudo dnf install buildah

# Verify
buildah --version
```

#### **Kubectl Installation**
```bash
# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# macOS
brew install kubectl

# Verify
kubectl version --client
```

## 🏗️ **Build Process**

### **Containerfile Features**
- **Base Image**: `python:3.11-slim-bullseye`
- **Security**: Non-root user (appuser)
- **Multi-stage**: Ottimizzato per size e security
- **Health Check**: Built-in health monitoring
- **Production Ready**: Uvicorn con workers multipli

### **Build Commands**

```bash
# Basic build
./scripts/build-image.sh

# Custom build tool
BUILD_TOOL=buildah ./scripts/build-image.sh

# Custom tag e registry
IMAGE_TAG=v1.0.0 PUSH_REGISTRY=registry.example.com ./scripts/build-image.sh

# Solo build (no push)
BUILD_TOOL=podman IMAGE_TAG=latest ./scripts/build-image.sh
```

### **Build con Makefile**

```bash
# Show help
make help

# Build targets
make build                    # Build con tool di default (podman)
make build-docker            # Force Docker build  
make build-podman            # Force Podman build
make build-buildah           # Force Buildah build

# CI/CD targets
make ci-build                # Lint + Build
make ci-deploy               # Build + Push + Deploy
```

## ☸️ **Kubernetes Deployment**

### **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Ingress       │    │  LoadBalancer    │    │   ClusterIP     │
│                 │    │                  │    │                 │
│ NGINX/Traefik   │    │ Cloud Provider   │    │ Internal Only   │
└─────────┬───────┘    └────────┬─────────┘    └─────────┬───────┘
          │                     │                        │
          └─────────────────────┼────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │      Service          │
                    │  vm-assessment-bom    │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │     Deployment        │
                    │   3 Replicas          │
                    │   Auto-scaling        │
                    └───────────┬───────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
    ┌─────▼─────┐         ┌─────▼─────┐         ┌─────▼─────┐
    │   Pod 1   │         │   Pod 2   │         │   Pod 3   │
    │           │         │           │         │           │
    │ App:8000  │         │ App:8000  │         │ App:8000  │
    └───────────┘         └───────────┘         └───────────┘
```

### **Deployment Components**

#### **1. Namespace & Resources**
```yaml
# k8s/namespace.yaml
- Namespace: vm-assessment
- ResourceQuota: 4 CPU, 8GB RAM limits
- LimitRange: Default resource limits
```

#### **2. Configuration**
```yaml
# k8s/configmap.yaml
- Application config (workers, timeouts, etc.)
- Oracle Cloud pricing configuration
- Environment-specific settings
```

#### **3. Deployment**
```yaml
# k8s/deployment.yaml
- 3 replicas per default
- Rolling update strategy
- Resource limits: 1 CPU, 2GB RAM
- Health checks: liveness + readiness
- Security: non-root, read-only filesystem
```

#### **4. Services**
```yaml
# k8s/service.yaml
- ClusterIP service for internal access
- LoadBalancer service for external access (optional)
- Headless service for direct pod access
```

#### **5. Auto-scaling**
```yaml
# k8s/hpa.yaml
- CPU target: 70%
- Memory target: 80%
- Min replicas: 2
- Max replicas: 10
```

#### **6. Network & Security**
```yaml
# k8s/ingress.yaml
- NGINX Ingress Controller support
- SSL termination
- File upload limits (100MB)
- Rate limiting
- CORS headers
```

### **Deploy Commands**

```bash
# Basic deployment
make deploy

# With custom namespace
NAMESPACE=production make deploy

# With custom image
IMAGE_TAG=v1.0.0 make deploy

# With ingress
make deploy-with-ingress

# Dry run first
make deploy-dry-run
```

### **Advanced Deployment**

```bash
# Deploy to specific cluster context
KUBECTL_CMD="kubectl --context=production" make deploy

# Deploy with custom registry
IMAGE_NAME=myregistry.com/vm-assessment make deploy

# Deploy with environment-specific config
NAMESPACE=staging IMAGE_TAG=develop make deploy
```

## 🔧 **Management Commands**

### **Development**
```bash
make dev              # Run development server
make test             # Run tests  
make lint             # Code linting
make format           # Code formatting
```

### **Container Management**
```bash
make run              # Run locally
make run-detached     # Run in background
make stop             # Stop container
make inspect          # Inspect image
make scan             # Security scan (requires trivy)
```

### **Kubernetes Management**
```bash
make status           # Show deployment status
make logs             # Show pod logs
make port-forward     # Port forward to localhost:8000
make shell            # Get shell access to pod
make update           # Update deployment
make rollback         # Rollback deployment
make undeploy         # Delete deployment
```

### **Cleanup**
```bash
make clean            # Clean containers
make clean-all        # Clean everything
```

## 🌐 **Access Options**

### **1. Port Forward (Development)**
```bash
make port-forward
# Access: http://localhost:8000
```

### **2. LoadBalancer (Cloud)**
```bash
# Get external IP
kubectl get services -n vm-assessment
# Access: http://<EXTERNAL-IP>
```

### **3. Ingress (Production)**
```bash
# Configure your domain in k8s/ingress.yaml
# Access: https://vm-assessment.your-domain.com
```

### **4. NodePort (Testing)**
```bash
# Edit service type to NodePort
kubectl patch svc vm-assessment-bom-service -n vm-assessment -p '{"spec":{"type":"NodePort"}}'
# Access: http://<NODE-IP>:<NODE-PORT>
```

## 🔒 **Security Features**

### **Container Security**
- ✅ Non-root user (UID 1000)
- ✅ Read-only root filesystem
- ✅ No privilege escalation
- ✅ Minimal attack surface
- ✅ Security scanning support

### **Kubernetes Security**
- ✅ Pod Security Context
- ✅ Network Policies (configurable)
- ✅ RBAC ready
- ✅ Secrets management
- ✅ Resource quotas

### **Application Security**
- ✅ File upload validation
- ✅ Session isolation
- ✅ Automatic cleanup
- ✅ Input sanitization
- ✅ CORS protection

## 🚨 **Troubleshooting**

### **Build Issues**
```bash
# Check tool installation
make check-prereqs

# Verbose build
BUILD_TOOL=podman ./scripts/build-image.sh

# Clean and rebuild
make clean build
```

### **Deployment Issues**
```bash
# Check cluster connection
kubectl cluster-info

# Check pod status
kubectl get pods -n vm-assessment

# Check logs
make logs

# Describe problematic pod
kubectl describe pod <pod-name> -n vm-assessment
```

### **Common Issues**

#### **1. Image Pull Errors**
```bash
# Check image exists
podman images vm-assessment-bom

# Retag if needed
podman tag vm-assessment-bom:latest vm-assessment-bom:v1.0.0
```

#### **2. Resource Limits**
```bash
# Check resource usage
kubectl top pods -n vm-assessment

# Adjust limits in k8s/deployment.yaml
```

#### **3. Network Issues**
```bash
# Test internal connectivity
kubectl exec -it deploy/vm-assessment-bom -n vm-assessment -- curl localhost:8000

# Check service endpoints
kubectl get endpoints -n vm-assessment
```

## 📊 **Monitoring & Observability**

### **Built-in Health Checks**
- **Liveness Probe**: HTTP GET `/` every 30s
- **Readiness Probe**: HTTP GET `/` every 10s
- **Startup Probe**: Configurable for slow starts

### **Metrics Collection**
```bash
# Application metrics (if Prometheus available)
curl http://localhost:8000/metrics

# Resource metrics
kubectl top pods -n vm-assessment
```

### **Log Aggregation**
```bash
# Stream logs
make logs

# Get logs from specific pod
kubectl logs <pod-name> -n vm-assessment -f

# Search logs
kubectl logs -l app.kubernetes.io/name=vm-assessment-bom -n vm-assessment | grep ERROR
```

## 🔄 **CI/CD Integration**

### **GitLab CI Example**
```yaml
build:
  script:
    - make ci-build
  
deploy:
  script:
    - make ci-deploy
  only:
    - main
```

### **GitHub Actions Example**
```yaml
- name: Build and Deploy
  run: |
    make ci-build
    make push REGISTRY=${{ secrets.REGISTRY }}
    make deploy
```

### **Jenkins Pipeline**
```groovy
pipeline {
  stages {
    stage('Build') {
      steps {
        sh 'make ci-build'
      }
    }
    stage('Deploy') {
      steps {
        sh 'make deploy'
      }
    }
  }
}
```

## 🎯 **Best Practices**

### **Production Deployment**
1. **Use specific image tags** (not `latest`)
2. **Set resource limits** appropriately
3. **Enable monitoring** and logging
4. **Configure backup** for persistent data
5. **Use secrets** for sensitive data
6. **Enable network policies** for security
7. **Regular security scanning** of images

### **Development Workflow**
1. **Test locally** with `make run`
2. **Dry run deployment** with `make deploy-dry-run`
3. **Use staging environment** before production
4. **Monitor logs** during deployment
5. **Have rollback plan** ready

---

## 🚀 **Ready to Deploy!**

Il tuo VM Assessment BOM Generator è ora pronto per essere deployato su Kubernetes con:

- ✅ **Build multi-tool** (Podman/Docker/Buildah)
- ✅ **Production-ready** container image
- ✅ **Complete Kubernetes** manifests
- ✅ **Auto-scaling** e health checks
- ✅ **Security** best practices
- ✅ **Monitoring** ready
- ✅ **CI/CD** integration ready

**Start deployment**: `make deploy` 🎉