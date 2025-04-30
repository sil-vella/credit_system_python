import pytest
from ..transaction_validator import TransactionValidator
from .......utils.exceptions.validation_exceptions import ValidationError
from .......utils.config.config import Config

class TestTransactionValidator:
    """Test cases for TransactionValidator class."""
    
    def test_validate_type_valid(self):
        """Test validation of valid transaction types."""
        # Test all valid types
        for ttype in TransactionValidator.VALID_TYPES:
            assert TransactionValidator.validate_type(ttype) == ttype
            
        # Test case insensitivity
        assert TransactionValidator.validate_type("PURCHASE") == "purchase"
        assert TransactionValidator.validate_type("Purchase") == "purchase"
        
        # Test with whitespace
        assert TransactionValidator.validate_type(" purchase ") == "purchase"
    
    def test_validate_type_invalid(self):
        """Test validation of invalid transaction types."""
        # Test invalid type
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidator.validate_type("invalid_type")
        assert "Invalid transaction type" in str(exc_info.value)
        
        # Test non-string input
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidator.validate_type(123)
        assert "Transaction type must be a string" in str(exc_info.value)
    
    def test_validate_metadata_valid(self):
        """Test validation of valid metadata."""
        # Test empty metadata
        assert TransactionValidator.validate_metadata() == {}
        assert TransactionValidator.validate_metadata(None) == {}
        
        # Test valid metadata
        valid_metadata = {
            "description": "Test transaction",
            "source": "test_source"
        }
        assert TransactionValidator.validate_metadata(valid_metadata) == valid_metadata
    
    def test_validate_metadata_invalid(self):
        """Test validation of invalid metadata."""
        # Test non-dict input
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidator.validate_metadata("invalid")
        assert "Metadata must be a dictionary" in str(exc_info.value)
        
        # Test oversized metadata
        large_metadata = {"data": "x" * (Config.MAX_METADATA_SIZE + 1)}
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidator.validate_metadata(large_metadata)
        assert "Metadata too large" in str(exc_info.value)
    
    def test_validate_reference_id_valid(self):
        """Test validation of valid reference IDs."""
        # Test None input
        assert TransactionValidator.validate_reference_id() is None
        assert TransactionValidator.validate_reference_id(None) is None
        
        # Test valid reference ID
        valid_id = "ref_123"
        assert TransactionValidator.validate_reference_id(valid_id) == valid_id
        
        # Test with whitespace
        assert TransactionValidator.validate_reference_id(" ref_123 ") == "ref_123"
    
    def test_validate_reference_id_invalid(self):
        """Test validation of invalid reference IDs."""
        # Test non-string input
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidator.validate_reference_id(123)
        assert "Reference ID must be a string" in str(exc_info.value)
        
        # Test empty string
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidator.validate_reference_id("")
        assert "Reference ID cannot be empty" in str(exc_info.value)
        
        # Test oversized reference ID
        large_id = "x" * (Config.MAX_REFERENCE_ID_LENGTH + 1)
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidator.validate_reference_id(large_id)
        assert "Reference ID too long" in str(exc_info.value) 