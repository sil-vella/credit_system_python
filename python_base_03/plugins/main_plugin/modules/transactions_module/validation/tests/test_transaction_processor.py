import pytest
import json
from datetime import datetime
from ..transaction_processor import TransactionProcessor
from .......utils.exceptions.validation_exceptions import ValidationError
from .......utils.config.config import Config

class TestTransactionProcessor:
    """Test cases for TransactionProcessor class."""
    
    def test_validate_transaction_payload_valid(self):
        """Test validation of valid transaction payloads."""
        # Test minimal valid payload
        payload = json.dumps({
            "from_user_id": "user1",
            "to_user_id": "user2",
            "amount": 10.5,
            "transaction_type": "transfer"
        })
        result = TransactionProcessor.validate_transaction_payload(payload)
        assert result["from_user_id"] == "user1"
        assert result["to_user_id"] == "user2"
        assert result["amount"] == 10.5
        assert result["transaction_type"] == "transfer"
        
        # Test payload with optional fields
        payload = json.dumps({
            "from_user_id": "user1",
            "to_user_id": "user2",
            "amount": 10.5,
            "transaction_type": "transfer",
            "metadata": {"description": "test"},
            "reference_id": "ref_123"
        })
        result = TransactionProcessor.validate_transaction_payload(payload)
        assert result["metadata"] == {"description": "test"}
        assert result["reference_id"] == "ref_123"
    
    def test_validate_transaction_payload_invalid(self):
        """Test validation of invalid transaction payloads."""
        # Test missing required field
        payload = json.dumps({
            "from_user_id": "user1",
            "to_user_id": "user2",
            "amount": 10.5
        })
        with pytest.raises(ValidationError) as exc_info:
            TransactionProcessor.validate_transaction_payload(payload)
        assert "Missing required field" in str(exc_info.value)
        
        # Test oversized payload
        large_payload = json.dumps({
            "from_user_id": "user1",
            "to_user_id": "user2",
            "amount": 10.5,
            "transaction_type": "transfer",
            "data": "x" * (Config.MAX_PAYLOAD_SIZE + 1)
        })
        with pytest.raises(ValidationError) as exc_info:
            TransactionProcessor.validate_transaction_payload(large_payload)
        assert "Payload too large" in str(exc_info.value)
        
        # Test malformed JSON
        with pytest.raises(ValidationError) as exc_info:
            TransactionProcessor.validate_transaction_payload('{"invalid": json}')
        assert "Invalid JSON format" in str(exc_info.value)
    
    def test_process_transaction_valid(self):
        """Test processing of valid transactions."""
        # Test basic transaction
        payload = json.dumps({
            "from_user_id": "user1",
            "to_user_id": "user2",
            "amount": 10.5,
            "transaction_type": "transfer"
        })
        result = TransactionProcessor.process_transaction(payload)
        assert result["from_user_id"] == "user1"
        assert result["to_user_id"] == "user2"
        assert result["amount"] == 10.5
        assert result["transaction_type"] == "transfer"
        assert "timestamp" in result
        
        # Test transaction with all fields
        payload = json.dumps({
            "from_user_id": "user1",
            "to_user_id": "user2",
            "amount": 10.5,
            "transaction_type": "transfer",
            "metadata": {"description": "test"},
            "reference_id": "ref_123",
            "timestamp": "2023-01-01T00:00:00"
        })
        result = TransactionProcessor.process_transaction(payload)
        assert result["metadata"] == {"description": "test"}
        assert result["reference_id"] == "ref_123"
        assert result["timestamp"] == "2023-01-01T00:00:00"
    
    def test_process_transaction_invalid(self):
        """Test processing of invalid transactions."""
        # Test invalid transaction type
        payload = json.dumps({
            "from_user_id": "user1",
            "to_user_id": "user2",
            "amount": 10.5,
            "transaction_type": "invalid_type"
        })
        with pytest.raises(ValidationError) as exc_info:
            TransactionProcessor.process_transaction(payload)
        assert "Invalid transaction type" in str(exc_info.value)
        
        # Test invalid amount
        payload = json.dumps({
            "from_user_id": "user1",
            "to_user_id": "user2",
            "amount": -10.5,
            "transaction_type": "transfer"
        })
        with pytest.raises(ValidationError) as exc_info:
            TransactionProcessor.process_transaction(payload)
        assert "Amount must be at least" in str(exc_info.value)
        
        # Test invalid metadata
        payload = json.dumps({
            "from_user_id": "user1",
            "to_user_id": "user2",
            "amount": 10.5,
            "transaction_type": "transfer",
            "metadata": "invalid"
        })
        with pytest.raises(ValidationError) as exc_info:
            TransactionProcessor.process_transaction(payload)
        assert "Metadata must be a dictionary" in str(exc_info.value)
    
    def test_validate_transaction_balance_valid(self):
        """Test validation of valid transaction balances."""
        # Test sufficient balance
        TransactionProcessor.validate_transaction_balance(50.0, 100.0)
        
        # Test exact balance
        TransactionProcessor.validate_transaction_balance(100.0, 100.0)
    
    def test_validate_transaction_balance_invalid(self):
        """Test validation of invalid transaction balances."""
        # Test insufficient balance
        with pytest.raises(ValidationError) as exc_info:
            TransactionProcessor.validate_transaction_balance(150.0, 100.0)
        assert "Insufficient balance" in str(exc_info.value)
        
        # Test negative amount when not allowed
        if not Config.CREDIT_ALLOW_NEGATIVE:
            with pytest.raises(ValidationError) as exc_info:
                TransactionProcessor.validate_transaction_balance(-50.0, 100.0)
            assert "Negative amounts are not allowed" in str(exc_info.value) 