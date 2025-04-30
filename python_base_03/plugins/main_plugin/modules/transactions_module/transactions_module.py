from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

@dataclass
class CreditTransaction:
    from_user_id: str
    to_user_id: str
    amount: float
    transaction_type: str
    metadata: Dict
    timestamp: datetime
    id: Optional[str] = None
    status: str = "PENDING"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "from_user_id": self.from_user_id,
            "to_user_id": self.to_user_id,
            "amount": self.amount,
            "transaction_type": self.transaction_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CreditTransaction':
        return cls(
            id=data.get("id"),
            from_user_id=data["from_user_id"],
            to_user_id=data["to_user_id"],
            amount=data["amount"],
            transaction_type=data["transaction_type"],
            metadata=data["metadata"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            status=data.get("status", "PENDING")
        ) 