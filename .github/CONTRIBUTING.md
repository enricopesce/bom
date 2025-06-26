# Contributing to VM Assessment BOM Generator

Thank you for your interest in contributing to the VM Assessment BOM Generator! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Security](#security)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this standard. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Container runtime (Docker, Podman, or Buildah)
- kubectl (for Kubernetes development)
- Git

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/vm-assessment-bom.git
   cd vm-assessment-bom
   ```

2. **Set up Development Environment**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. **Start Development Server**
   ```bash
   make dev
   # Or manually: cd web_app && python start.py
   ```

4. **Verify Setup**
   - Visit http://localhost:8000
   - Upload a test RVTools file
   - Verify all features work

## Development Setup

### Project Structure

```
vm-assessment-bom/
├── web_app/                 # Main application
│   ├── app.py              # FastAPI application
│   ├── models/             # Data models
│   ├── processors/         # File processing
│   ├── pricing/            # Cost calculations
│   ├── reports/            # Report generation
│   └── templates/          # HTML templates
├── k8s/                    # Kubernetes manifests
├── scripts/                # Build and deployment scripts
└── .github/                # GitHub workflows and templates
```

### Environment Configuration

1. **Copy Environment Template**
   ```bash
   cp .env.example .env
   ```

2. **Configure for Development**
   ```bash
   # Edit .env with your settings
   APP_ENV=development
   LOG_LEVEL=debug
   ```

## Making Changes

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/feature-name` - Feature development
- `bugfix/bug-description` - Bug fixes
- `hotfix/critical-fix` - Critical production fixes

### Creating a Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### Development Workflow

1. **Make your changes**
   - Follow the existing code structure
   - Add tests for new functionality
   - Update documentation as needed

2. **Test your changes**
   ```bash
   # Run tests
   make test
   
   # Run linting
   make lint
   
   # Test container build
   make build
   ```

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
cd web_app
python -m pytest tests/test_specific.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Test Categories

1. **Unit Tests** - Test individual functions and classes
2. **Integration Tests** - Test component interactions
3. **End-to-End Tests** - Test complete workflows
4. **Container Tests** - Test containerized application

### Writing Tests

- Place tests in `web_app/tests/`
- Follow naming convention: `test_*.py`
- Use pytest fixtures for common setup
- Mock external dependencies
- Test both success and failure cases

### Manual Testing

1. **Web Interface Testing**
   - Test file upload with various RVTools files
   - Test all report formats
   - Test error conditions
   - Test on different browsers

2. **Container Testing**
   ```bash
   # Build and test container
   make build
   make run
   
   # Test with scripts
   ./scripts/test-local.sh
   ```

3. **Kubernetes Testing**
   ```bash
   # Deploy to test environment
   make deploy-dry-run
   make deploy
   ```

## Submitting Changes

### Pull Request Process

1. **Update your branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout your-feature-branch
   git rebase develop
   ```

2. **Push your changes**
   ```bash
   git push origin your-feature-branch
   ```

3. **Create Pull Request**
   - Use the PR template
   - Fill out all relevant sections
   - Link related issues
   - Add reviewers

### PR Requirements

- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Container builds successfully
- [ ] No security vulnerabilities
- [ ] Performance impact considered

## Code Style

### Python Style

- Follow PEP 8
- Use Black for formatting
- Use flake8 for linting
- Maximum line length: 127 characters

```bash
# Format code
black web_app/

# Check linting
flake8 web_app/
```

### File Organization

- Keep files focused and single-purpose
- Use clear, descriptive names
- Organize imports (standard, third-party, local)
- Add docstrings to functions and classes

### Commit Messages

Follow conventional commit format:

```
type(scope): description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes
- refactor: Code refactoring
- test: Test changes
- chore: Maintenance tasks
```

Examples:
```
feat(reports): add CSV export functionality
fix(upload): handle large file uploads correctly
docs(readme): update installation instructions
```

## Security

### Security Guidelines

- Never commit secrets or credentials
- Validate all user inputs
- Use parameterized queries
- Follow principle of least privilege
- Keep dependencies updated

### Security Testing

```bash
# Run security scans
pip install bandit safety
bandit -r web_app/
safety check
```

### Reporting Security Issues

Please report security vulnerabilities privately to the maintainers rather than opening public issues.

## Documentation

### Documentation Standards

- Update README.md for user-facing changes
- Update DEPLOYMENT.md for deployment changes
- Add inline code comments for complex logic
- Update API documentation for endpoint changes

### Documentation Testing

- Ensure all examples work
- Test deployment instructions
- Verify links are valid
- Check formatting renders correctly

## Container Development

### Container Guidelines

- Keep images small and secure
- Use non-root users
- Minimize attack surface
- Follow container best practices

### Testing Containers

```bash
# Build and test
make build

# Security scan
make scan

# Size check
docker images vm-assessment-bom
```

## Kubernetes Development

### Kubernetes Guidelines

- Follow Kubernetes best practices
- Use proper resource limits
- Implement health checks
- Use namespaces for isolation

### Testing Kubernetes

```bash
# Validate manifests
kubectl apply --dry-run=client -f k8s/

# Deploy to test environment
make deploy-dry-run
```

## Release Process

### Version Management

- Use semantic versioning (MAJOR.MINOR.PATCH)
- Tag releases in git
- Update version in relevant files

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Container builds successfully
- [ ] Security scans pass
- [ ] Performance tested
- [ ] Kubernetes deployment tested

## Getting Help

### Resources

- Check existing issues and PRs
- Review documentation
- Look at test examples
- Check CI/CD logs

### Asking for Help

- Use GitHub Discussions for questions
- Create issues for bugs
- Tag maintainers for urgent issues
- Join community channels (if available)

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to the VM Assessment BOM Generator!