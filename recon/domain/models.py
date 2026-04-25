from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum, auto
from typing import Optional


class MatchClassification(str, Enum):
    EXACT_MATCH = "exact_match"
    PROBABLE_MATCH = "probable_match"
    LOW_CONFIDENCE = "low_confidence"


class MismatchType(str, Enum):
    MISSING_IN_BANK = "missing_in_bank"
    MISSING_IN_PLATFORM = "missing_in_platform"


@dataclass(frozen=True)
class Transaction:
    id: str
    reference_id: Optional[str]
    amount: Decimal
    currency: str
    timestamp: datetime
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class BankEntry:
    id: str
    reference_id: Optional[str]
    amount: Decimal
    currency: str
    timestamp: datetime
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.amount == 0:
            raise ValueError(f"Amount cannot be zero, got {self.amount}")


@dataclass(frozen=True)
class MatchResult:
    transaction_id: str
    bank_entry_id: str
    score: float
    classification: MatchClassification
    matcher_used: str
    reason: str


@dataclass(frozen=True)
class MismatchResult:
    type: MismatchType
    transaction_id: Optional[str]
    bank_entry_id: Optional[str]
    details: str