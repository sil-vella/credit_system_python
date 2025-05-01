#!/bin/sh

# Wait for Vault to be ready
until curl -fs http://vault:8200/v1/sys/health; do
  echo 'Waiting for Vault to be ready...'
  sleep 5
done

# Enable Kubernetes auth method
vault auth enable kubernetes

# Get the Kubernetes host
KUBE_HOST="https://kubernetes.default.svc"

# Get the Kubernetes CA certificate
KUBE_CA_CERT=$(kubectl config view --raw --minify --flatten -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' | base64 --decode)

# Get the service account token
SA_TOKEN=$(kubectl create token vault-auth)

# Configure Kubernetes auth method
vault write auth/kubernetes/config \
  kubernetes_host="$KUBE_HOST" \
  kubernetes_ca_cert="$KUBE_CA_CERT" \
  token_reviewer_jwt="$SA_TOKEN"

# Create a policy for Flask app
vault policy write flask-policy - <<EOF
path "secret/data/app/*" {
  capabilities = ["read"]
}
EOF

# Create a Kubernetes auth role
vault write auth/kubernetes/role/flask-auth \
  bound_service_account_names=flask-auth \
  bound_service_account_namespaces=default \
  policies=flask-policy \
  ttl=24h 