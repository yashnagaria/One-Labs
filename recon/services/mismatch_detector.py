from typing import List

from recon.domain.models import (
    Transaction,
    BankEntry,
    MatchResult,
    MismatchResult,
    MismatchType
)


class MismatchDetector:
    def detect_mismatches(
        self,
        transactions: List[Transaction],
        bank_entries: List[BankEntry],
        matches: List[MatchResult]
    ) -> List[MismatchResult]:
        mismatches = []
        
        matched_txn_ids = {m.transaction_id for m in matches}
        matched_bank_ids = {m.bank_entry_id for m in matches}
        
        for txn in transactions:
            if txn.id not in matched_txn_ids:
                mismatches.append(MismatchResult(
                    type=MismatchType.MISSING_IN_BANK,
                    transaction_id=txn.id,
                    bank_entry_id=None,
                    details=f"Transaction {txn.id} (amount: {txn.amount} {txn.currency}) not found in bank entries"
                ))
        
        for entry in bank_entries:
            if entry.id not in matched_bank_ids:
                mismatches.append(MismatchResult(
                    type=MismatchType.MISSING_IN_PLATFORM,
                    transaction_id=None,
                    bank_entry_id=entry.id,
                    details=f"Bank entry {entry.id} (amount: {entry.amount} {entry.currency}) not found in transactions"
                ))
        
        return mismatches
