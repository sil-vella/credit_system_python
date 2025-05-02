#!/bin/sh

# Wait for Vault to be ready
until curl -fs http://vault:8200/v1/sys/health; do
  echo 'Waiting for Vault to be ready...'
  sleep 5
done

# Enable KV v2 secrets engine if not already enabled
vault secrets enable -path=secret kv-v2

# Initialize Flask secrets
vault kv put secret/app/flask \
  service_name="flask" \
  port="5000" \
  pythonpath="/app" \
  debug="true" \
  url="http://localhost:5000" \
  jwt_key="your-super-secret-key-change-in-production" \
  access_token_expires="3600" \
  refresh_token_expires="604800" \
  jwt_algorithm="HS256" \
  jwt_token_type="bearer" \
  jwt_header_name="Authorization" \
  jwt_header_type="Bearer" \
  jwt_query_string_name="token" \
  jwt_query_string_value_prefix="Bearer" \
  jwt_cookie_name="access_token" \
  jwt_cookie_csrf_protect="true" \
  jwt_cookie_secure="false" \
  jwt_cookie_samesite="Lax" \
  jwt_cookie_domain="" \
  jwt_cookie_path="/" \
  jwt_cookie_max_age="3600" \
  ssl="false" \
  min_conn="1" \
  max_conn="10" \
  connect_timeout="10" \
  statement_timeout="30000" \
  keepalive="1" \
  keepalive_idle="30" \
  keepalive_interval="10" \
  keepalive_count="5" \
  max_conn_per_user="5" \
  max_query_size="10000" \
  max_result_size="1048576" \
  retry_count="3" \
  retry_delay="1" \
  rate_limit_storage_url="redis://localhost:6379/0" \
  logging_enabled="true" \
  log_level="INFO" \
  log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s" \
  log_file="/var/log/flask/app.log" \
  redis_ssl="false" \
  redis_ssl_verify_mode="required" \
  redis_max_conn="10" \
  redis_socket_timeout="5" \
  redis_socket_connect_timeout="5" \
  redis_retry_on_timeout="true" \
  redis_max_retries="3" \
  redis_key_prefix="app" \
  redis_encryption_key="" \
  redis_encryption_salt="" \
  redis_encryption_iterations="100000" \
  redis_max_cache_size="1048576" \
  redis_cache_ttl="300" \
  rate_limit_enabled="true" \
  rate_limit_ip_requests="100" \
  rate_limit_ip_window="60" \
  rate_limit_ip_prefix="rate_limit:ip" \
  rate_limit_user_requests="1000" \
  rate_limit_user_window="3600" \
  rate_limit_user_prefix="rate_limit:user" \
  rate_limit_api_key_requests="10000" \
  rate_limit_api_key_window="3600" \
  rate_limit_api_key_prefix="rate_limit:api_key" \
  rate_limit_headers_enabled="true" \
  rate_limit_header_limit="X-RateLimit-Limit" \
  rate_limit_header_remaining="X-RateLimit-Remaining" \
  rate_limit_header_reset="X-RateLimit-Reset" \
  auto_ban_enabled="true" \
  auto_ban_violations_threshold="5" \
  auto_ban_duration="3600" \
  auto_ban_window="300" \
  auto_ban_prefix="ban" \
  auto_ban_violations_prefix="violations" \
  allowed_origins="http://localhost:5000,http://localhost:3000" \
  credit_min_amount="0.01" \
  credit_max_amount="1000000.0" \
  credit_precision="2" \
  credit_allow_negative="false" \
  max_metadata_size="1024" \
  max_reference_id_length="64" \
  allowed_transaction_types="purchase,reward,burn,transfer,refund" \
  transaction_window="3600" \
  require_transaction_id="true" \
  enforce_balance_validation="true" \
  max_payload_size="1048576" \
  max_nesting_depth="10" \
  max_array_size="1000" \
  max_string_length="65536" \
  encryption_salt="default_salt_123" \
  mongodb_uri="mongodb://localhost:27017/" \
  mongodb_auth_source="admin" \
  mongodb_replica_set="" \
  mongodb_read_preference="primary" \
  mongodb_read_concern="majority" \
  mongodb_write_concern="majority" \
  mongodb_max_pool_size="100" \
  mongodb_min_pool_size="10" \
  mongodb_max_idle_time_ms="60000" \
  mongodb_socket_timeout_ms="5000" \
  mongodb_connect_timeout_ms="5000" \
  mongodb_ssl="false" \
  mongodb_ssl_ca_file="" \
  mongodb_ssl_cert_file="" \
  mongodb_ssl_key_file="" \
  mongodb_ssl_allow_invalid_certificates="false"

# Initialize MongoDB secrets
vault kv put secret/app/mongodb \
  service_name="mongodb" \
  root_username="root" \
  root_password="rootpassword" \
  username="credit_system_user" \
  password="credit_system_password" \
  db_name="credit_system" \
  host="mongodb" \
  port="27017" \
  database="admin" \
  auth_source="admin" \
  auth_mechanism="SCRAM-SHA-256" \
  tls="false" \
  tls_ca_file="" \
  tls_certificate_key_file="" \
  tls_certificate_key_file_password="" \
  tls_allow_invalid_certificates="false" \
  tls_allow_invalid_hostnames="false" \
  tls_insecure="false" \
  tls_crl_file="" \
  retry_writes="true" \
  retry_reads="true" \
  max_pool_size="100" \
  min_pool_size="0" \
  max_idle_time_ms="0" \
  connect_timeout_ms="20000" \
  socket_timeout_ms="0" \
  server_selection_timeout_ms="30000" \
  wait_queue_timeout_ms="0" \
  heartbeat_frequency_ms="10000" \
  local_threshold_ms="15" \
  retry_on_failure="true" \
  retry_delay_ms="500" \
  retry_max_delay_ms="5000" \
  retry_jitter="true" \
  retry_reads_on_server_selection_error="true" \
  retry_writes_on_server_selection_error="true"

# Initialize Redis secrets
vault kv put secret/app/redis \
  service_name="redis" \
  host="redis" \
  port="6379" \
  db="0" \
  password="template_three_redis_password" \
  ssl="false" \
  ssl_ca_certs="" \
  ssl_certfile="" \
  ssl_keyfile="" \
  ssl_cert_reqs="none" \
  ssl_check_hostname="false" \
  ssl_ca_data="" \
  ssl_certificate_data="" \
  ssl_key_data="" \
  retry_on_timeout="true" \
  retry_on_error="true" \
  retry_on_connection_error="true" \
  retry_on_timeout_error="true" \
  retry_on_connection_failure="true" \
  retry_on_connection_loss="true" \
  retry_on_connection_reset="true" \
  retry_on_connection_refused="true" \
  retry_on_connection_aborted="true" \
  retry_on_connection_closed="true" \
  retry_on_connection_broken="true" \
  retry_on_connection_timeout="true" \
  retry_on_connection_error_max_attempts="3" \
  retry_on_connection_error_delay="1" \
  retry_on_connection_error_max_delay="5" \
  retry_on_connection_error_exponential_backoff="true" \
  retry_on_connection_error_jitter="true" \
  retry_on_connection_error_jitter_min="0.1" \
  retry_on_connection_error_jitter_max="0.3"

echo "✅ Vault secrets have been initialized" 