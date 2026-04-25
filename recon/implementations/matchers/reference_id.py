from datetime import timedelta
from typing import List, Optional

from recon.domain.models import Transaction, BankEntry, MatchResult, MatchClassification
from recon.ports import Matcher


class ReferenceIdMatcher(Matcher):
    def __init__(self, time_window_hours: int = 48):
        self.time_window_hours = time_window_hours
    
    @property
    def name(self) -> str:
        return "reference_id_matcher"
    
    def match(
        self,
        transactions: List[Transaction],
        bank_entries: List[BankEntry],
        excluded_bank_ids: set = None
    ) -> List[MatchResult]:
        excluded_bank_ids = excluded_bank_ids or set()
        results = []
        
        bank_by_ref = {}
        for entry in bank_entries:
            if entry.reference_id and entry.id not in excluded_bank_ids:
                key = (entry.reference_id, entry.amount, entry.currency)
                if key not in bank_by_ref:
                    bank_by_ref[key] = []
                bank_by_ref[key].append(entry)
        
        matched_bank_ids = set(excluded_bank_ids)
        
        for txn in transactions:
            if not txn.reference_id:
                continue
            
            key = (txn.reference_id, txn.amount, txn.currency)
            candidates = bank_by_ref.get(key, [])
            
            for entry in candidates:
                if entry.id in matched_bank_ids:
                    continue
                
                time_diff = abs((txn.timestamp - entry.timestamp).total_seconds())
                max_diff = self.time_window_hours * 3600
                
                if time_diff <= max_diff:
                    results.append(MatchResult(
                        transaction_id=txn.id,
                        bank_entry_id=entry.id,
                        score=1.0,
                        classification=MatchClassification.EXACT_MATCH,
                        matcher_used=self.name,
                        reason=f"Exact reference_id match within {self.time_window_hours}h"
                    ))
                    matched_bank_ids.add(entry.id)
                    break
        
        return results
