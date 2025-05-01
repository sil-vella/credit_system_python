#!/bin/bash

# Wait for Vault to be ready
until curl -fs http://127.0.0.1:8200/v1/sys/health; do
    echo 'Waiting for Vault to be ready...'
    sleep 2
done

# Set environment variables
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='dev-token'

# Enable KV secrets engine
vault secrets enable -path=secret kv-v2

# Store MongoDB secrets
vault kv put secret/app/mongodb \
    service_name="mongodb" \
    root_username="root" \
    root_password="rootpassword" \
    db_name="credit_system"

# Store Redis secrets
vault kv put secret/app/redis \
    service_name="redis" \
    host="redis" \
    port="6379" \
    password="redis_password"

# Store Flask secrets
vault kv put secret/app/flask \
    service_name="flask" \
    jwt_key="dev_jwt_key" \
    secret_key="dev_secret_key"

echo "Vault has been configured with development secrets!" 