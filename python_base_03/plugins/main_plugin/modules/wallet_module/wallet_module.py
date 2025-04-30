from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class CreditWallet:
    user_id: str
    balance: float
    locked_balance: float = 0.0
    metadata: Dict = None
    id: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "balance": self.balance,
            "locked_balance": self.locked_balance,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CreditWallet':
        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            balance=data["balance"],
            locked_balance=data.get("locked_balance", 0.0),
            metadata=data.get("metadata", {})
        )
    
    def has_sufficient_balance(self, amount: float) -> bool:
        return self.balance >= amount
    
    def get_available_balance(self) -> float:
        return self.balance - self.locked_balance 