from typing import Dict, Any, Optional
from core.managers.encryption_manager import EncryptionManager
from utils.config.config import SENSITIVE_FIELDS, Config
from pymongo import MongoClient, ReadPreference, WriteConcern, ReadConcern
from pymongo.errors import OperationFailure, ConnectionFailure
import logging

class DatabaseManager:
    def __init__(self, role: str = "read_write"):
        """Initialize the database manager with role-based access control."""
        self.encryption_manager = EncryptionManager()
        self.encryption_manager.initialize()
        self.role = role
        self.logger = logging.getLogger(__name__)
        self._setup_mongodb_connection()

    def _setup_mongodb_connection(self):
        """Set up MongoDB connection with role-based access control and read-only replicas."""
        try:
            # Build connection options
            options = {
                "maxPoolSize": Config.MONGODB_MAX_POOL_SIZE,
                "minPoolSize": Config.MONGODB_MIN_POOL_SIZE,
                "maxIdleTimeMS": Config.MONGODB_MAX_IDLE_TIME_MS,
                "socketTimeoutMS": Config.MONGODB_SOCKET_TIMEOUT_MS,
                "connectTimeoutMS": Config.MONGODB_CONNECT_TIMEOUT_MS,
            }

            # Add authentication if credentials are provided
            if Config.MONGODB_USERNAME and Config.MONGODB_PASSWORD:
                options.update({
                    "username": Config.MONGODB_USERNAME,
                    "password": Config.MONGODB_PASSWORD,
                    "authSource": Config.MONGODB_AUTH_SOURCE
                })

            # Add SSL/TLS settings if enabled
            if Config.MONGODB_SSL:
                ssl_options = {
                    "ssl": True,
                    "ssl_cert_reqs": "CERT_REQUIRED" if not Config.MONGODB_SSL_ALLOW_INVALID_CERTIFICATES else "CERT_NONE"
                }
                if Config.MONGODB_SSL_CA_FILE:
                    ssl_options["ssl_ca_certs"] = Config.MONGODB_SSL_CA_FILE
                if Config.MONGODB_SSL_CERT_FILE and Config.MONGODB_SSL_KEY_FILE:
                    ssl_options["ssl_certfile"] = Config.MONGODB_SSL_CERT_FILE
                    ssl_options["ssl_keyfile"] = Config.MONGODB_SSL_KEY_FILE
                options.update(ssl_options)

            # Add replica set configuration if specified
            if Config.MONGODB_REPLICA_SET:
                options["replicaSet"] = Config.MONGODB_REPLICA_SET

            # Initialize MongoDB client
            self.client = MongoClient(Config.MONGODB_URI, **options)
            
            # Set up read preference based on role
            if self.role == "read_only":
                self.client.read_preference = ReadPreference.SECONDARY_PREFERRED
            else:
                self.client.read_preference = ReadPreference.PRIMARY

            # Set up write concern and read concern
            self.client.write_concern = WriteConcern(w=Config.MONGODB_WRITE_CONCERN)
            self.client.read_concern = ReadConcern(level=Config.MONGODB_READ_CONCERN)

            # Get database with proper role-based access
            self.db = self.client[Config.MONGODB_DB_NAME]

            # Verify connection and role-based access
            self._verify_connection_and_access()

            self.logger.info(f"✅ MongoDB connection established with role: {self.role}")

        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise

    def _verify_connection_and_access(self):
        """Verify MongoDB connection and role-based access permissions."""
        try:
            # Test basic connection
            self.client.server_info()

            # Test role-based access
            if self.role == "read_only":
                # Verify read access
                self.db.command("listCollections")
            else:
                # Verify write access
                test_collection = self.db["_test_access"]
                test_collection.insert_one({"test": "access"})
                test_collection.delete_one({"test": "access"})

        except OperationFailure as e:
            self.logger.error(f"❌ Role-based access verification failed: {e}")
            raise

    def _encrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in the data dictionary."""
        encrypted_data = data.copy()
        for field in SENSITIVE_FIELDS:
            if field in encrypted_data and encrypted_data[field] is not None:
                encrypted_data[field] = self.encryption_manager.encrypt_field(
                    encrypted_data[field]
                )
        return encrypted_data

    def _decrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in the data dictionary."""
        decrypted_data = data.copy()
        for field in SENSITIVE_FIELDS:
            if field in decrypted_data and decrypted_data[field] is not None:
                decrypted_data[field] = self.encryption_manager.decrypt_field(
                    decrypted_data[field]
                )
        return decrypted_data

    def insert(self, collection: str, data: Dict[str, Any]) -> str:
        """Insert a document into the specified collection with encrypted sensitive fields."""
        if self.role == "read_only":
            raise OperationFailure("Write operations not allowed with read-only role")
        
        encrypted_data = self._encrypt_sensitive_fields(data)
        result = self.db[collection].insert_one(encrypted_data)
        return str(result.inserted_id)

    def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one document in the specified collection and decrypt sensitive fields."""
        result = self.db[collection].find_one(query)
        if result:
            return self._decrypt_sensitive_fields(result)
        return None

    def find(self, collection: str, query: Dict[str, Any]) -> list:
        """Find documents in the specified collection and decrypt sensitive fields."""
        results = list(self.db[collection].find(query))
        return [self._decrypt_sensitive_fields(doc) for doc in results]

    def update(self, collection: str, query: Dict[str, Any], data: Dict[str, Any]) -> int:
        """Update documents in the specified collection with encrypted sensitive fields."""
        if self.role == "read_only":
            raise OperationFailure("Write operations not allowed with read-only role")
        
        encrypted_data = self._encrypt_sensitive_fields(data)
        result = self.db[collection].update_many(query, {'$set': encrypted_data})
        return result.modified_count

    def delete(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete documents from the specified collection."""
        if self.role == "read_only":
            raise OperationFailure("Write operations not allowed with read-only role")
        
        result = self.db[collection].delete_many(query)
        return result.deleted_count

    def close(self):
        """Close the database connection."""
        if hasattr(self, 'client'):
            self.client.close()
            self.logger.info("✅ MongoDB connection closed")

# ... existing code ... 