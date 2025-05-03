# Kubernetes Initialization Service Documentation

## Overview
The `k8s-init` service is a critical initialization component that sets up a Kubernetes cluster using KinD (Kubernetes in Docker) for local development and testing. This service runs once during system startup and is responsible for creating and configuring the Kubernetes environment needed by other services.

## Service Configuration

### Base Image
```yaml
image: alpine:3.18
```
- Uses Alpine Linux for minimal footprint
- Version 3.18 chosen for stability and package availability

### Volume Mounts
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
  - ./kind-config.yaml:/workspace/kind-config.yaml:ro
  - ./scripts:/workspace/scripts:ro
  - ./tools/logger:/workspace/tools/logger
  - k8s-config:/k8s-config
```

| Mount Point | Purpose | Access | Security Considerations |
|-------------|---------|--------|------------------------|
| `/var/run/docker.sock` | Docker daemon access | RW | High-risk, needed for KinD |
| `/workspace/kind-config.yaml` | Cluster configuration | RO | Configuration only |
| `/workspace/scripts` | Initialization scripts | RO | Prevents tampering |
| `/workspace/tools/logger` | Log output | RW | Required for logging |
| `k8s-config` | Kubernetes configuration | RW | Named volume, isolated |

### Network Configuration
```yaml
networks:
  vault_internal:
    aliases:
      - k8s-init
  init_network: {}
```

#### Network Details
1. **vault_internal**:
   - Internal network for Vault communication
   - No internet access
   - Secure service communication
   - Uses alias for service discovery

2. **init_network**:
   - Temporary network for initialization
   - Internet access enabled
   - Used only during setup
   - Removed after completion

### Environment Variables
```yaml
environment:
  - VAULT_ADDR=http://vault:8200
  - KUBECONFIG=/k8s-config/kubeconfig
```

| Variable | Purpose | Default Value |
|----------|---------|---------------|
| `VAULT_ADDR` | HashiCorp Vault endpoint | `http://vault:8200` |
| `KUBECONFIG` | Kubernetes config location | `/k8s-config/kubeconfig` |

### Health Check Configuration
```yaml
healthcheck:
  test: ["CMD", "kubectl", "--kubeconfig", "/k8s-config/kubeconfig", "get", "pods", "-A"]
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 30s
```

- Verifies cluster functionality
- 30-second initial grace period
- Fails after 3 retries
- 5-second timeout per check
- Runs every 10 seconds

## Initialization Process

### 1. Script Preparation
```bash
TEMP_DIR=$(mktemp -d)
cp /workspace/scripts/k8s-init.sh $TEMP_DIR/
chmod +x $TEMP_DIR/k8s-init.sh
```
- Creates isolated temporary directory
- Copies initialization script
- Makes script executable
- Maintains read-only mount security

### 2. Tool Installation
The service automatically installs required tools:
- `docker-cli`: For container management
- `curl`: For downloads and health checks
- `kind`: For Kubernetes cluster creation
- `kubectl`: For cluster management

### 3. Cluster Cleanup
```bash
cleanup_clusters() {
    # Check and remove existing clusters
    if kind get clusters 2>/dev/null | grep -q "vault-auth"; then
        kind delete cluster --name vault-auth
    fi
}
```
- Ensures clean state
- Prevents conflicts
- Handles existing clusters

### 4. Cluster Creation
- Uses `kind-config.yaml` for configuration
- Creates single-node cluster
- Sets up control plane
- Configures networking

### 5. Verification
- Waits for cluster readiness
- Checks for running pods
- Verifies control plane health
- Ensures proper configuration

## Logging

### Log File Location
- Path: `/workspace/tools/logger/compose.log`
- Captures stdout and stderr
- Includes timestamps
- Color-coded messages

### Log Format
```
[YYYY-MM-DD HH:MM:SS] Message
```

### Message Types
- 📝 Information
- 🔒 Security operations
- ⏳ Progress indicators
- ✅ Success confirmations
- 🧹 Cleanup operations

## Security Considerations

### File System Security
- Read-only mounts where possible
- Temporary file execution
- Cleanup after execution
- Minimal write access

### Network Security
- Limited internet access
- Internal network isolation
- Temporary initialization network
- Secure service communication

### Runtime Security
- Single execution model
- No persistent container
- Automatic cleanup
- Limited privilege scope

## Dependencies

### Required Services
- Docker daemon
- Vault service (for configuration)

### Required Files
- `kind-config.yaml`
- `k8s-init.sh`
- Logger directory structure

## Troubleshooting

### Common Issues
1. **Docker Socket Access**
   - Symptom: Cannot create containers
   - Solution: Check Docker socket permissions

2. **Network Connectivity**
   - Symptom: Cannot download tools
   - Solution: Verify init_network configuration

3. **Cluster Creation Failures**
   - Symptom: KinD cluster fails to start
   - Solution: Check system resources and existing clusters

### Debug Commands
```bash
# Check cluster status
kind get clusters

# Verify network connectivity
curl -v http://vault:8200

# Check logs
tail -f /workspace/tools/logger/compose.log
```

## Best Practices

1. **Initialization**
   - Always use cleanup before creation
   - Verify tool installation
   - Check dependencies

2. **Security**
   - Maintain read-only access where possible
   - Use temporary directories
   - Clean up after execution

3. **Logging**
   - Use consistent format
   - Include timestamps
   - Provide clear status messages

## Related Documentation
- [KinD Configuration](https://kind.sigs.k8s.io/docs/user/configuration/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Compose Reference](https://docs.docker.com/compose/) 