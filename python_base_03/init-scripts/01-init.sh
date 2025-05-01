#!/bin/bash
set -e

# Read secrets from files
MONGO_INITDB_ROOT_USERNAME=$(cat /run/secrets/mongodb_root_user)
MONGO_INITDB_ROOT_PASSWORD=$(cat /run/secrets/mongodb_root_password)
MONGO_INITDB_DATABASE=$(cat /run/secrets/mongodb_db_name)
MONGODB_USER=$(cat /run/secrets/mongodb_user)
MONGODB_PASSWORD=$(cat /run/secrets/mongodb_user_password)
MONGODB_PORT=$(cat /run/secrets/mongodb_port)

# Wait for MongoDB to be ready
until mongosh --port $MONGODB_PORT --eval "db.adminCommand('ping')" > /dev/null 2>&1; do
  echo "Waiting for MongoDB to be ready..."
  sleep 1
done

# Initialize application database and users
mongosh admin --port $MONGODB_PORT -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" --eval "
  db = db.getSiblingDB('admin');
  
  // Create application user if it doesn't exist
  if (!db.getUser('$MONGODB_USER')) {
    db.createUser({
      user: '$MONGODB_USER',
      pwd: '$MONGODB_PASSWORD',
      roles: [
        { role: 'readWrite', db: '$MONGO_INITDB_DATABASE' },
        { role: 'readWrite', db: 'admin' }
      ]
    });
  }

  db = db.getSiblingDB('$MONGO_INITDB_DATABASE');
  
  // Create collections
  db.createCollection('users');
  db.createCollection('user_sessions');
  db.createCollection('user_tokens');
  db.createCollection('audit_logs');
  
  // Create indexes
  db.users.createIndex({ 'email': 1 }, { unique: true });
  db.users.createIndex({ 'username': 1 });
  db.users.createIndex({ 'created_at': 1 });
  
  db.user_sessions.createIndex({ 'user_id': 1 });
  db.user_sessions.createIndex({ 'session_id': 1 }, { unique: true });
  db.user_sessions.createIndex({ 'created_at': 1 });
  
  db.user_tokens.createIndex({ 'user_id': 1 });
  db.user_tokens.createIndex({ 'access_token': 1 }, { unique: true });
  db.user_tokens.createIndex({ 'refresh_token': 1 }, { unique: true });
  db.user_tokens.createIndex({ 'expires_at': 1 });
  
  db.audit_logs.createIndex({ 'timestamp': 1 });
  db.audit_logs.createIndex({ 'user_id': 1 });
  db.audit_logs.createIndex({ 'action': 1 });
" 