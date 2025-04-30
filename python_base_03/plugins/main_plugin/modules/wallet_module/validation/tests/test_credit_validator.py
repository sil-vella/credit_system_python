from decimal import Decimal
import pytest
from ..credit_validator import CreditValidator
from .......utils.exceptions.validation_exceptions import ValidationError
from .......utils.config.config import Config

class TestCreditValidator:
    """Test cases for CreditValidator class."""
    
    def test_validate_amount_valid(self):
        """Test validation of valid amounts."""
        # Test with different valid inputs
        assert CreditValidator.validate_amount(10) == Decimal('10')
        assert CreditValidator.validate_amount(10.5) == Decimal('10.5')
        assert CreditValidator.validate_amount('10.5') == Decimal('10.5')
        assert CreditValidator.validate_amount(Decimal('10.5')) == Decimal('10.5')
        
        # Test with minimum and maximum allowed amounts
        assert CreditValidator.validate_amount(Config.CREDIT_MIN_AMOUNT) == Decimal(str(Config.CREDIT_MIN_AMOUNT))
        assert CreditValidator.validate_amount(Config.CREDIT_MAX_AMOUNT) == Decimal(str(Config.CREDIT_MAX_AMOUNT))
    
    def test_validate_amount_invalid(self):
        """Test validation of invalid amounts."""
        # Test with invalid formats
        with pytest.raises(ValidationError):
            CreditValidator.validate_amount('invalid')
        
        with pytest.raises(ValidationError):
            CreditValidator.validate_amount('')
        
        # Test with too many decimal places
        with pytest.raises(ValidationError):
            CreditValidator.validate_amount('10.123')
        
        # Test with amounts below minimum
        with pytest.raises(ValidationError):
            CreditValidator.validate_amount(Config.CREDIT_MIN_AMOUNT - 0.01)
        
        # Test with amounts above maximum
        with pytest.raises(ValidationError):
            CreditValidator.validate_amount(Config.CREDIT_MAX_AMOUNT + 0.01)
        
        # Test with negative amounts when not allowed
        if not Config.CREDIT_ALLOW_NEGATIVE:
            with pytest.raises(ValidationError):
                CreditValidator.validate_amount(-10)
    
    def test_validate_balance_valid(self):
        """Test validation of valid balances."""
        # Test with different valid inputs
        assert CreditValidator.validate_balance(100) == Decimal('100')
        assert CreditValidator.validate_balance(100.5) == Decimal('100.5')
        assert CreditValidator.validate_balance('100.5') == Decimal('100.5')
        assert CreditValidator.validate_balance(Decimal('100.5')) == Decimal('100.5')
    
    def test_validate_balance_invalid(self):
        """Test validation of invalid balances."""
        # Test with invalid formats
        with pytest.raises(ValidationError):
            CreditValidator.validate_balance('invalid')
        
        with pytest.raises(ValidationError):
            CreditValidator.validate_balance('')
        
        # Test with too many decimal places
        with pytest.raises(ValidationError):
            CreditValidator.validate_balance('100.123')
        
        # Test with negative balance when not allowed
        if not Config.CREDIT_ALLOW_NEGATIVE:
            with pytest.raises(ValidationError):
                CreditValidator.validate_balance(-100)
    
    def test_validate_transaction_amount_valid(self):
        """Test validation of valid transaction amounts."""
        # Test with different valid inputs
        assert CreditValidator.validate_transaction_amount(10) == Decimal('10')
        assert CreditValidator.validate_transaction_amount(10.5) == Decimal('10.5')
        
        # Test with balance check
        assert CreditValidator.validate_transaction_amount(50, 100) == Decimal('50')
        assert CreditValidator.validate_transaction_amount(-50, 100) == Decimal('-50')
    
    def test_validate_transaction_amount_invalid(self):
        """Test validation of invalid transaction amounts."""
        # Test with insufficient balance
        with pytest.raises(ValidationError):
            CreditValidator.validate_transaction_amount(-150, 100)
        
        # Test with invalid amount
        with pytest.raises(ValidationError):
            CreditValidator.validate_transaction_amount('invalid', 100)
        
        # Test with invalid balance
        with pytest.raises(ValidationError):
            CreditValidator.validate_transaction_amount(50, 'invalid') 