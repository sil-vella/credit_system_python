# Docker Network Security Configuration

This document outlines the network security configurations and best practices implemented in our credit system architecture.

## Network Architecture Overview

Our system uses three distinct networks with specific security configurations:

1. **vault_internal** (Highly Secured Internal Network)
   ```yaml
   networks:
     vault_internal:
       driver: bridge
       internal: true
       driver_opts:
         com.docker.network.bridge.enable_icc: "true"  # Allow specific inter-container communication
         com.docker.network.bridge.enable_ip_masquerade: "false"  # Disable outbound NAT
       ipam:
         config:
           - subnet: "172.28.0.0/16"
   ```

2. **vault_setup** (Temporary Setup Network)
   ```yaml
   networks:
     vault_setup:
       driver: bridge
       internal: false  # Needs internet access for setup
       driver_opts:
         com.docker.network.bridge.enable_ip_masquerade: "true"  # Enable NAT for internet access
   ```

3. **cr_credit_system_network** (Main Application Network)
   ```yaml
   networks:
     cr_credit_system_network:
       driver: bridge
       internal: false
       driver_opts:
         com.docker.network.bridge.enable_icc: "true"
         com.docker.network.driver.mtu: "1450"
   ```

## Multi-Layer Security Approach

### 1. Container Level Security

#### Flask Application Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/api/endpoint")
@limiter.limit("1 per second")  # Endpoint-specific limits
def api_endpoint():
    return "Protected endpoint"
```

#### Container Resource Limits
```yaml
flask_app:
  security_opt:
    - no-new-privileges:true
  ulimits:
    nproc: 65535
    nofile:
      soft: 20000
      hard: 40000
```

### 2. Service Level Security

#### Nginx Rate Limiting
```nginx
http {
    # Define rate limiting zones
    limit_req_zone $binary_remote_addr zone=one:10m rate=1r/s;
    limit_conn_zone $binary_remote_addr zone=addr:10m;

    server {
        location /api/ {
            # Apply rate limiting
            limit_req zone=one burst=5 nodelay;
            limit_conn addr 10;
            
            # Additional security headers
            add_header X-Frame-Options "SAMEORIGIN";
            add_header X-XSS-Protection "1; mode=block";
            add_header X-Content-Type-Options "nosniff";
        }
    }
}
```

#### Redis Security Configuration
```yaml
redis:
  command: redis-server --maxclients 10000 --tcp-backlog 128
  # Additional security options
  security_opt:
    - no-new-privileges:true
```

### 3. Network Level Security

#### Docker Network Features
- Network isolation between containers
- Controlled inter-container communication
- Subnet management and IP allocation
- Traffic encryption (when using overlay networks)

#### Network Options
- `internal: true` - Prevents external network access
- `enable_ip_masquerade: false` - Disables outbound NAT
- `enable_icc: false` - Disables inter-container communication

### 4. Host Level Security

#### IPTables Rate Limiting
```bash
# Rate limit incoming connections
iptables -A INPUT -p tcp --dport 80 -m state --state NEW -m recent --set
iptables -A INPUT -p tcp --dport 80 -m state --state NEW -m recent \
         --update --seconds 60 --hitcount 10 -j DROP
```

#### Fail2ban Configuration
```ini
[nginx-http-auth]
enabled  = true
filter   = nginx-http-auth
port     = http,https
logpath  = /var/log/nginx/error.log
maxretry = 3
bantime  = 600
```

## External Communication Flow

All external communication follows this path:
1. Container Network Interface
2. Docker Network (with applied security rules)
3. Host's Network Stack (with iptables rules)
4. External Network

## Best Practices Implementation

1. **Network Segmentation**
   - Use separate networks for different concerns
   - Implement least privilege principle
   - Control inter-network communication

2. **Rate Limiting Strategy**
   - Application-level rate limiting
   - Service-level connection limits
   - Network-level traffic control
   - Host-level protection

3. **Security Monitoring**
   - Log all network activities
   - Monitor connection attempts
   - Track resource usage
   - Alert on suspicious patterns

4. **Additional Security Measures**
   - Web Application Firewall (WAF)
   - Docker's seccomp profiles
   - Regular security audits
   - Network policy enforcement

## Maintenance and Monitoring

1. **Regular Tasks**
   - Monitor network traffic patterns
   - Review security logs
   - Update security rules
   - Audit network configurations

2. **Security Updates**
   - Keep all components updated
   - Review security patches
   - Test security configurations
   - Update rate limiting rules

## Troubleshooting

1. **Common Issues**
   - Rate limiting too aggressive
   - Network connectivity issues
   - Container communication problems
   - Resource exhaustion

2. **Debugging Steps**
   - Check container logs
   - Review network configurations
   - Verify security rules
   - Test connectivity between services

## References

- [Docker Network Documentation](https://docs.docker.com/network/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Nginx Rate Limiting](https://www.nginx.com/blog/rate-limiting-nginx/)
- [Flask Rate Limiting](https://flask-limiter.readthedocs.io/) 