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

log "INIT" "Starting Vault secrets initialization..."

set -e  # Exit on any error

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'

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

# Wait for Vault to be ready
log "WAIT" "Waiting for Vault to become ready..."
until curl -fs http://vault:8200/v1/sys/health; do
  log "WAIT" "Vault not ready, retrying in 5 seconds..."
  sleep 5
done
log "SUCCESS" "Vault is ready"

# Enable KV v2 secrets engine
log "SETUP" "Enabling KV v2 secrets engine..."
log_cmd "vault secrets enable -path=secret kv-v2" "Enable KV v2 secrets engine"

# Initialize Flask secrets
log "SECRETS" "Initializing Flask application secrets..."
log_cmd "vault kv put secret/app/flask \
  service_name='flask' \
  port='5000' \
  pythonpath='/app' \
  debug='true' \
  url='http://localhost:5000' \
  jwt_key='$(openssl rand -hex 32)' \
  access_token_expires='3600' \
  refresh_token_expires='604800' \
  jwt_algorithm='HS256' \
  jwt_token_type='bearer' \
  jwt_header_name='Authorization' \
  jwt_header_type='Bearer' \
  jwt_query_string_name='token' \
  jwt_query_string_value_prefix='Bearer' \
  jwt_cookie_name='access_token' \
  jwt_cookie_csrf_protect='true' \
  jwt_cookie_secure='false' \
  jwt_cookie_samesite='Lax' \
  jwt_cookie_domain='' \
  jwt_cookie_path='/' \
  jwt_cookie_max_age='3600' \
  ssl='false' \
  min_conn='1' \
  max_conn='10' \
  connect_timeout='10' \
  statement_timeout='30000' \
  keepalive='1' \
  keepalive_idle='30' \
  keepalive_interval='10' \
  keepalive_count='5' \
  max_conn_per_user='5' \
  max_query_size='10000' \
  max_result_size='1048576' \
  retry_count='3' \
  retry_delay='1' \
  rate_limit_storage_url='redis://localhost:6379/0' \
  logging_enabled='true' \
  log_level='INFO' \
  log_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' \
  log_file='/var/log/flask/app.log' \
  redis_ssl='false' \
  redis_ssl_verify_mode='none' \
  redis_max_conn='10' \
  redis_socket_timeout='5' \
  redis_socket_connect_timeout='5' \
  redis_retry_on_timeout='true' \
  redis_max_retries='3' \
  redis_key_prefix='app' \
  redis_encryption_key='$(openssl rand -hex 32)' \
  redis_encryption_salt='$(openssl rand -hex 16)' \
  redis_encryption_iterations='100000' \
  redis_max_cache_size='1048576' \
  redis_cache_ttl='300' \
  rate_limit_enabled='true' \
  temp_dir='/tmp' \
  credit_system_url='http://localhost:8000' \
  credit_system_api_key='$(openssl rand -hex 32)' \
  rate_limit_ip_requests='100' \
  rate_limit_ip_window='60' \
  rate_limit_ip_prefix='rate_limit:ip' \
  rate_limit_user_requests='1000' \
  rate_limit_user_window='3600' \
  rate_limit_user_prefix='rate_limit:user' \
  rate_limit_api_key_requests='10000' \
  rate_limit_api_key_window='3600' \
  rate_limit_api_key_prefix='rate_limit:api_key' \
  rate_limit_headers_enabled='true' \
  rate_limit_header_limit='X-RateLimit-Limit' \
  rate_limit_header_remaining='X-RateLimit-Remaining' \
  rate_limit_header_reset='X-RateLimit-Reset' \
  auto_ban_enabled='true' \
  auto_ban_violations_threshold='5' \
  auto_ban_duration='3600' \
  auto_ban_window='300' \
  auto_ban_prefix='ban' \
  auto_ban_violations_prefix='violations' \
  credit_min_amount='0.01' \
  credit_max_amount='1000000.0' \
  credit_precision='2' \
  credit_allow_negative='false' \
  max_metadata_size='1024' \
  max_reference_id_length='64' \
  allowed_transaction_types='purchase,reward,burn,transfer,refund' \
  transaction_window='3600' \
  require_transaction_id='true' \
  enforce_balance_validation='true' \
  max_payload_size='1048576' \
  max_nesting_depth='10' \
  max_array_size='1000' \
  max_string_length='65536' \
  encryption_salt='$(openssl rand -hex 16)' \
  mongodb_auth_source='admin' \
  mongodb_replica_set='' \
  mongodb_read_preference='primary' \
  mongodb_read_concern='majority' \
  mongodb_write_concern='majority' \
  mongodb_max_pool_size='100' \
  mongodb_min_pool_size='10' \
  mongodb_max_idle_time_ms='60000' \
  mongodb_socket_timeout_ms='5000' \
  mongodb_connect_timeout_ms='5000' \
  mongodb_ssl='false' \
  mongodb_ssl_ca_file='' \
  mongodb_ssl_cert_file='' \
  mongodb_ssl_key_file='' \
  mongodb_ssl_allow_invalid_certificates='false' \
  allowed_origins='http://localhost:5000,http://localhost:3000'" "Create Flask secrets"

# Initialize MongoDB secrets
log "SECRETS" "Initializing MongoDB secrets..."
log_cmd "vault kv put secret/app/mongodb \
  service_name='mongodb' \
  root_username='root' \
  root_password='$(openssl rand -hex 32)' \
  username='credit_system_user' \
  password='$(openssl rand -hex 32)' \
  db_name='credit_system' \
  host='mongodb' \
  port='27017' \
  database='admin' \
  auth_source='admin' \
  auth_mechanism='SCRAM-SHA-256' \
  tls='false' \
  retry_writes='true' \
  retry_reads='true' \
  max_pool_size='100' \
  min_pool_size='0'" "Create MongoDB secrets"

# Initialize Redis secrets
log "SECRETS" "Initializing Redis secrets..."
log_cmd "vault kv put secret/app/redis \
  service_name='redis' \
  host='redis' \
  port='6379' \
  db='0' \
  password='$(openssl rand -hex 32)' \
  ssl='false' \
  ssl_ca_certs='' \
  ssl_certfile='' \
  ssl_keyfile='' \
  ssl_cert_reqs='none' \
  ssl_check_hostname='false' \
  retry_on_timeout='true' \
  retry_on_error='true'" "Create Redis secrets"

log "SUCCESS" "✅ Vault secrets initialization completed successfully!"
log "SUMMARY" "The following secrets have been configured:"
log "SUMMARY" "  - Flask application secrets"
log "SUMMARY" "  - MongoDB secrets"
log "SUMMARY" "  - Redis secrets" 