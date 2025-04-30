import pytest
from datetime import datetime, timedelta
from ulid import ULID
from ..transaction_integrity import TransactionIntegrity
from .......utils.exceptions.validation_exceptions import ValidationError
from .......core.managers.redis_manager import RedisManager

class TestTransactionIntegrity:
    """Test cases for TransactionIntegrity class."""
    
    def setup_method(self):
        """Clean up Redis before each test."""
        redis_manager = RedisManager()
        # Clean up any existing transaction data
        redis_manager.delete(TransactionIntegrity.TRANSACTION_ID_PREFIX, "*")
        redis_manager.delete(TransactionIntegrity.TRANSACTION_HASH_PREFIX, "*")
    
    def test_generate_transaction_id(self):
        """Test generation of transaction IDs."""
        # Generate multiple IDs and verify they are unique
        ids = {TransactionIntegrity.generate_transaction_id() for _ in range(100)}
        assert len(ids) == 100  # All IDs should be unique
        
        # Verify IDs are valid ULIDs
        for transaction_id in ids:
            ULID.from_str(transaction_id)  # Should not raise an exception
    
    def test_calculate_transaction_hash(self):
        """Test calculation of transaction hashes."""
        # Test with same data produces same hash
        data1 = {
            "transaction_id": "01H9Z7X3V4M5N6P7Q8R9S0T1U2",
            "amount": 100,
            "from_user_id": "user1",
            "to_user_id": "user2"
        }
        data2 = {
            "transaction_id": "01H9Z7X3V4M5N6P7Q8R9S0T1U2",
            "amount": 100,
            "from_user_id": "user1",
            "to_user_id": "user2"
        }
        hash1 = TransactionIntegrity.calculate_transaction_hash(data1)
        hash2 = TransactionIntegrity.calculate_transaction_hash(data2)
        assert hash1 == hash2
        
        # Test with different data produces different hash
        data3 = {
            "transaction_id": "01H9Z7X3V4M5N6P7Q8R9S0T1U2",
            "amount": 200,  # Different amount
            "from_user_id": "user1",
            "to_user_id": "user2"
        }
        hash3 = TransactionIntegrity.calculate_transaction_hash(data3)
        assert hash3 != hash1
    
    def test_validate_transaction_idempotency(self):
        """Test validation of transaction idempotency."""
        transaction_id = TransactionIntegrity.generate_transaction_id()
        transaction_data = {
            "transaction_id": transaction_id,
            "amount": 100,
            "from_user_id": "user1",
            "to_user_id": "user2"
        }
        transaction_hash = TransactionIntegrity.calculate_transaction_hash(transaction_data)
        
        # First validation should pass
        TransactionIntegrity.validate_transaction_idempotency(transaction_id, transaction_hash)
        
        # Register the transaction
        TransactionIntegrity.register_transaction(transaction_id, transaction_hash)
        
        # Second validation should fail
        with pytest.raises(ValidationError) as exc_info:
            TransactionIntegrity.validate_transaction_idempotency(transaction_id, transaction_hash)
        assert "Transaction has already been processed" in str(exc_info.value)
    
    def test_validate_transaction_timestamp_valid(self):
        """Test validation of valid transaction timestamps."""
        # Test current timestamp
        current_time = datetime.utcnow().isoformat()
        TransactionIntegrity.validate_transaction_timestamp(current_time)
        
        # Test timestamp within window
        within_window = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
        TransactionIntegrity.validate_transaction_timestamp(within_window)
    
    def test_validate_transaction_timestamp_invalid(self):
        """Test validation of invalid transaction timestamps."""
        # Test timestamp too old
        too_old = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        with pytest.raises(ValidationError) as exc_info:
            TransactionIntegrity.validate_transaction_timestamp(too_old)
        assert "Transaction timestamp is too old" in str(exc_info.value)
        
        # Test future timestamp
        future = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        with pytest.raises(ValidationError) as exc_info:
            TransactionIntegrity.validate_transaction_timestamp(future)
        assert "Transaction timestamp is in the future" in str(exc_info.value)
        
        # Test invalid format
        with pytest.raises(ValidationError) as exc_info:
            TransactionIntegrity.validate_transaction_timestamp("invalid-timestamp")
        assert "Invalid timestamp format" in str(exc_info.value)
    
    def test_validate_transaction_integrity_valid(self):
        """Test validation of valid transaction integrity."""
        transaction_data = {
            "transaction_id": TransactionIntegrity.generate_transaction_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "amount": 100,
            "from_user_id": "user1",
            "to_user_id": "user2"
        }
        
        # First validation should pass
        TransactionIntegrity.validate_transaction_integrity(transaction_data)
        
        # Second validation with same data should fail
        with pytest.raises(ValidationError) as exc_info:
            TransactionIntegrity.validate_transaction_integrity(transaction_data)
        assert "Transaction has already been processed" in str(exc_info.value)
    
    def test_validate_transaction_integrity_invalid(self):
        """Test validation of invalid transaction integrity."""
        # Test missing required fields
        transaction_data = {
            "transaction_id": TransactionIntegrity.generate_transaction_id(),
            "timestamp": datetime.utcnow().isoformat()
        }
        with pytest.raises(ValidationError) as exc_info:
            TransactionIntegrity.validate_transaction_integrity(transaction_data)
        assert "Missing required fields" in str(exc_info.value)
        
        # Test invalid transaction ID format
        transaction_data = {
            "transaction_id": "invalid-id",
            "timestamp": datetime.utcnow().isoformat(),
            "amount": 100,
            "from_user_id": "user1",
            "to_user_id": "user2"
        }
        with pytest.raises(ValidationError) as exc_info:
            TransactionIntegrity.validate_transaction_integrity(transaction_data)
        assert "Invalid transaction ID format" in str(exc_info.value) 