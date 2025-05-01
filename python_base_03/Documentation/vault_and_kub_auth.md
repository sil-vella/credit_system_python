# HashiCorp Vault Integration with Docker Compose (Local Development)

This guide explains how to integrate HashiCorp Vault with your existing Docker Compose setup for secure secret management. This setup can be easily migrated to a VPS later.

## 📋 Implementation Status

### ✅ Core Infrastructure
- [x] Docker Compose integration
- [x] Vault service configuration
- [x] Multi-layer secret management
- [x] Health monitoring
- [x] Logging system

### ✅ Secret Management Implementation
- [x] VaultSecretsManager class
- [x] Multiple authentication methods
  - [x] Token-based authentication
  - [x] Kubernetes authentication (ready for k8s migration)
- [x] Fallback mechanisms
  - [x] Vault -> Docker Secrets -> Environment Variables

### ✅ Security Features
- [x] No hardcoded secrets
- [x] Secure secret retrieval chain
- [x] Error handling and logging
- [x] Health checks
- [x] Audit logging

### ✅ Code Integration
- [x] Configuration system (`config.py`)
- [x] Vault client integration (`vault_secrets.py`)
- [x] Health monitoring (`health.py`)
- [x] Dependencies management (hvac in requirements.txt)

### 🚧 Pending Enhancements (Optional)
- [ ] Secret rotation procedures
- [ ] Monitoring dashboards
- [ ] Automated tests
- [ ] Backup procedures
- [ ] Alert system for failed secret access

## 🔐 Current Architecture

### Secret Retrieval Chain:
```python
1. HashiCorp Vault (Primary)
   ↓ (if not available)
2. Docker Secrets (Secondary)
   ↓ (if not available)
3. Environment Variables (Fallback)
```

### Authentication Methods:
```python
1. Vault Token (from Docker secrets)
   ↓ (if not available)
2. Kubernetes Authentication
   ↓ (if not available)
3. Graceful failure with logging
```

## 📊 Monitoring and Health Checks

The system includes comprehensive health checks:

```python
{
    "vault": {
        "healthy": bool,  # Vault connection status
        "available": bool # Vault service availability
    },
    "docker_secrets": {
        "available": bool # Docker secrets availability
    },
    "overall": bool      # Overall system health
}
```

## 🔍 Logging System

Implemented comprehensive logging:
- Authentication attempts
- Secret access patterns
- Error tracking
- Security events

## 💾 Secret Storage Structure

```
secret/
├── app/
│   ├── mongodb/
│   │   ├── service_name
│   │   ├── root_username
│   │   ├── root_password
│   │   └── db_name
│   ├── redis/
│   │   ├── service_name
│   │   ├── host
│   │   ├── port
│   │   └── password
│   └── flask/
│       ├── service_name
│       ├── jwt_key
│       └── secret_key
```

## 🚀 Usage Example

```python
from utils.config import Config

# Secrets are automatically retrieved using the secure chain:
mongodb_user = Config.MONGODB_ROOT_USER  # Tries Vault -> Docker Secrets -> Env
redis_host = Config.REDIS_HOST          # Same secure retrieval chain
```

## 🔒 Security Best Practices Implemented

1. **Defense in Depth**
   - Multiple secret storage layers
   - Multiple authentication methods
   - Fallback mechanisms

2. **Zero Trust Architecture**
   - No default trust assumptions
   - Each secret request is authenticated
   - All access is logged

3. **Audit Trail**
   - Comprehensive logging
   - Access patterns tracking
   - Error tracking

4. **Health Monitoring**
   - Real-time health checks
   - Component availability monitoring
   - System status reporting

## 🔄 Migration Path

When ready to move to Kubernetes:
1. The Kubernetes authentication is already implemented
2. Vault configuration is container-ready
3. Secret structure is environment-agnostic

## ⚡ Next Steps

1. Implement secret rotation:
   ```bash
   # Example rotation schedule
   vault write secret/app/mongodb/root_password @new_password.json
   ```

2. Set up monitoring dashboards:
   - Secret access patterns
   - Authentication success/failure rates
   - System health metrics

3. Configure automated backups:
   ```bash
   vault operator raft snapshot save snapshot.gz
   ```

4. Implement alert system:
   - Failed authentication attempts
   - Failed secret retrievals
   - System health status changes

## 📋 Current Architecture

Your current stack includes:
- Flask Application
- MongoDB
- Redis
- Nginx (reverse proxy)
- Monitoring Stack:
  - Prometheus
  - Grafana
  - Alertmanager

## 🔐 Adding Vault Integration

### Step 1: Add Vault Service to docker-compose.yml

Add the following service to your existing docker-compose.yml:

```yaml
  vault:
    image: hashicorp/vault:1.15
    cap_add:
      - IPC_LOCK
    ports:
      - "8200:8200"
    environment:
      VAULT_ADDR: 'http://0.0.0.0:8200'
      VAULT_API_ADDR: 'http://0.0.0.0:8200'
      VAULT_LOCAL_CONFIG: |
        {
          "backend": {
            "file": {
              "path": "/vault/file"
            }
          },
          "default_lease_ttl": "168h",
          "max_lease_ttl": "720h",
          "listener": {
            "tcp": {
              "address": "0.0.0.0:8200",
              "tls_disable": 1
            }
          }
        }
    volumes:
      - vault-data:/vault/file
    networks:
      - cr_credit_system_network
    command: server
    restart: unless-stopped
```

### Step 2: Initialize Vault

After starting the services:

```bash
# Export Vault address
export VAULT_ADDR='http://127.0.0.1:8200'

# Initialize Vault
docker-compose exec vault vault operator init

# This will output 5 unseal keys and a root token
# SAVE THESE SECURELY
```

### Step 3: Move Current Secrets to Vault

Instead of using Docker secrets, we'll store them in Vault:

```bash
# Login to Vault
vault login <root-token>

# Enable KV secrets engine
vault secrets enable -path=secret kv-v2

# Store MongoDB secrets
vault kv put secret/mongodb \
  root_username="root" \
  root_password="rootpassword" \
  db_name="admin"

# Store Redis secrets
vault kv put secret/redis \
  password="your-redis-password" \
  host="redis" \
  port="6379"

# Store Flask secrets
vault kv put secret/flask \
  secret_key="your-secret-key" \
  jwt_key="your-jwt-key"
```

### Step 4: Update Flask Application

Add Vault integration to your Flask app:

```python
import hvac
import os

def get_vault_client():
    return hvac.Client(
        url='http://vault:8200',
        token=os.environ.get('VAULT_TOKEN')
    )

def get_secret(path, key):
    client = get_vault_client()
    try:
        secret = client.secrets.kv.v2.read_secret_version(path=path)
        return secret['data']['data'][key]
    except Exception as e:
        print(f"Error fetching secret: {e}")
        return None
```

### Step 5: Update Flask Service Configuration

Modify the Flask service in docker-compose.yml:

```yaml
  flask_app:
    # ... existing configuration ...
    environment:
      - VAULT_ADDR=http://vault:8200
      - VAULT_TOKEN=${VAULT_TOKEN}  # Set this via .env file
    depends_on:
      - vault
      - mongodb
      - redis
```

## 🔄 Migration Path to VPS

When ready to move to VPS:

1. **Export Vault Data**:
   ```bash
   docker-compose exec vault vault operator raft snapshot save snapshot.gz
   ```

2. **Transfer Configuration**:
   - Copy your docker-compose.yml
   - Transfer the Vault snapshot
   - Copy your application code

3. **On VPS**:
   ```bash
   # Start services
   docker-compose up -d

   # Restore Vault data
   docker-compose exec vault vault operator raft snapshot restore snapshot.gz
   ```

## 🔒 Security Considerations

1. **Development Mode**:
   - Current setup uses file backend for development
   - TLS is disabled for local testing

2. **Production Modifications Needed**:
   - Enable TLS
   - Use Consul or Raft storage backend
   - Implement proper access control policies
   - Enable audit logging

3. **Secret Rotation**:
   - Implement periodic secret rotation
   - Use Vault's dynamic secrets when possible
   - Set up proper lease TTLs

## 📊 Monitoring Integration

Your existing monitoring stack can be enhanced to monitor Vault:

1. **Prometheus Metrics**:
   - Add Vault metrics endpoint to prometheus.yml
   - Configure Vault telemetry

2. **Grafana Dashboard**:
   - Import Vault dashboard (ID: 12904)
   - Monitor seal status, token counts, and request rates

## ⚡ Next Steps

1. [ ] Implement secret rotation policies
2. [ ] Add Vault-specific monitoring
3. [ ] Set up backup procedures
4. [ ] Create development-specific Vault policies
5. [ ] Document secret management procedures

This setup provides a robust local development environment that can be easily migrated to a VPS while maintaining security best practices and your existing monitoring capabilities.

