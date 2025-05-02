#!/bin/sh

set -e  # Exit on any error

echo "Starting Vault Kubernetes authentication setup..."

# Wait for Vault to be ready
until curl -fs http://vault:8200/v1/sys/health; do
    echo 'Waiting for Vault to be ready...'
    sleep 5
done

echo "Vault is ready. Configuring Kubernetes authentication..."

# Enable Kubernetes auth method if not already enabled
vault auth enable kubernetes || echo "Kubernetes auth already enabled"

# Get the Kubernetes host
KUBE_HOST="https://kubernetes.default.svc"

# Get the Kubernetes CA certificate
echo "Retrieving Kubernetes CA certificate..."
KUBE_CA_CERT=$(kubectl config view --raw --minify --flatten \
    -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' | base64 --decode)

if [ -z "$KUBE_CA_CERT" ]; then
    echo "Error: Failed to retrieve Kubernetes CA certificate"
    exit 1
fi

# Create service account if it doesn't exist
echo "Creating Kubernetes service account..."
kubectl apply -f k8s/flask-auth-sa.yaml

# Get the service account token
echo "Generating service account token..."
SA_TOKEN=$(kubectl create token flask-auth)

if [ -z "$SA_TOKEN" ]; then
    echo "Error: Failed to generate service account token"
    exit 1
fi

# Configure Kubernetes auth method
echo "Configuring Vault Kubernetes authentication..."
vault write auth/kubernetes/config \
    kubernetes_host="$KUBE_HOST" \
    kubernetes_ca_cert="$KUBE_CA_CERT" \
    token_reviewer_jwt="$SA_TOKEN"

# Create a policy for Flask app
echo "Creating Vault policy for Flask application..."
vault policy write flask-policy - <<EOF
# Allow Flask app to read secrets
path "secret/data/app/*" {
    capabilities = ["read"]
}

# Allow Flask app to read its own configuration
path "secret/data/flask/*" {
    capabilities = ["read"]
}

# Deny all other paths
path "*" {
    capabilities = ["deny"]
}
EOF

# Create a Kubernetes auth role
echo "Creating Kubernetes authentication role..."
vault write auth/kubernetes/role/flask-auth \
    bound_service_account_names=flask-auth \
    bound_service_account_namespaces=default \
    policies=flask-policy \
    ttl=24h

echo "✅ Vault Kubernetes authentication setup completed successfully!"
echo "The following components have been configured:"
echo "  - Kubernetes authentication method enabled"
echo "  - Service account created: flask-auth"
echo "  - Vault policy created: flask-policy"
echo "  - Kubernetes auth role created: flask-auth" 