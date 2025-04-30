from typing import Dict, Optional
from datetime import datetime
from ....utils.exceptions.validation_exceptions import ValidationError
from ....utils.config.config import Config
from ....utils.validation.sanitizer import Sanitizer
from ....utils.validation.payload_validator import PayloadValidator
from ....utils.validation.credit_validator import CreditValidator
from ....utils.validation.transaction_validator import TransactionValidator
from ....utils.validation.transaction_integrity import TransactionIntegrity
from ....tools.logger.audit_logger import AuditLogger

class TransactionProcessor:
    """Class for processing credit transactions with validation."""
    
    @staticmethod
    def validate_transaction_payload(payload: Dict) -> None:
        """
        Validate a transaction payload.
        
        Args:
            payload: The transaction payload to validate
            
        Raises:
            ValidationError: If the payload is invalid
        """
        # Validate payload size and format
        PayloadValidator.validate_payload(payload)
        
        # Sanitize string fields
        sanitized_payload = Sanitizer.sanitize_json(payload)
        
        # Validate required fields
        required_fields = {'transaction_id', 'user_id', 'type', 'amount'}
        missing_fields = required_fields - set(sanitized_payload.keys())
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    @staticmethod
    def process_transaction(transaction_data: Dict) -> Dict:
        """
        Process a credit transaction with full validation.
        
        Args:
            transaction_data: The transaction data to process
            
        Returns:
            Dict: The processed transaction data
            
        Raises:
            ValidationError: If the transaction is invalid
        """
        try:
            # Log transaction start
            AuditLogger.log_transaction(
                transaction_id=transaction_data['transaction_id'],
                user_id=transaction_data['user_id'],
                action_type=transaction_data['type'],
                credit_delta=transaction_data['amount'],
                source={
                    'service': 'transaction_processor',
                    'ip': transaction_data.get('source_ip', 'unknown'),
                    'client': transaction_data.get('client_id', 'unknown')
                },
                metadata={
                    'validation_start': datetime.utcnow().isoformat()
                }
            )
            
            # Validate transaction integrity
            TransactionIntegrity.validate_transaction_integrity(transaction_data)
            
            # Validate transaction payload
            TransactionProcessor.validate_transaction_payload(transaction_data)
            
            # Validate transaction type
            TransactionValidator.validate_type(transaction_data['type'])
            
            # Validate amount
            CreditValidator.validate_amount(transaction_data['amount'])
            
            # Validate balance if enabled
            if Config.ENFORCE_BALANCE_VALIDATION:
                # Get current balance from database
                current_balance = TransactionProcessor._get_user_balance(transaction_data['from_user_id'])
                
                # Validate transaction amount against balance
                TransactionProcessor.validate_transaction_balance(
                    transaction_data['from_user_id'],
                    current_balance,
                    transaction_data['amount']
                )
            
            # Validate metadata if present
            if 'metadata' in transaction_data:
                TransactionValidator.validate_metadata(transaction_data['metadata'])
            
            # Validate reference ID if present
            if 'reference_id' in transaction_data:
                TransactionValidator.validate_reference_id(transaction_data['reference_id'])
            
            # Add timestamp if not present
            if 'timestamp' not in transaction_data:
                transaction_data['timestamp'] = datetime.utcnow().isoformat()
            
            # Log successful validation
            AuditLogger.log_transaction(
                transaction_id=transaction_data['transaction_id'],
                user_id=transaction_data['user_id'],
                action_type=transaction_data['type'],
                credit_delta=transaction_data['amount'],
                source={
                    'service': 'transaction_processor',
                    'ip': transaction_data.get('source_ip', 'unknown'),
                    'client': transaction_data.get('client_id', 'unknown')
                },
                metadata={
                    'validation_complete': datetime.utcnow().isoformat(),
                    'status': 'validated'
                }
            )
            
            return transaction_data
            
        except ValidationError as e:
            # Log validation failure
            AuditLogger.log_validation_failure(
                transaction_id=transaction_data['transaction_id'],
                user_id=transaction_data['user_id'],
                validation_type=e.validation_type,
                error_message=str(e),
                context={
                    'transaction_data': transaction_data,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            raise
    
    @staticmethod
    def _get_user_balance(user_id: str) -> float:
        """
        Get the current balance for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            float: Current balance of the user
        """
        # TODO: Implement actual database query
        # This is a placeholder that should be replaced with actual database access
        return 0.0
    
    @staticmethod
    def validate_transaction_balance(
        user_id: str,
        current_balance: float,
        transaction_amount: float
    ) -> None:
        """
        Validate that a transaction amount is valid for the current balance.
        
        Args:
            user_id: ID of the user
            current_balance: Current balance of the user
            transaction_amount: Amount of the transaction
            
        Raises:
            ValidationError: If the transaction amount is invalid
        """
        try:
            # Validate current balance
            CreditValidator.validate_balance(current_balance)
            
            # Validate transaction amount against balance
            CreditValidator.validate_transaction_amount(
                transaction_amount,
                current_balance=current_balance,
                check_balance=True
            )
            
            # Calculate new balance
            new_balance = current_balance + transaction_amount
            
            # Log balance change
            AuditLogger.log_balance_change(
                user_id=user_id,
                old_balance=current_balance,
                new_balance=new_balance,
                transaction_id='pending',
                reason=f"Balance validation for transaction amount: {transaction_amount}"
            )
            
        except ValidationError as e:
            # Log validation failure
            AuditLogger.log_validation_failure(
                transaction_id='pending',
                user_id=user_id,
                validation_type='balance_validation',
                error_message=str(e),
                context={
                    'current_balance': current_balance,
                    'transaction_amount': transaction_amount,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            raise 