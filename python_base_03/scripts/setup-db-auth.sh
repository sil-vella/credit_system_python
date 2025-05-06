#!/bin/bash

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to read secret from file
read_secret() {
    local secret_file=$1
    if [ -f "$secret_file" ]; then
        cat "$secret_file"
    else
        echo ""
    fi
}

# Wait for MongoDB to be ready
wait_for_mongodb() {
    log "Waiting for MongoDB to be ready..."
    until mongosh --host mongodb --quiet --eval "db.runCommand('ping').ok" > /dev/null 2>&1; do
        log "MongoDB not ready, retrying in 5 seconds..."
        sleep 5
    done
    log "MongoDB is ready"
}

# Wait for Redis to be ready
wait_for_redis() {
    log "Waiting for Redis to be ready..."
    until redis-cli -h redis ping > /dev/null 2>&1; do
        log "Redis not ready, retrying in 5 seconds..."
        sleep 5
    done
    log "Redis is ready"
}

# Setup MongoDB authentication
setup_mongodb_auth() {
    log "Setting up MongoDB authentication..."
    
    # Read credentials from secret files
    MONGODB_ROOT_USER=$(read_secret "/run/secrets/mongodb_root_user")
    MONGODB_ROOT_PASSWORD=$(read_secret "/run/secrets/mongodb_root_password")
    MONGODB_DB_NAME="credit_system"
    
    if [ -z "$MONGODB_ROOT_USER" ] || [ -z "$MONGODB_ROOT_PASSWORD" ]; then
        log "Error: MongoDB credentials not found in secret files"
        return 1
    }
    
    # Create root user if it doesn't exist
    log "Creating root user..."
    mongosh --host mongodb --quiet --eval "
        use admin;
        db.createUser({
            user: '$MONGODB_ROOT_USER',
            pwd: '$MONGODB_ROOT_PASSWORD',
            roles: ['root']
        });
    " || log "Root user might already exist"
    
    # Verify root user can authenticate
    log "Verifying root user authentication..."
    if ! mongosh --host mongodb --quiet --authenticationDatabase "admin" -u "$MONGODB_ROOT_USER" -p "$MONGODB_ROOT_PASSWORD" --eval "db.runCommand('ping')" > /dev/null 2>&1; then
        log "Error: Failed to authenticate as root user"
        return 1
    }
    log "Root user authentication successful"
    
    # Create application database and user
    log "Creating application database and user..."
    mongosh --host mongodb --quiet --authenticationDatabase "admin" -u "$MONGODB_ROOT_USER" -p "$MONGODB_ROOT_PASSWORD" --eval "
        use $MONGODB_DB_NAME;
        db.createUser({
            user: '$MONGODB_ROOT_USER',
            pwd: '$MONGODB_ROOT_PASSWORD',
            roles: ['readWrite', 'dbAdmin']
        });
    " || log "Database user might already exist"
    
    # Verify application user can authenticate
    log "Verifying application user authentication..."
    if ! mongosh --host mongodb --quiet --authenticationDatabase "admin" -u "$MONGODB_ROOT_USER" -p "$MONGODB_ROOT_PASSWORD" --eval "use $MONGODB_DB_NAME; db.runCommand('ping')" > /dev/null 2>&1; then
        log "Error: Failed to authenticate as application user"
        return 1
    }
    log "Application user authentication successful"
    
    log "MongoDB authentication setup completed successfully"
}

# Setup Redis authentication
setup_redis_auth() {
    log "Setting up Redis authentication..."
    
    # Read Redis password from secret file
    REDIS_PASSWORD=$(read_secret "/run/secrets/redis_password")
    
    if [ -z "$REDIS_PASSWORD" ]; then
        log "Error: Redis password not found in secret file"
        return 1
    }
    
    # Set Redis password
    log "Setting Redis password..."
    if ! redis-cli -h redis CONFIG SET requirepass "$REDIS_PASSWORD"; then
        log "Error: Failed to set Redis password"
        return 1
    }
    
    # Verify Redis authentication
    log "Verifying Redis authentication..."
    if ! redis-cli -h redis -a "$REDIS_PASSWORD" PING > /dev/null 2>&1; then
        log "Error: Failed to authenticate with Redis"
        return 1
    }
    log "Redis authentication successful"
    
    log "Redis authentication setup completed successfully"
}

# Main execution
main() {
    log "Starting database authentication setup..."
    
    # Wait for services to be ready
    wait_for_mongodb || exit 1
    wait_for_redis || exit 1
    
    # Setup authentication
    setup_mongodb_auth || exit 1
    setup_redis_auth || exit 1
    
    log "Database authentication setup completed successfully"
}

# Execute main function
main 