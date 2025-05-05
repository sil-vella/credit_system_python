#!/bin/bash

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

log "INIT" "Starting Vault development configuration..."

# Wait for Vault to be ready
log "WAIT" "Waiting for Vault to become ready..."
until curl -fs http://127.0.0.1:8200/v1/sys/health; do
    log "WAIT" "Vault not ready, retrying in 2 seconds..."
    sleep 2
done
log "SUCCESS" "Vault is ready"

# Set environment variables
log "CONFIG" "Setting up Vault environment variables..."
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='dev-token'
log "INFO" "Using Vault address: $VAULT_ADDR"

# Enable KV secrets engine
log "SETUP" "Enabling KV v2 secrets engine..."
log_cmd "vault secrets enable -path=secret kv-v2" "Enable KV v2 secrets engine"

# Store MongoDB secrets
log "SECRETS" "Storing MongoDB development secrets..."
log_cmd "vault kv put secret/app/mongodb \
    service_name='mongodb' \
    root_username='root' \
    root_password='rootpassword' \
    db_name='credit_system'" "Create MongoDB development secrets"

# Store Redis secrets
log "SECRETS" "Storing Redis development secrets..."
log_cmd "vault kv put secret/app/redis \
    service_name='redis' \
    host='redis' \
    port='6379' \
    password='redis_password'" "Create Redis development secrets"

# Store Flask secrets
log "SECRETS" "Storing Flask development secrets..."
log_cmd "vault kv put secret/app/flask \
    service_name='flask' \
    jwt_key='dev_jwt_key' \
    secret_key='dev_secret_key'" "Create Flask development secrets"

log "SUCCESS" "✅ Vault development configuration completed successfully!"
log "SUMMARY" "The following components have been configured:"
log "SUMMARY" "  - KV v2 secrets engine enabled"
log "SUMMARY" "  - MongoDB development secrets stored"
log "SUMMARY" "  - Redis development secrets stored"
log "SUMMARY" "  - Flask development secrets stored" 