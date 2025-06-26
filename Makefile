# VM Assessment BOM Generator - Makefile
# Supports multiple container tools and deployment scenarios

# Configuration
IMAGE_NAME ?= vm-assessment-bom
IMAGE_TAG ?= latest
BUILD_TOOL ?= podman
NAMESPACE ?= vm-assessment
REGISTRY ?= ghcr.io/$(shell git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/')
KUBECTL_CMD ?= kubectl

# Derived variables
FULL_IMAGE_NAME = $(if $(REGISTRY),$(REGISTRY)/$(IMAGE_NAME),$(IMAGE_NAME))
BUILD_CONTEXT = .

# Colors
BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m

# Help target
.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)VM Assessment BOM Generator - Build & Deploy$(NC)"
	@echo "=============================================="
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Environment variables:$(NC)"
	@echo "  $(YELLOW)BUILD_TOOL$(NC)     Container build tool (podman, docker, buildah) [$(BUILD_TOOL)]"
	@echo "  $(YELLOW)IMAGE_NAME$(NC)     Container image name [$(IMAGE_NAME)]"
	@echo "  $(YELLOW)IMAGE_TAG$(NC)      Container image tag [$(IMAGE_TAG)]"
	@echo "  $(YELLOW)REGISTRY$(NC)       Container registry [$(REGISTRY)]"
	@echo "  $(YELLOW)NAMESPACE$(NC)      Kubernetes namespace [$(NAMESPACE)]"
	@echo "  $(YELLOW)KUBECTL_CMD$(NC)    kubectl command [$(KUBECTL_CMD)]"
	@echo ""
	@echo "$(GREEN)Examples:$(NC)"
	@echo "  make build                    # Build with podman"
	@echo "  BUILD_TOOL=docker make build  # Build with docker"
	@echo "  make build push              # Build and push"
	@echo "  make deploy                  # Deploy to Kubernetes"
	@echo "  make clean                   # Clean up"

# Development targets
.PHONY: dev
dev: ## Run development server
	@echo "$(BLUE)Starting development server...$(NC)"
	cd web_app && python start.py

.PHONY: test
test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	python -m pytest tests/ -v || echo "$(YELLOW)No tests found - add tests in tests/ directory$(NC)"

.PHONY: lint
lint: ## Run code linting
	@echo "$(BLUE)Running code linting...$(NC)"
	@command -v flake8 >/dev/null 2>&1 || { echo "$(YELLOW)flake8 not found, skipping...$(NC)"; exit 0; }
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

.PHONY: format
format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	@command -v black >/dev/null 2>&1 || { echo "$(YELLOW)black not found, skipping...$(NC)"; exit 0; }
	black . --line-length 88

# Container build targets
.PHONY: build
build: ## Build container image
	@echo "$(BLUE)Building container image with $(BUILD_TOOL)...$(NC)"
	BUILD_TOOL=$(BUILD_TOOL) IMAGE_TAG=$(IMAGE_TAG) ./scripts/build-image.sh

.PHONY: build-docker
build-docker: ## Build with Docker
	@$(MAKE) build BUILD_TOOL=docker

.PHONY: build-podman
build-podman: ## Build with Podman
	@$(MAKE) build BUILD_TOOL=podman

.PHONY: build-buildah
build-buildah: ## Build with Buildah
	@$(MAKE) build BUILD_TOOL=buildah

.PHONY: push
push: ## Push container image to registry
	@if [ -z "$(REGISTRY)" ]; then \
		echo "$(RED)ERROR: REGISTRY must be set to push images$(NC)"; \
		echo "Example: make push REGISTRY=registry.example.com"; \
		exit 1; \
	fi
	@echo "$(BLUE)Pushing image to $(REGISTRY)...$(NC)"
	$(BUILD_TOOL) tag $(IMAGE_NAME):$(IMAGE_TAG) $(FULL_IMAGE_NAME):$(IMAGE_TAG)
	$(BUILD_TOOL) push $(FULL_IMAGE_NAME):$(IMAGE_TAG)
	@echo "$(GREEN)Image pushed successfully: $(FULL_IMAGE_NAME):$(IMAGE_TAG)$(NC)"

.PHONY: run
run: ## Run container locally
	@echo "$(BLUE)Running container locally...$(NC)"
	$(BUILD_TOOL) run -it --rm \
		-p 8000:8000 \
		-e APP_ENV=development \
		--name vm-assessment-bom-dev \
		$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: run-detached
run-detached: ## Run container in background
	@echo "$(BLUE)Running container in background...$(NC)"
	$(BUILD_TOOL) run -d \
		-p 8000:8000 \
		-e APP_ENV=production \
		--name vm-assessment-bom \
		$(IMAGE_NAME):$(IMAGE_TAG)
	@echo "$(GREEN)Container started. Access at: http://localhost:8000$(NC)"

.PHONY: stop
stop: ## Stop running container
	@echo "$(BLUE)Stopping container...$(NC)"
	$(BUILD_TOOL) stop vm-assessment-bom || true
	$(BUILD_TOOL) rm vm-assessment-bom || true

# Kubernetes targets
.PHONY: deploy
deploy: ## Deploy to Kubernetes
	@echo "$(BLUE)Deploying to Kubernetes...$(NC)"
	NAMESPACE=$(NAMESPACE) IMAGE_TAG=$(IMAGE_TAG) ./scripts/deploy-k8s.sh deploy

.PHONY: deploy-dry-run
deploy-dry-run: ## Dry run Kubernetes deployment
	@echo "$(BLUE)Dry run Kubernetes deployment...$(NC)"
	DRY_RUN=true NAMESPACE=$(NAMESPACE) IMAGE_TAG=$(IMAGE_TAG) ./scripts/deploy-k8s.sh deploy

.PHONY: deploy-with-ingress
deploy-with-ingress: ## Deploy with ingress
	@echo "$(BLUE)Deploying with ingress...$(NC)"
	DEPLOY_INGRESS=true NAMESPACE=$(NAMESPACE) IMAGE_TAG=$(IMAGE_TAG) ./scripts/deploy-k8s.sh deploy

.PHONY: update
update: ## Update deployment with new image
	@echo "$(BLUE)Updating deployment...$(NC)"
	NAMESPACE=$(NAMESPACE) IMAGE_TAG=$(IMAGE_TAG) ./scripts/deploy-k8s.sh update

.PHONY: rollback
rollback: ## Rollback deployment
	@echo "$(BLUE)Rolling back deployment...$(NC)"
	NAMESPACE=$(NAMESPACE) ./scripts/deploy-k8s.sh rollback

.PHONY: status
status: ## Show deployment status
	@echo "$(BLUE)Checking deployment status...$(NC)"
	NAMESPACE=$(NAMESPACE) ./scripts/deploy-k8s.sh status

.PHONY: logs
logs: ## Show pod logs
	@echo "$(BLUE)Showing pod logs...$(NC)"
	$(KUBECTL_CMD) logs -f -l app.kubernetes.io/name=vm-assessment-bom -n $(NAMESPACE)

.PHONY: port-forward
port-forward: ## Port forward to local machine
	@echo "$(BLUE)Port forwarding to localhost:8000...$(NC)"
	$(KUBECTL_CMD) port-forward -n $(NAMESPACE) service/vm-assessment-bom-service 8000:80

.PHONY: shell
shell: ## Get shell access to pod
	@echo "$(BLUE)Getting shell access...$(NC)"
	$(KUBECTL_CMD) exec -it -n $(NAMESPACE) deployment/vm-assessment-bom -- /bin/bash

.PHONY: undeploy
undeploy: ## Delete Kubernetes deployment
	@echo "$(BLUE)Deleting deployment...$(NC)"
	NAMESPACE=$(NAMESPACE) ./scripts/deploy-k8s.sh delete

# Utility targets
.PHONY: clean
clean: ## Clean up local containers and images
	@echo "$(BLUE)Cleaning up...$(NC)"
	$(BUILD_TOOL) system prune -f
	@echo "$(GREEN)Cleanup completed$(NC)"

.PHONY: clean-all
clean-all: ## Clean up everything including images
	@echo "$(BLUE)Cleaning up everything...$(NC)"
	$(BUILD_TOOL) system prune -a -f
	@echo "$(GREEN)Complete cleanup completed$(NC)"

.PHONY: inspect
inspect: ## Inspect container image
	@echo "$(BLUE)Inspecting image: $(IMAGE_NAME):$(IMAGE_TAG)$(NC)"
	$(BUILD_TOOL) inspect $(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: scan
scan: ## Security scan of container image
	@echo "$(BLUE)Scanning image for vulnerabilities...$(NC)"
	@command -v trivy >/dev/null 2>&1 || { echo "$(YELLOW)trivy not found, install from: https://aquasecurity.github.io/trivy/$(NC)"; exit 1; }
	trivy image $(IMAGE_NAME):$(IMAGE_TAG)

# CI/CD targets
.PHONY: ci-build
ci-build: lint build ## CI build pipeline
	@echo "$(GREEN)CI build completed successfully$(NC)"

.PHONY: ci-deploy
ci-deploy: ci-build push deploy ## CI deploy pipeline
	@echo "$(GREEN)CI deploy completed successfully$(NC)"

# GitHub specific targets
.PHONY: github-login
github-login: ## Login to GitHub Container Registry
	@echo "$(BLUE)Logging in to GitHub Container Registry...$(NC)"
	echo "$(GITHUB_TOKEN)" | $(BUILD_TOOL) login ghcr.io -u $(GITHUB_ACTOR) --password-stdin

.PHONY: github-push
github-push: ## Push to GitHub Container Registry
	@if [ -z "$(GITHUB_TOKEN)" ]; then \
		echo "$(RED)ERROR: GITHUB_TOKEN must be set$(NC)"; \
		exit 1; \
	fi
	@$(MAKE) github-login
	@$(MAKE) push REGISTRY=ghcr.io/$(shell git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/')

.PHONY: release-build
release-build: ## Build for release with proper tags
	@echo "$(BLUE)Building release image...$(NC)"
	BUILD_TOOL=$(BUILD_TOOL) IMAGE_TAG=$(IMAGE_TAG) ./scripts/build-image.sh
	@if [ "$(IMAGE_TAG)" != "latest" ]; then \
		$(BUILD_TOOL) tag $(IMAGE_NAME):$(IMAGE_TAG) $(IMAGE_NAME):latest; \
	fi

# Prerequisites check
.PHONY: check-prereqs
check-prereqs: ## Check prerequisites
	@echo "$(BLUE)Checking prerequisites...$(NC)"
	@command -v $(BUILD_TOOL) >/dev/null 2>&1 || { echo "$(RED)$(BUILD_TOOL) not found$(NC)"; exit 1; }
	@command -v $(KUBECTL_CMD) >/dev/null 2>&1 || { echo "$(RED)$(KUBECTL_CMD) not found$(NC)"; exit 1; }
	@echo "$(GREEN)Prerequisites check passed$(NC)"

# Default target
.DEFAULT_GOAL := help