# Docker Services Documentation

This document provides a detailed overview of all services defined in our `docker-compose.yml` file and their roles in the credit system architecture.

## System Architecture Overview

Our system utilizes a microservices architecture with the following key components:
- Web Application Layer (Flask + Nginx)
- Data Layer (MongoDB + Redis)
- Security Layer (Vault)
- Monitoring Stack (Prometheus, Grafana, Alertmanager)
- Kubernetes Integration (Kind)

## Service Details

### 1. Kubernetes Initialization (k8s-init)
**Purpose**: Local Kubernetes cluster setup and configuration
- Uses `alpine:3.18` as base image
- Sets up Kind (Kubernetes in Docker) for local development
- Installs required tools: docker-cli, curl, kind, kubectl
- Creates and configures the cluster using `kind-config.yaml`
- Waits for cluster readiness before completing

### 2. Secret Management Services

#### 2.1 Vault
**Purpose**: Central secrets management system
- Image: `hashicorp/vault:1.15`
- Runs in development mode
- Exposes port 8200
- Manages sensitive information:
  - Database credentials
  - API keys
  - Service configurations
  - Encryption keys
  - Application secrets

#### 2.2 Vault Config
**Purpose**: Vault initialization and configuration
- Configures initial secrets
- Sets up authentication
- Manages secret distribution
- Initializes security policies
- Security features:
  - One-time execution (restart: "no")
  - Temporary script execution permissions
  - Automatic permission revocation after initialization
  - Scripts retained for audit/debugging
  - Clear security state logging

### 3. Application Services

#### 3.1 Flask Application (flask_app)
**Purpose**: Main application service
- Custom built image: `silvella/cr_credit_system_flask_app`
- Runs on Gunicorn with gevent worker
- Exposed on port 5000
- Key features:
  - Integrates with MongoDB and Redis
  - Uses Vault for secrets
  - Mounts multiple application directories:
    - /plugins
    - /core
    - /static
    - /tools
    - /utils

#### 3.2 Nginx
**Purpose**: Web server and reverse proxy
- Routes traffic to Flask application
- Load balancing capabilities
- Static file serving
- Exposed on port 8080

### 4. Data Services

#### 4.1 MongoDB
**Purpose**: Primary database
- Latest MongoDB version
- Persistent data storage
- Secured with root authentication
- Exposed on port 27017
- Health checks enabled
- Used for:
  - User data
  - Transaction records
  - System configurations

#### 4.2 Redis
**Purpose**: In-memory cache/database
- Alpine-based Redis image
- Password protected
- Exposed on port 6379
- Used for:
  - Session management
  - Caching
  - Temporary data storage
  - Rate limiting

### 5. Monitoring Stack

#### 5.1 Prometheus
**Purpose**: Metrics collection and monitoring
- Collects metrics from all services
- Stores time-series data
- Exposed on port 9090
- Configured via `prometheus.yml`

#### 5.2 Grafana
**Purpose**: Monitoring visualization
- Latest Grafana version
- Exposed on port 3000
- Features:
  - Custom dashboards
  - Metric visualization
  - Alert visualization
  - Data source integration

#### 5.3 Alertmanager
**Purpose**: Alert handling and notification
- Manages alert notifications
- Handles alert routing
- Exposed on port 9093
- Configured via `alertmanager.yml`

## Network Configuration

All services are connected through the `cr_credit_system_network` bridge network, ensuring:
- Service isolation
- Secure inter-service communication
- Network policy enforcement

## Persistent Storage

The system uses named volumes for persistent data:
- `cr_credit_system_mongodb_data`: MongoDB data
- `cr_credit_system_redis_data`: Redis data
- `prometheus_data`: Monitoring metrics
- `grafana_data`: Dashboard configurations
- `alertmanager_data`: Alert configurations
- `k8s-config`: Kubernetes configurations
- `vault-data`: Secrets storage

## Security Considerations

1. **Secret Management**
   - All sensitive data managed by Vault
   - No hardcoded credentials
   - Secure secret distribution
   - Initialization scripts with temporary execution rights
   - Automated security controls for initialization process

2. **Service Security**
   - Password-protected Redis
   - MongoDB authentication
   - Grafana admin password protection
   - Vault token authentication

3. **Network Security**
   - Isolated network
   - Controlled service exposure
   - Internal service discovery

## Health Monitoring

All critical services include health checks:
- MongoDB: Database connectivity
- Redis: Service responsiveness
- Flask: Application availability
- Prometheus: Metrics collection
- Grafana: Dashboard accessibility
- Alertmanager: Alert system status

## Development Workflow

1. Start the stack:
```bash
docker-compose up -d
```

2. Access services:
- Application: http://localhost:8080
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093
- Vault: http://localhost:8200

3. Monitor logs:
```bash
docker-compose logs -f [service_name]
```

## Troubleshooting

Common issues and solutions:

1. **Service Dependencies**
   - Services are configured with appropriate `depends_on` conditions
   - Health checks ensure service readiness
   - Retry mechanisms implemented for critical services

2. **Volume Management**
   - All data persisted in named volumes
   - Volume backup recommended
   - Clear volume naming convention

3. **Network Issues**
   - Check network connectivity
   - Verify service discovery
   - Confirm port mappings

## Maintenance

Regular maintenance tasks:

1. **Updates**
   - Keep base images updated
   - Review security patches
   - Update configurations as needed

2. **Monitoring**
   - Review Grafana dashboards
   - Check alert configurations
   - Monitor resource usage

3. **Backup**
   - Regular database backups
   - Configuration backups
   - Volume backups 