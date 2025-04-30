from decimal import Decimal, InvalidOperation
from typing import Union, Optional
from ....utils.config.config import Config
from ....utils.exceptions.validation_exceptions import ValidationError

class CreditValidator:
    """Utility class for validating credit amounts and related values."""
    
    @staticmethod
    def validate_amount(amount: Union[int, float, str, Decimal]) -> Decimal:
        """
        Validate a credit amount against configured limits.
        
        Args:
            amount: The amount to validate
            
        Returns:
            Decimal: The validated amount
            
        Raises:
            ValidationError: If the amount is invalid
        """
        try:
            # Convert to Decimal for precise arithmetic
            amount_decimal = Decimal(str(amount))
            
            # Check if amount is a number
            if not amount_decimal.is_finite():
                raise ValidationError("Amount must be a finite number")
            
            # Check precision
            if abs(amount_decimal.as_tuple().exponent) > Config.CREDIT_PRECISION:
                raise ValidationError(f"Amount can have at most {Config.CREDIT_PRECISION} decimal places")
            
            # Check range
            if amount_decimal < Config.CREDIT_MIN_AMOUNT:
                raise ValidationError(f"Amount must be at least {Config.CREDIT_MIN_AMOUNT}")
            
            if amount_decimal > Config.CREDIT_MAX_AMOUNT:
                raise ValidationError(f"Amount must not exceed {Config.CREDIT_MAX_AMOUNT}")
            
            # Check for negative amounts if not allowed
            if not Config.CREDIT_ALLOW_NEGATIVE and amount_decimal < 0:
                raise ValidationError("Negative amounts are not allowed")
            
            return amount_decimal
            
        except (InvalidOperation, ValueError) as e:
            raise ValidationError(f"Invalid amount format: {str(e)}")
    
    @staticmethod
    def validate_balance(balance: Union[int, float, str, Decimal]) -> Decimal:
        """
        Validate a wallet balance.
        
        Args:
            balance: The balance to validate
            
        Returns:
            Decimal: The validated balance
            
        Raises:
            ValidationError: If the balance is invalid
        """
        try:
            balance_decimal = Decimal(str(balance))
            
            # Check if balance is a number
            if not balance_decimal.is_finite():
                raise ValidationError("Balance must be a finite number")
            
            # Check precision
            if abs(balance_decimal.as_tuple().exponent) > Config.CREDIT_PRECISION:
                raise ValidationError(f"Balance can have at most {Config.CREDIT_PRECISION} decimal places")
            
            # Check for negative balance if not allowed
            if not Config.CREDIT_ALLOW_NEGATIVE and balance_decimal < 0:
                raise ValidationError("Negative balance is not allowed")
            
            return balance_decimal
            
        except (InvalidOperation, ValueError) as e:
            raise ValidationError(f"Invalid balance format: {str(e)}")
    
    @staticmethod
    def validate_transaction_amount(amount: Union[int, float, str, Decimal], 
                                  current_balance: Optional[Union[int, float, str, Decimal]] = None) -> Decimal:
        """
        Validate a transaction amount, optionally checking against current balance.
        
        Args:
            amount: The transaction amount to validate
            current_balance: Optional current balance to check against
            
        Returns:
            Decimal: The validated amount
            
        Raises:
            ValidationError: If the amount is invalid or exceeds balance
        """
        validated_amount = CreditValidator.validate_amount(amount)
        
        if current_balance is not None:
            validated_balance = CreditValidator.validate_balance(current_balance)
            
            # For negative transactions (withdrawals), check if balance is sufficient
            if validated_amount < 0 and validated_balance + validated_amount < 0:
                raise ValidationError("Insufficient balance for transaction")
        
        return validated_amount 