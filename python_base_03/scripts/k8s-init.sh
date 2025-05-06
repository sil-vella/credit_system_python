#!/bin/bash

# Configure logging
exec 1> >(tee -a /workspace/tools/logger/compose.log)
exec 2>&1

# Set color codes for logging
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

# Logging function
log() {
    local level=$1
    local message=$2
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ${YELLOW}[${level}]${NC} ${message}"
}

log "INIT" "Starting Kubernetes cluster initialization..."

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
RED='\033[0;31m'

# Function to log with timestamps and categories
log_with_timestamp() {
    local category="$1"
    local message="$2"
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[$timestamp]${NC} ${YELLOW}[$category]${NC} $message" | tee -a /workspace/tools/logger/compose.log
}

# Function to log diagnostic information
log_diagnostic() {
    local command="$1"
    local description="$2"
    
    echo -e "\n${YELLOW}=== $description ===${NC}" | tee -a /workspace/tools/logger/compose.log
    echo "Command: $command" | tee -a /workspace/tools/logger/compose.log
    echo "----------------------------------------" | tee -a /workspace/tools/logger/compose.log
    eval "$command" 2>&1 | tee -a /workspace/tools/logger/compose.log
    echo "----------------------------------------" | tee -a /workspace/tools/logger/compose.log
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

# Function to check if a port is available
check_port_available() {
    local port=$1
    if command -v nc >/dev/null 2>&1; then
        if nc -z localhost "$port" >/dev/null 2>&1; then
            return 1
        fi
    else
        if curl -s localhost:"$port" >/dev/null 2>&1; then
            return 1
        fi
    fi
    return 0
}

# Function to cleanup any existing resources
cleanup_resources() {
    log "CLEANUP" "Starting thorough cleanup of all resources..."
    
    # 1. Check and remove any existing KinD clusters
    if kind get clusters 2>/dev/null | grep -q "vault-auth"; then
        log "CLEANUP" "Found existing vault-auth cluster, deleting..."
        kind delete cluster --name vault-auth
        log "SUCCESS" "Existing cluster deleted"
        
        # Give Docker some time to release resources
        sleep 5
    else
        log "DEBUG" "No existing KinD clusters found"
    fi
    
    # 2. Check for and remove any leftover containers
    log "CLEANUP" "Checking for leftover containers..."
    for container in $(docker ps -a --filter "name=vault-auth" --format "{{.ID}}"); do
        log "CLEANUP" "Removing container $container..."
        docker rm -f "$container" 2>/dev/null || true
    done
    
    # 3. Clean up any leftover KinD networks
    log "CLEANUP" "Checking for leftover Docker networks..."
    for network in $(docker network ls --filter "name=kind" --format "{{.ID}}"); do
        log "CLEANUP" "Removing network $network..."
        docker network rm "$network" 2>/dev/null || true
    done
    
    # 4. Clean up any leftover volumes
    log "CLEANUP" "Checking for leftover Docker volumes..."
    for volume in $(docker volume ls --filter "name=kind" --format "{{.Name}}"); do
        log "CLEANUP" "Removing volume $volume..."
        docker volume rm "$volume" 2>/dev/null || true
    done
    
    # 5. Clean up any leftover kubeconfig
    log "CLEANUP" "Cleaning up kubeconfig..."
    rm -f /k8s-config/kubeconfig 2>/dev/null || true
    
    # Wait a moment to ensure all resources are released
    log "CLEANUP" "Waiting for resources to be fully released..."
    sleep 5
    
    log "SUCCESS" "Cleanup completed"
}

# Function to perform emergency cleanup on script exit
emergency_cleanup() {
    log "EMERGENCY" "Performing emergency cleanup..."
    cleanup_resources
    exit 1
}

# Function to wait for pods with timeout
wait_for_pods() {
    local timeout=300  # 5 minutes timeout
    local start_time=$(date +%s)
    local end_time=$((start_time + timeout))
    
    log "Waiting for pods to be running (timeout: ${timeout}s)..."
    while [ $(date +%s) -lt $end_time ]; do
        log "Current pod status:"
        kubectl --kubeconfig /k8s-config/kubeconfig get pods -A
        log "Node status:"
        kubectl --kubeconfig /k8s-config/kubeconfig get nodes
        log "Cluster info:"
        kubectl --kubeconfig /k8s-config/kubeconfig cluster-info dump | grep -m 5 "ERROR\|WARN" || true
        
        if kubectl --kubeconfig /k8s-config/kubeconfig get pods -A | grep -q 'Running'; then
            return 0
        fi
        echo "  ⏳ Checking cluster status... ($(($end_time - $(date +%s)))s remaining)"
        sleep 10  # Increased sleep to reduce log spam
    done
    
    # If we timeout, gather diagnostic information
    log "${RED}Error: Timeout waiting for pods to be running${NC}"
    log "${YELLOW}=== Diagnostic Information ===${NC}"
    log "Docker info:"
    docker info || true
    log "Available memory:"
    free -h || true
    log "Disk space:"
    df -h || true
    log "Pod status:"
    kubectl --kubeconfig /k8s-config/kubeconfig get pods -A
    log "Pod details:"
    kubectl --kubeconfig /k8s-config/kubeconfig describe pods -A
    log "${YELLOW}=== End Diagnostic Information ===${NC}"
    return 1
}

# Function to verify kind cluster
verify_kind_cluster() {
    log "VERIFY" "Starting KinD cluster verification..."
    
    # Check if the container exists and is running
    if ! docker ps --filter "name=vault-auth-control-plane" --format "{{.Status}}" | grep -q "Up"; then
        log "ERROR" "KinD control plane container is not running"
        log_diagnostic "docker ps -a --filter name=vault-auth-control-plane" "Docker container status"
        return 1
    fi
    
    # Check kubelet logs
    log "DEBUG" "Checking kubelet logs..."
    log_diagnostic "docker exec vault-auth-control-plane journalctl -u kubelet.service" "Kubelet Service Logs"
    
    # Check static pod manifests
    log "DEBUG" "Checking static pod manifests..."
    log_diagnostic "docker exec vault-auth-control-plane ls -l /etc/kubernetes/manifests/" "Static Pod Manifests"
    
    # Check if API server container is running in containerd
    log "DEBUG" "Checking for kube-apiserver container..."
    log_diagnostic "docker exec vault-auth-control-plane crictl ps | grep kube-apiserver" "API Server Container"
    
    # Check all containers running in the control plane
    log "DEBUG" "Listing all containers..."
    log_diagnostic "docker exec vault-auth-control-plane crictl ps" "All Containers"
    
    # Check container networking
    log "DEBUG" "Checking container networking..."
    log_diagnostic "docker inspect vault-auth-control-plane -f '{{json .NetworkSettings.Networks}}'" "Container network settings"
    
    # Try to get cluster info directly from container
    log "DEBUG" "Attempting to reach API server from inside container..."
    log_diagnostic "docker exec vault-auth-control-plane curl -k https://localhost:6443/healthz" "API Server Health Check"
    
    return 0
}

# Function to wait for API server
wait_for_api_server() {
    local timeout=300  # 5 minutes timeout
    local start_time=$(date +%s)
    local end_time=$((start_time + timeout))
    
    log "INIT" "Waiting for API server to become ready (timeout: ${timeout}s)..."
    
    while [ $(date +%s) -lt $end_time ]; do
        # Check if container is running and healthy
        if ! docker inspect vault-auth-control-plane --format '{{.State.Running}}' 2>/dev/null | grep -q "true"; then
            log "DEBUG" "Waiting for control plane container to start..."
            sleep 5
            continue
        fi

        # Get container IP
        local container_ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' vault-auth-control-plane)
        if [ -z "$container_ip" ]; then
            log "DEBUG" "Waiting for container IP..."
            sleep 5
            continue
        fi

        # Check if kubelet is running
        if docker exec vault-auth-control-plane systemctl is-active kubelet >/dev/null 2>&1; then
            # Check API server health using container IP
            if docker exec vault-auth-control-plane curl -sk https://localhost:6443/healthz >/dev/null 2>&1; then
                log "SUCCESS" "API server is ready"
                
                # Update kubeconfig to use container IP
                log "CONFIG" "Updating kubeconfig to use container IP..."
                sed -i "s|server: https://.*|server: https://${container_ip}:6443|" /k8s-config/kubeconfig
                
                return 0
            fi
        fi
        
        log "DEBUG" "Waiting for API server pod to start..."
        sleep 5
    done
    
    log "ERROR" "Timeout waiting for API server"
    return 1
}

# Function to ensure kind network exists
ensure_kind_network() {
    log "NETWORK" "Ensuring kind network exists..."
    if ! docker network ls | grep -q "kind"; then
        log "NETWORK" "Creating kind network..."
        docker network create kind
        log "SUCCESS" "Kind network created"
    else
        log "NETWORK" "Kind network already exists"
    fi
}

# Main execution starts here
log "START" "Beginning Kubernetes initialization"
log "INIT" "Starting system initialization"

# Install required tools
check_command "docker-cli"
check_command "curl"
check_command "kind"
check_command "kubectl"

# Clean up any existing resources
cleanup_resources

# Ensure kind network exists before cluster creation
ensure_kind_network

# Create the KinD cluster
log "INIT" "Creating Kubernetes cluster using KinD..."
if ! timeout 300 kind create cluster --config /workspace/kind-config.yaml --kubeconfig /k8s-config/kubeconfig; then
    log "ERROR" "Failed to create KinD cluster within timeout"
    exit 1
fi

# Wait for container to be running
log "INIT" "Waiting for control plane container to be ready..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if docker inspect vault-auth-control-plane --format '{{.State.Running}}' 2>/dev/null | grep -q "true"; then
        log "SUCCESS" "Control plane container is running"
        break
    fi
    counter=$((counter + 1))
    sleep 1
done

if [ $counter -eq $timeout ]; then
    log "ERROR" "Timeout waiting for control plane container"
    exit 1
fi

# Get the container IP and port
log "CONFIG" "Getting container IP and port..."
CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' vault-auth-control-plane)
API_PORT=$(docker port vault-auth-control-plane | grep 6443 | sed -e 's/.*://')

if [ -z "$CONTAINER_IP" ] || [ -z "$API_PORT" ]; then
    log "ERROR" "Failed to get container IP or port"
    exit 1
fi

log "INFO" "Control plane container IP: $CONTAINER_IP, API Port: $API_PORT"

# Update kubeconfig with correct IP and port
log "CONFIG" "Updating kubeconfig with container IP and port..."
sed -i "s|server: https://.*|server: https://${CONTAINER_IP}:6443|" /k8s-config/kubeconfig

# Wait for API server
log "INIT" "Waiting for API server to be ready..."
timeout=120
counter=0
while [ $counter -lt $timeout ]; do
    if curl -sk https://${CONTAINER_IP}:6443/healthz >/dev/null 2>&1; then
        log "SUCCESS" "API server is ready"
        break
    fi
    log "INFO" "Waiting for API server... ($(($timeout - $counter))s remaining)"
    counter=$((counter + 1))
    sleep 1
done

if [ $counter -eq $timeout ]; then
    log "ERROR" "Timeout waiting for API server"
    verify_kind_cluster
    exit 1
fi

# Verify kubeconfig is working
log "VERIFY" "Testing cluster connectivity..."
if ! kubectl --kubeconfig /k8s-config/kubeconfig cluster-info; then
    log "ERROR" "Cannot connect to cluster after kubeconfig update"
    verify_kind_cluster
    exit 1
fi

# Add a delay to allow all control plane components to start
log "INIT" "Waiting for control plane components to stabilize..."
sleep 30

# Wait for cluster readiness with timeout
if ! wait_for_pods; then
    log "ERROR" "Cluster failed to become ready"
    exit 1
fi

# Apply the service account configuration
log "INIT" "Creating Flask service account..."
if ! kubectl --kubeconfig /k8s-config/kubeconfig apply -f /workspace/k8s/flask-auth-sa.yaml; then
    log "ERROR" "Failed to create Flask service account"
    exit 1
fi
log "SUCCESS" "Flask service account created successfully"

# Wait for service account to be ready
log "INIT" "Waiting for service account to be ready..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if kubectl --kubeconfig /k8s-config/kubeconfig get serviceaccount flask-auth -n default -o jsonpath='{.secrets[0].name}' >/dev/null 2>&1; then
        log "SUCCESS" "Service account is ready"
        break
    fi
    counter=$((counter + 1))
    sleep 1
done

if [ $counter -eq $timeout ]; then
    log "ERROR" "Timeout waiting for service account to be ready"
    exit 1
fi

# Create directory for service account token
log "INIT" "Setting up service account token directory..."
mkdir -p /var/run/secrets/kubernetes.io/serviceaccount
chmod 755 /var/run/secrets/kubernetes.io/serviceaccount

# Create token and CA cert
log "INIT" "Creating service account token and CA cert..."
if ! kubectl --kubeconfig /k8s-config/kubeconfig create token flask-auth --duration=8760h > /var/run/secrets/kubernetes.io/serviceaccount/token; then
    log "ERROR" "Failed to create service account token"
    exit 1
fi

# Get the CA cert
if ! kubectl --kubeconfig /k8s-config/kubeconfig get secret -n kube-system -o jsonpath='{.items[?(@.type=="kubernetes.io/service-account-token")].data.ca\.crt}' | base64 -d > /var/run/secrets/kubernetes.io/serviceaccount/ca.crt; then
    log "ERROR" "Failed to get CA certificate"
    exit 1
fi

# Verify token and CA cert exist
if [ ! -f "/var/run/secrets/kubernetes.io/serviceaccount/token" ] || [ ! -f "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt" ]; then
    log "ERROR" "Service account token or CA cert not created"
    exit 1
fi

log "SUCCESS" "Service account token and CA cert created successfully"

# Final verification
if kubectl --kubeconfig /k8s-config/kubeconfig cluster-info > /dev/null 2>&1; then
    log "SUCCESS" "Kubernetes cluster is ready"
    log "SUCCESS" "Control plane is healthy"
    log "SUCCESS" "System pods are running"
    exit 0
else
    log "ERROR" "Final cluster verification failed"
    exit 1
fi

log "END" "Setup complete - initialization successful" 