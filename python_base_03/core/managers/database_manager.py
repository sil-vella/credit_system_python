from typing import Dict, Any, Optional
from core.managers.encryption_manager import EncryptionManager
from utils.config.config import config
from pymongo import MongoClient, ReadPreference
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from pymongo.errors import OperationFailure, ConnectionFailure
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, role: str = "read_write"):
        """Initialize database manager with specific role."""
        self.role = role
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.db = None
        self._setup_mongodb_connection()

    def _setup_mongodb_connection(self):
        """Set up MongoDB connection with role-based access control and read-only replicas."""
        try:
            # Get MongoDB URI from config
            mongodb_uri = config.MONGODB_URI

            # Set up connection options
            options = {
                'readPreference': 'primaryPreferred' if self.role == "read_only" else 'primary',
                'readConcernLevel': 'majority',
                'w': 'majority',
                'retryWrites': True,
                'retryReads': True
            }

            # Create MongoDB client
            self.client = MongoClient(mongodb_uri, **options)
            self.db = self.client[config.get_secret("secret/app/mongodb", "db_name", "credit_system")]

            # Verify connection and access
            self._verify_connection_and_access()

        except Exception as e:
            self.logger.error(f"❌ Failed to connect to MongoDB: {str(e)}")
            raise

    def _verify_connection_and_access(self):
        """Verify database connection and role-based access."""
        try:
            # Ping database
            self.client.admin.command('ping')
            self.logger.info("✅ Successfully connected to MongoDB")

            # Verify role-based access
            if self.role == "read_only":
                # Attempt a read operation
                self.db.list_collection_names()
                self.logger.info("✅ Read-only access verified")
            else:
                # Attempt a write operation to a test collection
                test_collection = self.db.get_collection('connection_test')
                test_collection.insert_one({'test': 'write_access'})
                test_collection.delete_one({'test': 'write_access'})
                self.logger.info("✅ Read-write access verified")

        except OperationFailure as e:
            self.logger.error(f"❌ Access verification failed: {str(e)}")
            raise
        except ConnectionFailure as e:
            self.logger.error(f"❌ Database connection failed: {str(e)}")
            raise

    def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert a single document into the specified collection."""
        if self.role != "read_write":
            raise PermissionError("Write operations not allowed for read-only role")
        
        try:
            result = self.db[collection].insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"Failed to insert document: {e}")
            raise

    def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document in the specified collection."""
        try:
            return self.db[collection].find_one(query)
        except Exception as e:
            self.logger.error(f"Failed to find document: {e}")
            raise

    def find_many(self, collection: str, query: Dict[str, Any]) -> list:
        """Find multiple documents in the specified collection."""
        try:
            return list(self.db[collection].find(query))
        except Exception as e:
            self.logger.error(f"Failed to find documents: {e}")
            raise

    def update_one(self, collection: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update a single document in the specified collection."""
        if self.role != "read_write":
            raise PermissionError("Write operations not allowed for read-only role")
        
        try:
            result = self.db[collection].update_one(query, update)
            return result.modified_count
        except Exception as e:
            self.logger.error(f"Failed to update document: {e}")
            raise

    def delete_one(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete a single document from the specified collection."""
        if self.role != "read_write":
            raise PermissionError("Write operations not allowed for read-only role")
        
        try:
            result = self.db[collection].delete_one(query)
            return result.deleted_count
        except Exception as e:
            self.logger.error(f"Failed to delete document: {e}")
            raise

    def _encrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in the data dictionary."""
        encrypted_data = data.copy()
        for field in config.SENSITIVE_FIELDS:
            if field in encrypted_data and encrypted_data[field] is not None:
                encrypted_data[field] = EncryptionManager().encrypt_field(
                    encrypted_data[field]
                )
        return encrypted_data

    def _decrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in the data dictionary."""
        decrypted_data = data.copy()
        for field in config.SENSITIVE_FIELDS:
            if field in decrypted_data and decrypted_data[field] is not None:
                decrypted_data[field] = EncryptionManager().decrypt_field(
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