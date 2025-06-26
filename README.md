# VM Assessment BOM Generator

**Professional web-based tool for generating Oracle Cloud Infrastructure Bill of Materials from RVTools exports.**

![Web Interface](https://img.shields.io/badge/Interface-Web%20App-blue)
![Container](https://img.shields.io/badge/Container-Ready-green)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Native-purple)
![License](https://img.shields.io/badge/License-Enterprise-orange)

## 🚀 **Quick Start**

### **1. Development Mode**
```bash
# Start development server
make dev
# Access: http://localhost:8000
```

### **2. Container Deployment**
```bash
# Build container
make build

# Run locally
make run
# Access: http://localhost:8000
```

### **3. Kubernetes Deployment**
```bash
# Deploy to cluster
make deploy

# Access via port-forward
make port-forward
# Access: http://localhost:8000
```

## 📋 **Features**

### **🎯 Core Functionality**
- ✅ **RVTools Import**: Upload ZIP exports from RVTools
- ✅ **Oracle Cloud Pricing**: Accurate OCI cost calculations
- ✅ **Multiple Formats**: Excel, CSV, Text, JSON reports
- ✅ **Sales Reports**: Professional presentations with ROI analysis
- ✅ **Real-time Processing**: Live progress tracking
- ✅ **Secure Upload**: 100MB file limit with validation

### **🌐 Web Interface**
- ✅ **Modern UI**: Bootstrap 5 responsive design
- ✅ **Drag & Drop**: Intuitive file upload
- ✅ **Progress Tracking**: Real-time processing updates
- ✅ **Results Page**: Professional summary with download links
- ✅ **Help Documentation**: Integrated user guide
- ✅ **Mobile Friendly**: Works on all devices

### **🏗️ Enterprise Ready**
- ✅ **Container Native**: Podman/Docker/Buildah support
- ✅ **Kubernetes Ready**: Complete K8s manifests
- ✅ **High Availability**: Auto-scaling and health checks
- ✅ **Security**: Non-root containers, resource limits
- ✅ **Monitoring**: Prometheus metrics ready
- ✅ **CI/CD Ready**: Complete automation

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Interface                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Upload    │  │ Processing  │  │       Results           │  │
│  │    Page     │  │    Page     │  │       Page              │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                   FastAPI Backend                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Upload    │  │ Processing  │  │      Download           │  │
│  │  Endpoint   │  │   Engine    │  │     Endpoints           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                 Processing Modules                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  RVTools    │  │   Oracle    │  │      Report             │  │
│  │ Processor   │  │   Pricing   │  │    Generators           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 **Project Structure**

```
vm-assessment-bom/
├── 🌐 Web Application
│   └── web_app/
│       ├── app.py                 # Main FastAPI application
│       ├── start.py               # Development server
│       ├── pricing.json           # Oracle Cloud pricing data
│       ├── templates/             # HTML templates
│       │   ├── index.html         # Main upload page
│       │   ├── processing.html    # Progress tracking
│       │   ├── results.html       # Results & downloads
│       │   └── help.html          # Documentation
│       ├── static/                # Static assets
│       │   └── uploads/           # Upload storage
│       ├── models/                # Data models
│       ├── processors/            # RVTools processing
│       ├── pricing/               # Cost calculations
│       └── reports/               # Report generators
│
├── 🐳 Container & Deployment
│   ├── Containerfile             # Container definition
│   ├── requirements.txt          # Python dependencies
│   ├── .containerignore          # Build optimization
│   └── k8s/                      # Kubernetes manifests
│       ├── namespace.yaml        # Namespace setup
│       ├── deployment.yaml       # Application deployment
│       ├── service.yaml          # Service definitions
│       ├── ingress.yaml          # Ingress configuration
│       └── *.yaml               # HPA, PDB, ConfigMaps
│
├── 🔧 Scripts & Automation
│   ├── Makefile                  # Build & deploy automation
│   └── scripts/
│       ├── build-image.sh        # Multi-tool container build
│       ├── deploy-k8s.sh         # Kubernetes deployment
│       └── test-local.sh         # Local testing
│
└── 📖 Documentation
    ├── README.md                 # This file
    ├── DEPLOYMENT.md             # Deployment guide
    └── KUBERNETES-SUMMARY.md     # K8s quick reference
```

## 🛠️ **Development**

### **Prerequisites**
- Python 3.11+
- Container tool (Podman/Docker/Buildah)
- kubectl (for Kubernetes)

### **Local Development**
```bash
# Clone repository
git clone <repository-url>
cd vm-assessment-bom

# Install dependencies
pip install -r requirements.txt

# Start development server
make dev

# Access application
open http://localhost:8000
```

### **Testing**
```bash
# Run tests
make test

# Test container locally
make build
make run

# Run comprehensive tests
./scripts/test-local.sh
```

## 📦 **Deployment Options**

### **1. Local Container**
```bash
# Build and run
make build run

# With custom configuration
HOST=0.0.0.0 PORT=8080 make run
```

### **2. Kubernetes**
```bash
# Basic deployment
make deploy

# Production deployment
NAMESPACE=production IMAGE_TAG=v1.0.0 make deploy-with-ingress

# Monitor deployment
make status logs
```

### **3. Cloud Platforms**

#### **AWS EKS**
```bash
# Configure kubectl for EKS
aws eks update-kubeconfig --name your-cluster

# Deploy
make deploy
```

#### **Google GKE**
```bash
# Configure kubectl for GKE
gcloud container clusters get-credentials your-cluster

# Deploy
make deploy
```

#### **Azure AKS**
```bash
# Configure kubectl for AKS
az aks get-credentials --name your-cluster --resource-group your-rg

# Deploy
make deploy
```

## ⚙️ **Configuration**

### **Environment Variables**
```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
vim .env
```

### **Key Settings**
- `APP_ENV`: Environment (development/staging/production)
- `WORKERS`: Number of worker processes
- `UPLOAD_MAX_SIZE`: Maximum file size (bytes)
- `SESSION_TIMEOUT`: Session timeout (seconds)

### **Oracle Cloud Pricing**
Edit `web_app/pricing.json` to customize:
- Compute pricing (OCPU, memory)
- Storage pricing (block volumes)
- Licensing costs (Windows, Oracle DB)

## 🔍 **Usage**

### **1. Upload RVTools File**
- Drag & drop RVTools ZIP export
- Select desired report formats
- Click "Generate BOM Reports"

### **2. Monitor Processing**
- Real-time progress tracking
- Live status updates
- Processing typically takes 30-60 seconds

### **3. Download Results**
- Professional results page
- Multiple report formats
- Download individual files or all at once

### **4. Report Types**
- **Sales Excel**: Professional presentations with ROI
- **Technical Excel**: Detailed VM specifications
- **CSV**: Raw data for analysis
- **Text**: Human-readable summaries

## 🔧 **Management**

### **Container Commands**
```bash
make help              # Show all commands
make build             # Build container
make run               # Run locally
make stop              # Stop container
make inspect           # Inspect image
make clean             # Clean up
```

### **Kubernetes Commands**
```bash
make deploy            # Deploy to cluster
make status            # Check deployment
make logs              # View logs
make port-forward      # Local access
make shell             # Pod shell access
make rollback          # Rollback deployment
make undeploy          # Remove deployment
```

### **Monitoring**
```bash
# Application logs
make logs

# Resource usage
kubectl top pods -n vm-assessment

# Admin interface
curl http://localhost:8000/admin/sessions
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Build Problems**
```bash
# Check prerequisites
make check-prereqs

# Clean and rebuild
make clean build

# Use different build tool
BUILD_TOOL=docker make build
```

#### **Upload Failures**
- Check file format (ZIP only)
- Verify file size (<100MB)
- Ensure RVTools export is complete

#### **Processing Errors**
- Check application logs: `make logs`
- Verify pricing.json configuration
- Ensure sufficient resources

## 📊 **Monitoring & Metrics**

### **Health Checks**
- **Liveness**: `GET /`
- **Readiness**: `GET /`
- **Admin**: `GET /admin/sessions`

### **Performance**
- **Upload Speed**: ~10MB/s typical
- **Processing Time**: 30-60 seconds for standard exports
- **Memory Usage**: ~512MB per session
- **CPU Usage**: Scales with file size

## 🔒 **Security**

### **Container Security**
- Non-root user execution
- Read-only filesystem
- Resource limits enforced
- Vulnerability scanning ready

### **Application Security**
- File type validation
- Size limits enforced
- Session isolation
- Automatic cleanup
- Input sanitization

## 📝 **License**

Enterprise License - See license terms for usage restrictions.

## 🤝 **Support**

- **Documentation**: See `DEPLOYMENT.md` for detailed guides
- **Issues**: Check logs and troubleshooting section
- **Updates**: Follow semantic versioning

---

## 🚀 **Ready to Deploy!**

Your VM Assessment BOM Generator is ready for professional use:

✅ **Modern web interface** with professional design  
✅ **Enterprise container deployment** with Kubernetes  
✅ **Production-ready** with security and monitoring  
✅ **Sales-ready reports** with ROI analysis  

**Start now**: `make dev` 🎉