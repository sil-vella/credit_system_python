from typing import Dict, Optional
from datetime import datetime, timedelta
import hashlib
import json
from ulid import ULID
from ....utils.exceptions.validation_exceptions import ValidationError
from ....utils.config.config import Config
from ....core.managers.redis_manager import RedisManager

class TransactionIntegrity:
    """Class for ensuring transaction integrity and preventing replay attacks."""
    
    # Redis key prefixes
    TRANSACTION_ID_PREFIX = "tx:id:"
    TRANSACTION_HASH_PREFIX = "tx:hash:"
    
    # Maximum age of transaction hashes to keep (in seconds)
    TRANSACTION_WINDOW = 3600  # 1 hour
    
    @staticmethod
    def generate_transaction_id() -> str:
        """
        Generate a new ULID-based transaction ID.
        
        Returns:
            str: A new transaction ID
        """
        return str(ULID())
    
    @staticmethod
    def calculate_transaction_hash(transaction_data: Dict) -> str:
        """
        Calculate a hash for a transaction to prevent replay attacks.
        
        Args:
            transaction_data: The transaction data to hash
            
        Returns:
            str: The transaction hash
        """
        # Create a deterministic string representation of the transaction
        # Sort keys to ensure consistent ordering
        sorted_data = json.dumps(transaction_data, sort_keys=True)
        
        # Calculate SHA-256 hash
        return hashlib.sha256(sorted_data.encode()).hexdigest()
    
    @staticmethod
    def validate_transaction_idempotency(transaction_id: str, transaction_hash: str) -> None:
        """
        Validate that a transaction hasn't been processed before.
        
        Args:
            transaction_id: The transaction ID to check
            transaction_hash: The transaction hash to check
            
        Raises:
            ValidationError: If the transaction has been processed before
        """
        redis_manager = RedisManager()
        
        # Check if transaction ID exists in Redis
        if redis_manager.exists(TransactionIntegrity.TRANSACTION_ID_PREFIX, transaction_id):
            raise ValidationError("Transaction has already been processed")
            
        # Check if transaction hash exists in Redis
        if redis_manager.exists(TransactionIntegrity.TRANSACTION_HASH_PREFIX, transaction_hash):
            raise ValidationError("Transaction hash has been seen before (possible replay attack)")
    
    @staticmethod
    def register_transaction(transaction_id: str, transaction_hash: str) -> None:
        """
        Register a new transaction to prevent replay attacks.
        
        Args:
            transaction_id: The transaction ID to register
            transaction_hash: The transaction hash to register
        """
        redis_manager = RedisManager()
        
        # Store both the ID and hash with TTL
        redis_manager.set(
            TransactionIntegrity.TRANSACTION_ID_PREFIX,
            transaction_id,
            "1",
            expire=TransactionIntegrity.TRANSACTION_WINDOW
        )
        
        redis_manager.set(
            TransactionIntegrity.TRANSACTION_HASH_PREFIX,
            transaction_hash,
            "1",
            expire=TransactionIntegrity.TRANSACTION_WINDOW
        )
    
    @staticmethod
    def validate_transaction_timestamp(timestamp: str) -> None:
        """
        Validate that a transaction timestamp is within the allowed window.
        
        Args:
            timestamp: The transaction timestamp to validate
            
        Raises:
            ValidationError: If the timestamp is outside the allowed window
        """
        try:
            transaction_time = datetime.fromisoformat(timestamp)
            current_time = datetime.utcnow()
            
            # Check if transaction is too old
            if (current_time - transaction_time) > timedelta(seconds=TransactionIntegrity.TRANSACTION_WINDOW):
                raise ValidationError("Transaction timestamp is too old")
                
            # Check if transaction is from the future
            if transaction_time > current_time:
                raise ValidationError("Transaction timestamp is in the future")
                
        except ValueError:
            raise ValidationError("Invalid timestamp format")
    
    @staticmethod
    def validate_transaction_integrity(transaction_data: Dict) -> None:
        """
        Validate all aspects of transaction integrity.
        
        Args:
            transaction_data: The transaction data to validate
            
        Raises:
            ValidationError: If any integrity check fails
        """
        # Validate required fields
        required_fields = {'transaction_id', 'timestamp', 'amount', 'from_user_id', 'to_user_id'}
        missing_fields = required_fields - set(transaction_data.keys())
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Validate transaction ID format
        try:
            ULID.from_str(transaction_data['transaction_id'])
        except ValueError:
            raise ValidationError("Invalid transaction ID format")
        
        # Validate timestamp
        TransactionIntegrity.validate_transaction_timestamp(transaction_data['timestamp'])
        
        # Calculate and validate transaction hash
        transaction_hash = TransactionIntegrity.calculate_transaction_hash(transaction_data)
        TransactionIntegrity.validate_transaction_idempotency(
            transaction_data['transaction_id'],
            transaction_hash
        )
        
        # Register the transaction
        TransactionIntegrity.register_transaction(
            transaction_data['transaction_id'],
            transaction_hash
        ) 