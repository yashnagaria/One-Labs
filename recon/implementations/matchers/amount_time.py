from datetime import timedelta
from decimal import Decimal
from typing import List

from recon.domain.models import Transaction, BankEntry, MatchResult, MatchClassification
from recon.ports import Matcher


class AmountTimeMatcher(Matcher):
    def __init__(
        self,
        time_window_hours: int = 72,
        amount_tolerance_percent: float = 0.01
    ):
        self.time_window_hours = time_window_hours
        self.amount_tolerance_percent = amount_tolerance_percent
    
    @property
    def name(self) -> str:
        return "amount_time_matcher"
    
    def match(
        self,
        transactions: List[Transaction],
        bank_entries: List[BankEntry],
        excluded_bank_ids: set = None
    ) -> List[MatchResult]:
        excluded_bank_ids = excluded_bank_ids or set()
        results = []
        matched_bank_ids = set(excluded_bank_ids)
        
        for txn in transactions:
            best_match = None
            best_score = 0.0
            
            for entry in bank_entries:
                if entry.id in matched_bank_ids:
                    continue
                
                if txn.currency != entry.currency:
                    continue
                
                amount_match = self._calculate_amount_score(txn.amount, entry.amount)
                time_match = self._calculate_time_score(txn.timestamp, entry.timestamp)
                
                score = (amount_match * 0.7) + (time_match * 0.3)
                
                if score > best_score and score >= 0.6:
                    best_score = score
                    best_match = entry
            
            if best_match:
                classification = (
                    MatchClassification.PROBABLE_MATCH
                    if best_score >= 0.8
                    else MatchClassification.LOW_CONFIDENCE
                )
                results.append(MatchResult(
                    transaction_id=txn.id,
                    bank_entry_id=best_match.id,
                    score=best_score,
                    classification=classification,
                    matcher_used=self.name,
                    reason=f"Amount/time proximity match (score: {best_score:.2f})"
                ))
                matched_bank_ids.add(best_match.id)
        
        return results
    
    def _calculate_amount_score(self, txn_amount: Decimal, bank_amount: Decimal) -> float:
        if txn_amount == bank_amount:
            return 1.0
        
        diff = abs(txn_amount - bank_amount)
        tolerance = txn_amount * Decimal(str(self.amount_tolerance_percent))
        
        if diff <= tolerance:
            return 0.9
        
        max_acceptable = txn_amount * Decimal('0.05')
        if diff > max_acceptable:
            return 0.0
        
        return float(1.0 - (diff / max_acceptable) * 0.5)
    
    def _calculate_time_score(self, txn_time, bank_time) -> float:
        diff_seconds = abs((txn_time - bank_time).total_seconds())
        max_window = self.time_window_hours * 3600
        
        if diff_seconds >= max_window:
            return 0.0
        
        return 1.0 - (diff_seconds / max_window)
