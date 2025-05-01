// Switch to admin database first
db = db.getSiblingDB('admin');

// Create application user with proper roles
db.createUser({
    user: process.env.MONGODB_USER,
    pwd: process.env.MONGODB_PASSWORD,
    roles: [
        {
            role: "readWrite",
            db: process.env.MONGO_INITDB_DATABASE
        },
        {
            role: "dbAdmin",
            db: process.env.MONGO_INITDB_DATABASE
        }
    ]
});

// Switch to application database
db = db.getSiblingDB(process.env.MONGO_INITDB_DATABASE);

// Create collections and indexes
db.createCollection("users");
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "username": 1 });
db.users.createIndex({ "created_at": 1 });

db.createCollection("user_sessions");
db.user_sessions.createIndex({ "user_id": 1 });
db.user_sessions.createIndex({ "session_id": 1 }, { unique: true });
db.user_sessions.createIndex({ "created_at": 1 });

db.createCollection("user_tokens");
db.user_tokens.createIndex({ "user_id": 1 });
db.user_tokens.createIndex({ "access_token": 1 }, { unique: true });
db.user_tokens.createIndex({ "refresh_token": 1 }, { unique: true });
db.user_tokens.createIndex({ "expires_at": 1 });

db.createCollection("audit_logs");
db.audit_logs.createIndex({ "timestamp": 1 });
db.audit_logs.createIndex({ "user_id": 1 });
db.audit_logs.createIndex({ "action": 1 });

// Enable encryption at rest
db.adminCommand({
    setParameter: 1,
    "enableEncryption": true
}); 