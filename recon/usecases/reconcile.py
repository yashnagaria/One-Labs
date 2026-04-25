from dataclasses import dataclass
from typing import List

from recon.domain.models import Transaction, BankEntry, MatchResult, MismatchResult
from recon.services.matching_engine import MatchingEngine
from recon.services.mismatch_detector import MismatchDetector
from recon.ports import Repository


@dataclass
class ReconciliationResult:
    matches: List[MatchResult]
    mismatches: List[MismatchResult]
    stats: dict


class ReconcileUseCase:
    def __init__(
        self,
        matching_engine: MatchingEngine = None,
        mismatch_detector: MismatchDetector = None,
        repository: Repository = None
    ):
        self.matching_engine = matching_engine or MatchingEngine()
        self.mismatch_detector = mismatch_detector or MismatchDetector()
        self.repository = repository
    
    def execute(
        self,
        transactions: List[Transaction],
        bank_entries: List[BankEntry]
    ) -> ReconciliationResult:
        matches = self.matching_engine.match(transactions, bank_entries)
        mismatches = self.mismatch_detector.detect_mismatches(
            transactions,
            bank_entries,
            matches
        )
        
        if self.repository:
            self.repository.save_results(matches, mismatches)
        
        stats = self._calculate_stats(matches, transactions, bank_entries)
        
        return ReconciliationResult(
            matches=matches,
            mismatches=mismatches,
            stats=stats
        )
    
    def _calculate_stats(
        self,
        matches: List[MatchResult],
        transactions: List[Transaction],
        bank_entries: List[BankEntry]
    ) -> dict:
        exact_count = sum(1 for m in matches if m.score >= 0.9)
        probable_count = sum(1 for m in matches if 0.6 <= m.score < 0.9)
        low_conf_count = sum(1 for m in matches if m.score < 0.6)
        
        return {
            "total_transactions": len(transactions),
            "total_bank_entries": len(bank_entries),
            "total_matches": len(matches),
            "exact_matches": exact_count,
            "probable_matches": probable_count,
            "low_confidence_matches": low_conf_count,
            "unmatched_transactions": len(transactions) - len({m.transaction_id for m in matches}),
            "unmatched_bank_entries": len(bank_entries) - len({m.bank_entry_id for m in matches}),
            "confidence_distribution": {
                "high": exact_count,
                "medium": probable_count,
                "low": low_conf_count
            }
        }
