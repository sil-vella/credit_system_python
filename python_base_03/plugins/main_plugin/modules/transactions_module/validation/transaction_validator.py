from typing import List, Optional
from ....utils.exceptions.validation_exceptions import ValidationError
from ....utils.config.config import Config

class TransactionValidator:
    """Utility class for validating transaction types and related data."""
    
    # Define valid transaction types
    VALID_TYPES = {
        'purchase': 'Credit purchase transaction',
        'reward': 'Credit reward transaction',
        'burn': 'Credit burn transaction',
        'transfer': 'Credit transfer between users',
        'refund': 'Credit refund transaction'
    }
    
    @staticmethod
    def validate_type(transaction_type: str) -> str:
        """
        Validate a transaction type against the allowlist.
        
        Args:
            transaction_type: The type to validate
            
        Returns:
            str: The validated transaction type (lowercase)
            
        Raises:
            ValidationError: If the type is invalid
        """
        if not isinstance(transaction_type, str):
            raise ValidationError("Transaction type must be a string")
            
        transaction_type = transaction_type.lower().strip()
        
        if transaction_type not in TransactionValidator.VALID_TYPES:
            valid_types = ", ".join(TransactionValidator.VALID_TYPES.keys())
            raise ValidationError(f"Invalid transaction type. Must be one of: {valid_types}")
            
        return transaction_type
    
    @staticmethod
    def validate_metadata(metadata: Optional[dict] = None) -> dict:
        """
        Validate transaction metadata.
        
        Args:
            metadata: Optional metadata dictionary
            
        Returns:
            dict: Validated metadata
            
        Raises:
            ValidationError: If metadata is invalid
        """
        if metadata is None:
            return {}
            
        if not isinstance(metadata, dict):
            raise ValidationError("Metadata must be a dictionary")
            
        # Validate metadata size
        if len(str(metadata)) > Config.MAX_METADATA_SIZE:
            raise ValidationError(f"Metadata too large (max {Config.MAX_METADATA_SIZE} bytes)")
            
        return metadata
    
    @staticmethod
    def validate_reference_id(reference_id: Optional[str] = None) -> Optional[str]:
        """
        Validate a transaction reference ID.
        
        Args:
            reference_id: Optional reference ID
            
        Returns:
            Optional[str]: Validated reference ID
            
        Raises:
            ValidationError: If reference ID is invalid
        """
        if reference_id is None:
            return None
            
        if not isinstance(reference_id, str):
            raise ValidationError("Reference ID must be a string")
            
        reference_id = reference_id.strip()
        
        if not reference_id:
            raise ValidationError("Reference ID cannot be empty")
            
        if len(reference_id) > Config.MAX_REFERENCE_ID_LENGTH:
            raise ValidationError(f"Reference ID too long (max {Config.MAX_REFERENCE_ID_LENGTH} characters)")
            
        return reference_id 