# VM Assessment BOM Generator

**Professional web-based tool for generating Oracle Cloud Infrastructure Bill of Materials from RVTools exports.**

![Web Interface](https://img.shields.io/badge/Interface-Web%20App-blue)
![Container](https://img.shields.io/badge/Container-Ready-green)
![Podman](https://img.shields.io/badge/Podman-Native-purple)
![License](https://img.shields.io/badge/License-Enterprise-orange)

## 🚀 **Quick Start**

### **1. Local Development**
```bash
# Direct Python development
./scripts/dev-local.sh
# Access: http://localhost:8000
```

### **2. Container Development**
```bash
# Build and run with Podman
./scripts/dev-simple.sh
# Access: http://localhost:8080
```

### **3. Testing**
```bash
# Test container deployment
./scripts/test-simple.sh
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
- ✅ **Container Native**: Podman support
- ✅ **Lightweight**: No complex orchestration needed
- ✅ **Secure**: Non-root containers, resource limits
- ✅ **Simple**: Easy local development and testing
- ✅ **Professional**: Production-ready reports and analysis

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
│   └── .containerignore          # Build optimization
│
├── 🔧 Scripts & Automation
│   └── scripts/
│       ├── dev-local.sh          # Direct Python development
│       ├── dev-simple.sh         # Podman container development
│       ├── test-local.sh         # Local testing
│       └── test-simple.sh        # Container testing
│
└── 📖 Documentation
    ├── README.md                 # This file
    ├── DEPLOYMENT.md             # Deployment guide
    └── KUBERNETES-SUMMARY.md     # K8s quick reference
```

## 🛠️ **Development**

### **Prerequisites**
- Python 3.11+
- Podman (open source container tool)

### **Local Development**

#### **Option 1: Direct Python (fastest)**
```bash
# Clone repository
git clone <repository-url>
cd rvtools

# Install dependencies
pip install -r requirements.txt

# Start development server
./scripts/dev-local.sh

# Access application
open http://localhost:8000
```

#### **Option 2: Container (production-like)**
```bash
# Build and run with Podman
./scripts/dev-simple.sh

# Access application
open http://localhost:8080
```

### **Testing**
```bash
# Test direct Python setup
./scripts/test-local.sh

# Test container setup
./scripts/test-simple.sh
```

## 📦 **Deployment Options**

### **1. Local Development**
```bash
# Direct Python (fastest)
./scripts/dev-local.sh

# Container-based (production-like)
./scripts/dev-simple.sh
```

### **2. Production Container**
```bash
# Build container
podman build -t vm-assessment-bom .

# Run container
podman run -d -p 8080:8080 \
  -v ./uploads:/app/uploads \
  -v ./reports:/app/reports \
  vm-assessment-bom
```

### **3. Server Deployment**
For production deployment, use any container orchestration platform:
- **Podman** on single servers
- **Docker Swarm** for multi-node
- **Kubernetes** for enterprise scale

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
# Build container
podman build -t vm-assessment-bom .

# Run container
podman run -d --name vm-assessment-dev -p 8080:8080 vm-assessment-bom

# View logs
podman logs vm-assessment-dev

# Stop container
podman stop vm-assessment-dev

# Remove container
podman rm vm-assessment-dev
```

### **Development Scripts**
```bash
# Start development
./scripts/dev-simple.sh

# Test application
./scripts/test-simple.sh

# Stop development
podman stop vm-assessment-dev
```

### **Monitoring**
```bash
# Application logs
podman logs vm-assessment-dev

# Container stats
podman stats vm-assessment-dev

# Admin interface
curl http://localhost:8080/admin/sessions
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Build Problems**
```bash
# Check Podman installation
podman --version

# Clean and rebuild
podman rmi vm-assessment-bom || true
podman build -t vm-assessment-bom .

# Check container logs
podman logs vm-assessment-dev
```

#### **Upload Failures**
- Check file format (ZIP only)
- Verify file size (<100MB)
- Ensure RVTools export is complete

#### **Processing Errors**
- Check application logs: `podman logs vm-assessment-dev`
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
✅ **Simple container deployment** with Podman  
✅ **Production-ready** with security and monitoring  
✅ **Sales-ready reports** with ROI analysis  

**Start now**: `./scripts/dev-simple.sh` 🎉