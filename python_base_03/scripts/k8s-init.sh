#!/bin/sh

# k8s-init.sh
# Purpose: Initialize a Kubernetes cluster using KinD (Kubernetes in Docker)
# This script:
# 1. Installs required tools
# 2. Creates a KinD cluster
# 3. Waits for cluster readiness
# 4. Verifies cluster health

set -e  # Exit on any error

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log function for consistent output
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Function to install kubectl
install_kubectl() {
    log "Installing kubectl..."
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    chmod +x kubectl
    mv kubectl /usr/local/bin/
}

# Function to check if a command exists
check_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        log "Installing $1..."
        case "$1" in
            kubectl)
                install_kubectl
                ;;
            *)
                apk add --no-cache "$1"
                ;;
        esac
    else
        log "$1 is already installed"
    fi
}

# Main initialization function
init_kubernetes() {
    log "🔄 Phase 1: System initialization"

    # Install required tools
    for tool in docker-cli curl kind kubectl; do
        check_command "$tool"
    done

    # Ensure we're in the workspace directory
    cd /workspace

    # Create KinD cluster
    log "Creating Kubernetes cluster using KinD..."
    kind create cluster --config kind-config.yaml --kubeconfig /k8s-config/kubeconfig

    # Wait for cluster readiness
    log "Waiting for cluster to be ready..."
    until kubectl --kubeconfig /k8s-config/kubeconfig get pods -A | grep -q 'Running'; do
        echo "  ⏳ Checking cluster status..."
        sleep 5
    done

    # Verify cluster health
    if kubectl --kubeconfig /k8s-config/kubeconfig cluster-info > /dev/null 2>&1; then
        log "${GREEN}✅ Kubernetes cluster is ready${NC}"
        log "${GREEN}✅ Control plane is healthy${NC}"
    else
        log "Error: Cluster health check failed"
        exit 1
    fi
}

# Main execution
log "Starting Kubernetes initialization"
init_kubernetes
log "🔒 Setup complete - initialization successful" 