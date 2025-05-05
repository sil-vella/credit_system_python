#!/bin/sh

set -e  # Exit on any error

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to log with timestamps and categories
log() {
    local category="$1"
    local message="$2"
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[$timestamp]${NC} ${YELLOW}[$category]${NC} $message" | tee -a /workspace/tools/logger/compose.log
}

# Function to log command output
log_cmd() {
    local cmd="$1"
    local description="$2"
    log "CMD" "Executing: $description"
    log "CMD" "Command: $cmd"
    eval "$cmd" 2>&1 | tee -a /workspace/tools/logger/compose.log
    local status=$?
    if [ $status -eq 0 ]; then
        log "SUCCESS" "$description completed successfully"
    else
        log "ERROR" "$description failed with status $status"
        return $status
    fi
}

log "INIT" "Starting Kubernetes authentication setup in Vault..."

# Wait for Vault to be ready
log "WAIT" "Waiting for Vault to become ready..."
until curl -fs http://vault:8200/v1/sys/health; do
    log "WAIT" "Vault not ready, retrying in 5 seconds..."
    sleep 5
done
log "SUCCESS" "Vault is ready"

# Enable KV secrets engine
log "SETUP" "Enabling KV secrets engine..."
log_cmd "vault secrets enable -version=2 kv || true" "Enable KV secrets engine"
log_cmd "vault secrets move kv secret || true" "Move KV secrets to 'secret' path"

# Enable Kubernetes auth method
log "SETUP" "Enabling Kubernetes authentication method..."
log_cmd "vault auth enable kubernetes" "Enable Kubernetes auth"

# Get the Kubernetes CA certificate
log "SETUP" "Retrieving Kubernetes CA certificate and token..."
KUBE_CA_CERT=$(cat /var/run/secrets/kubernetes.io/serviceaccount/ca.crt)
KUBE_TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
KUBE_HOST="https://vault-auth-control-plane:6443"
log "INFO" "Using Kubernetes host: $KUBE_HOST"

# Configure Kubernetes auth method
log "CONFIG" "Configuring Kubernetes authentication method..."
log_cmd "vault write auth/kubernetes/config kubernetes_host='$KUBE_HOST' kubernetes_ca_cert='$KUBE_CA_CERT' token_reviewer_jwt='$KUBE_TOKEN'" "Configure Kubernetes auth"

# Create a policy for Flask app
log "POLICY" "Creating Vault policy for Flask application..."
policy_content="# Allow Flask app to read secrets
path \"secret/data/app/*\" {
    capabilities = [\"read\"]
}

# Allow Flask app to list available secrets
path \"secret/metadata/app/*\" {
    capabilities = [\"list\"]
}

# Deny all other paths
path \"*\" {
    capabilities = [\"deny\"]
}"

log "DEBUG" "Policy content:"
echo "$policy_content" | tee -a /workspace/tools/logger/compose.log
log_cmd "echo '$policy_content' | vault policy write flask-policy -" "Write Flask policy"

# Create a role for Flask app
log "ROLE" "Creating Kubernetes authentication role..."
log_cmd "vault write auth/kubernetes/role/flask-auth \
    bound_service_account_names=flask-auth \
    bound_service_account_namespaces=default \
    policies=flask-policy \
    ttl=1h" "Create Flask auth role"

# Create Flask application secrets
log "SECRETS" "Creating Flask application secrets..."
log_cmd "vault kv put secret/app/flask \
    debug='true' \
    host='0.0.0.0' \
    port='5000' \
    secret_key='$(openssl rand -hex 32)' \
    jwt_key='$(openssl rand -hex 32)' \
    service_name='flask' \
    encryption_key='$(openssl rand -hex 32)' \
    encryption_salt='$(openssl rand -hex 16)' \
    pythonpath='/app' \
    url='http://localhost:5000'" "Create Flask secrets"

log "SUCCESS" "✅ Kubernetes authentication setup completed successfully!"
log "SUMMARY" "The following components have been configured:"
log "SUMMARY" "  - Kubernetes auth method enabled"
log "SUMMARY" "  - Flask policy created"
log "SUMMARY" "  - Flask auth role created" 