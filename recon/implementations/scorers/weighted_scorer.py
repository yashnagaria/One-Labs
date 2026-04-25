from datetime import timedelta
from decimal import Decimal
from typing import Optional

from recon.domain.models import Transaction, BankEntry
from recon.ports import Scorer


class WeightedScorer(Scorer):
    def __init__(
        self,
        amount_weight: float = 0.5,
        time_weight: float = 0.3,
        reference_weight: float = 0.2,
        time_window_hours: int = 72
    ):
        self.amount_weight = amount_weight
        self.time_weight = time_weight
        self.reference_weight = reference_weight
        self.time_window_hours = time_window_hours
    
    def calculate_score(
        self,
        transaction: Transaction,
        bank_entry: BankEntry
    ) -> float:
        amount_score = self._calculate_amount_score(transaction.amount, bank_entry.amount)
        time_score = self._calculate_time_score(transaction.timestamp, bank_entry.timestamp)
        reference_score = self._calculate_reference_score(
            transaction.reference_id,
            bank_entry.reference_id
        )
        
        total_score = (
            amount_score * self.amount_weight +
            time_score * self.time_weight +
            reference_score * self.reference_weight
        )
        
        return min(max(total_score, 0.0), 1.0)
    
    def _calculate_amount_score(self, txn_amount: Decimal, bank_amount: Decimal) -> float:
        if txn_amount == bank_amount:
            return 1.0
        
        diff = abs(txn_amount - bank_amount)
        max_amount = max(txn_amount, bank_amount)
        
        if max_amount == 0:
            return 0.0
        
        diff_percent = float(diff) / float(max_amount)
        
        if diff_percent > 0.05:
            return 0.0
        
        return 1.0 - (diff_percent / 0.05) * 0.5
    
    def _calculate_time_score(self, txn_time, bank_time) -> float:
        diff_seconds = abs((txn_time - bank_time).total_seconds())
        max_window = self.time_window_hours * 3600
        
        if diff_seconds >= max_window:
            return 0.0
        
        return 1.0 - (diff_seconds / max_window)
    
    def _calculate_reference_score(
        self,
        txn_ref: Optional[str],
        bank_ref: Optional[str]
    ) -> float:
        if not txn_ref or not bank_ref:
            return 0.0
        
        if txn_ref == bank_ref:
            return 1.0
        
        if txn_ref.lower() == bank_ref.lower():
            return 0.8
        
        return 0.0
