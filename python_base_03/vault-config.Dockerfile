FROM hashicorp/vault:1.15

# Install required packages
RUN apk add --no-cache \
    curl \
    bash \
    openssl

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/v1.29.2/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/

# Create directory for scripts
RUN mkdir -p /app/scripts

# Copy scripts into the image
COPY scripts/setup-k8s-auth.sh /app/scripts/
COPY scripts/init-vault-secrets.sh /app/scripts/

# Make scripts executable
RUN chmod +x /app/scripts/*.sh

# Set working directory
WORKDIR /app

# Create directory for logs
RUN mkdir -p /workspace/tools/logger

# Default command that will be overridden by docker-compose
CMD ["sh", "-c", "echo 'Vault config container started'"] 